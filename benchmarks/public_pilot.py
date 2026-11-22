"""Run the public financial research pilot with the local Codex subscription."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
from time import perf_counter

from pydantic import Field

from benchmarks.public_cases import input_checksums, load_cases
from research_app.adapters import AdapterError, Codex
from research_app.discovery import source_key
from research_app.research import document_evidence
from research_app.schema import Event, Question, Schema
from research_app.store import Store

MODEL = "gpt-6.2-astra"
SNAPSHOT = "2026-11-22"
EFFORT = "medium"
ACTION_BUDGET = {"search": 7, "open": 7}
BASE_INSTRUCTION = (
    "Answer the financial research request in Traditional Chinese. Preserve every requested component, "
    "units, accounting periods, denominators, and relevant limitations. For each important claim, "
    "cite its source in the answer. Label projections as such and state what is unverified. "
    "Do not retrieve benchmarks, answer keys, or rubrics. Use only the input evidence and allowed domains."
)


class Citation(Schema):
    ref: str
    published_on: str | None
    supports: str


class Response(Schema):
    answer: str
    citations: list[Citation] = Field(max_length=15)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def web_items(events):
    return [event["item"] for event in events if event.get("type") == "item.completed"
            and event.get("item", {}).get("type") == "web_search"]


def web_audit(events, domains):
    records = web_items(events)
    actions = dict.fromkeys(ACTION_BUDGET, 0)
    urls = set()
    for item in records:
        action = item.get("action", {})
        kind = action.get("type")
        if kind in ("search", "open", "open_page"):
            category = "search" if kind == "search" else "open"
            actions[category] += len(action.get("queries") or action.get("urls") or [None])
        urls.update(hit["url"] for hit in item.get("results", []) if hit.get("url"))
        if action.get("url"):
            urls.add(action["url"])
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    return {
        "actions": actions,
        "web_items": len(records),
        "budget_exceeded": any(actions[key] > ACTION_BUDGET[key] for key in actions),
        "observed_allowed_urls": sorted(
            url for url in urls if (key := source_key(url)) and
            any(key[0] == domain or key[0].endswith("." + domain) for domain in domains)
        ),
        "usage": {key: sum(turn.get(key, 0) for turn in usage) for key in (
            "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
        )},
    }


def run_direct(case, adapter):
    data = {
        "question": case["question"], "target": case["target"], "as_of": case["cutoff"],
        "allowed_domains": case["domains"],
        "evidence": [row for doc in case["docs"] for row in document_evidence(doc)],
    }
    search = bool(case["domains"])
    instruction = BASE_INSTRUCTION
    if search:
        instruction += (
            " Use native web search with at most seven query strings and seven page opens total. "
            "Scope queries to the allowed domains. Cite exact HTTPS URLs and explicitly documented "
            "publication dates. If an as_of date is supplied, restrict retrieval to documents available "
            "by that date and do not use facts learned later. For dates not explicitly supported return null."
        )
    else:
        instruction += " Cite the supplied evidence IDs and only use the provided filing excerpts."
    result, _ = adapter._call(Response, instruction, data, search=search)
    return {"answer": result.answer, "citations": [row.model_dump() for row in result.citations]}


def run_harness(case, adapter, path):
    supply = case["suite"] == "Supply chain"
    event = Event(
        event_text=case["question"], research_target=case["target"],
        research_horizon="12 months" if supply else None,
        as_of=f"{case['cutoff'] or SNAPSHOT}T23:59:59Z",
        search_mode="historical_replay" if case["domains"] else "off",
        search_domains=list(case["domains"]), documents=case["docs"],
    )
    store = Store(path)
    report_id = store.create(event, adapter)["report_id"]
    report = store.revision(report_id, 1)
    if supply:
        refs = [row["id"] for row in report["evidence"]
                if f"[`{row['id']}`](#" in report["markdown"]]
        answer = report["markdown"]
    else:
        qa = store.question(report_id, Question(
            parent_revision=1, question=case["question"], evidence_search="off",
        ), adapter)
        refs, answer = qa["evidence_ids"], qa["answer"]
    citations = [
        {"ref": row["source"] if case["domains"] else row["id"],
         "published_on": row["published_at"][:10] if case["domains"] else None,
         "supports": row["quote"]}
        for row in report["evidence"] if row["id"] in refs
    ]
    return {"answer": answer, "citations": citations, "report": report}


def run_arm(case, arm, output, effort, call_timeout):
    destination = output / case["id"] / arm
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "result.json"
    if path.exists():
        if "answer" in json.loads(path.read_text(encoding="utf-8")):
            return case["id"], arm, "reused"
        attempt = 1
        while (destination / f"attempt-{attempt}").exists():
            attempt += 1
        archive = destination / f"attempt-{attempt}"
        archive.mkdir()
        for artifact in ("result.json", "events.jsonl", "run.sqlite3"):
            if (destination / artifact).exists():
                (destination / artifact).replace(archive / artifact)
    events = []
    log = destination / "events.jsonl"

    def audit(rows):
        events.extend(rows)
        with log.open("a", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    log.write_text("", encoding="utf-8")
    adapter = Codex(audit=audit, reasoning_effort=effort, call_timeout=call_timeout)
    started = perf_counter()
    try:
        if arm == "direct":
            result = run_direct(case, adapter)
        else:
            result = run_harness(case, adapter, destination / "run.sqlite3")
        (destination / "answer.md").write_text(result["answer"] + "\n", encoding="utf-8")
        status = "ok"
    except (AdapterError, ValueError) as exc:
        result = {"error": str(exc)}
        status = "failed"
    write_json(path, {
        **result, "elapsed_seconds": round(perf_counter() - started, 2),
        "call_timeout_override": call_timeout,
        "audit": web_audit(events, case["domains"]),
    })
    return case["id"], arm, status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/public-benchmark"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--call-timeout", type=int, help="Override per-call timeout for technical retries.")
    parser.add_argument("--case", action="append", help="Run specific IDs; repeat or omit for all.")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    inputs = args.output / "inputs"
    cases = load_cases(inputs)
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    manifest = {
        "model": MODEL, "reasoning_effort": EFFORT, "search_budget": ACTION_BUDGET,
        "input_sha256": input_checksums(inputs),
        "cases": [{key: value for key, value in case.items() if key not in ("docs", "reference")}
                  for case in cases],
    }
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists():
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        if saved != json.loads(json.dumps(manifest)):
            parser.error("The benchmark inputs or configuration changed. Use a new --output directory.")
    else:
        write_json(manifest_path, manifest)
    if args.prepare_only:
        print(f"Prepared {len(cases)} cases", flush=True)
        return
    selected = set(args.case or [case["id"] for case in cases])
    if unknown := selected - {case["id"] for case in cases}:
        parser.error(f"Unknown cases: {sorted(unknown)}")
    # Run cases from every suite early. Alternate ordering so one arm does not consistently run first.
    cases = sorted(cases, key=lambda case: (case["id"][-2:], case["id"][:2]))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(run_arm, case, arm, args.output, EFFORT, args.call_timeout)
            for index, case in enumerate(cases) if case["id"] in selected
            for arm in (("direct", "harness") if index % 2 == 0 else ("harness", "direct"))
        ]
        for task in as_completed(futures):
            print(*task.result(), flush=True)


if __name__ == "__main__":
    main()
