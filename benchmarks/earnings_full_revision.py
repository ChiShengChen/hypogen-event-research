"""Replay the same complete issuer disclosures through three equal-budget workflows."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
from time import perf_counter
from urllib.parse import urlsplit
import unicodedata
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import ValidationError

from research_app import full_revision, revision_bridge
from research_app.adapters import AdapterError, Codex
from research_app.schema import MetricKey

from . import earnings_raw_revision as raw
from . import earnings_revision as prior
from .earnings_horizon import freeze_json
from .public_pilot import EFFORT, MODEL, write_json


OUT = Path("output/earnings-full-revision")
ROOT = Path(__file__).resolve().parents[1]
ARMS = {"current": "現版 Harness", "candidate": "新版 Harness", "astra": "純 Astra"}
SPLITS = ("pilot", "holdout")
TIMEOUT = 240
EXCLUDED = {"HOLX"}

POLICY = (
    "Use the supplied complete archived issuer document blocks and frozen incumbent. "
    "Find explicit updated issuer-issued consolidated quarterly revenue guidance or a "
    "preliminary point estimate for the exact target fiscal quarter, currency and basis. "
    "Company-level unqualified revenue or net sales of the US issuers in this replay is "
    "US GAAP in USD absent conflicting labels. Use the supplied fiscal label and cutoff. "
    "Discard guidance for a different quarter, full year, segment or metric, reported actuals, "
    "earlier table columns, statements from after the cutoff and single-sided or unbounded estimates. "
    "A cited interval may pair context and table headings within the same issuer document. "
    "Identify exact provided block IDs for amount, period or the reason a qualifying range is missing. "
    "For a point both ends are equal. Compute tolerances in full currency units without separators."
)
DIRECT = (
    "Return status, bounds new_low/new_high, remaining_delta, evidence_ids, and brief Chinese reason. "
    "Use status eligible and a signed adjustment if the incumbent is outside the interval. "
    "Use the nearest interval edge less the incumbent. Use noop and 0 if inside or on an edge. "
    "Use blocked with null bounds and adjustment when the disclosure is incompatible or absent. "
    "Cite the supplied amount and context blocks and include the header block if separate."
)
CURRENT = (
    "Extract a proposed quote and provide the required legacy native_proof and exact block IDs. "
    "amount_ref is the block with the new bounds; context_ref is the same issuer document's "
    "fiscal period context. For a legacy table proof use an amount block that already includes "
    "the column header, set header_ref to the same ID as amount_ref, and set column to its "
    "zero-based value position excluding the metric name. Use both null for prose. Use a matching "
    "prose quote if available. In quote include the exact metric key, the cited document's "
    "obtained_at, low and high, and every cited proof ID. Use a null quote if no matching "
    "guidance was found. The outer evidence_ids explain the selected or blocked result."
)
PROMPTS = {"astra": DIRECT, "current": CURRENT, "candidate": full_revision.FILING_SELECTION_PROMPT}
SCHEMAS = {"astra": raw.Decision, "current": raw.Extraction, "candidate": full_revision.FilingExtraction}


def manifest_path(split, *, gold=False):
    suffix = "_gold" if gold else ""
    return Path(__file__).with_name(f"earnings_full_{split}{suffix}.json")


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(value.translate(str.maketrans({"’": "'", "‘": "'", "–": "-", "—": "-", "|": " "})).split())


def validate_timestamp(value):
    when = prior.instant(value)
    if when.utcoffset() is None:
        raise ValueError(f"資料須有時區 {value}")
    return when


def source_url(value):
    url = urlsplit(value)
    if url.scheme != "https" or not url.netloc or url.username or url.password:
        raise ValueError(f"公告來源須為 HTTPS {value}")
    return value


def archive(case):
    cutoff, event = map(validate_timestamp, (case["as_of"], case["event_at"]))
    if not validate_timestamp(case["baseline"]["available_at"]) <= event <= cutoff:
        raise ValueError(f"現估或截止時間不符 {case['id']}")
    if Decimal(case["baseline"]["amount"]) < 0:
        raise ValueError(f"現估不可為負值 {case['id']}")
    source_url(case["baseline"]["source_url"])
    MetricKey.model_validate(prior.target(case))
    if not case["documents"]:
        raise ValueError(f"缺完整發行人公告 {case['id']}")
    documents = []
    for document in case["documents"]:
        published, obtained = map(validate_timestamp, (document["published_at"], document["obtained_at"]))
        if not published <= obtained <= cutoff:
            raise ValueError(f"公告可見時間不符 {document['id']}")
        source_url(document["source_url"])
        path = ROOT / document["path"]
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"公告封存路徑不符 {document['id']}")
        body = path.read_bytes()
        if sha256(body).hexdigest() != document["sha256"]:
            raise ValueError(f"公告封存雜湊不符 {document['id']}")
        html = body.decode("utf-8-sig")
        if document.get("media_type", document.get("content_type")) == "text/plain":
            paragraphs = re.split(r"\r?\n[ \t]*\r?\n", html.strip())
            html = "<html><body>" + "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs) + "</body></html>"
        blocks = full_revision.parse_filing(html, document_id=document["id"])
        if not blocks:
            raise ValueError(f"公告正文缺失 {document['id']}")
        metadata = {key: document[key] for key in ("id", "source_url", "published_at", "obtained_at")}
        documents.append({**metadata, "blocks": blocks})
    ids = [document["id"] for document in documents] + [
        block["id"] for document in documents for block in document["blocks"]
    ]
    if len(ids) != len(set(ids)):
        raise ValueError(f"公告或段落 ID 重複 {case['id']}")
    return {
        "issuer": case["issuer"],
        "ticker": case["ticker"],
        "as_of": case["as_of"],
        "event_at": case["event_at"],
        "target": prior.target(case),
        "fiscal_label": case["fiscal_label"],
        "incumbent": {key: case["baseline"][key] for key in ("amount", "available_at", "source_url")},
        "documents": documents,
    }


def validate_gold(case, expected, data):
    status = expected["disposition"]
    delta = Decimal(expected["delta"])
    low, high = (expected[key] for key in ("new_low", "new_high"))
    incumbent = Decimal(case["baseline"]["amount"])
    if status == "blocked":
        if low is not None or high is not None or delta:
            raise ValueError(f"暫緩裁定不可含金額 {case['id']}")
    else:
        if status not in {"eligible", "noop"} or low is None or high is None:
            raise ValueError(f"區間裁定不完整 {case['id']}")
        low, high = Decimal(low), Decimal(high)
        if not 0 <= low <= high or delta != min(max(incumbent, low), high) - incumbent:
            raise ValueError(f"區間及金額不符 {case['id']}")
        if (status == "eligible") != bool(delta):
            raise ValueError(f"處置與差額不符 {case['id']}")
    sources = set(expected["source_ids"])
    documents = [document for document in data["documents"] if document["id"] in sources]
    if not sources or len(documents) != len(sources):
        raise ValueError(f"裁定來源缺失 {case['id']}")
    texts = [normalize(block["text"]) for document in documents for block in document["blocks"]]
    for item in expected["required_text"]:
        if not normalize(item) or not any(normalize(item) in block for block in texts):
            raise ValueError(f"裁定引文在公告中無法定位 {case['id']}: {item!r}")
    if not expected["required_text"]:
        raise ValueError(f"裁定缺原文定位 {case['id']}")


def load_inputs():
    cases, gold, inputs = [], {}, {}
    issuers = set()
    for split in SPLITS:
        rows = prior.load(manifest_path(split))
        targets = prior.load(manifest_path(split, gold=True))
        if (split == "pilot" and len(rows) != 5) or len(rows) < 4:
            raise ValueError(f"{split} 案例數不符")
        tickers = {row["ticker"].upper() for row in rows}
        if len(rows) != len(tickers) or tickers & (issuers | EXCLUDED):
            raise ValueError("案例發行人重複或包含已指定回歸案例")
        if set(targets) != {row["id"] for row in rows} or set(targets) & gold.keys():
            raise ValueError(f"{split} 案例 ID 與裁定檔不符")
        for row in rows:
            if row["split"] != split or not re.fullmatch(r"[a-zA-Z0-9_-]+", row["id"]):
                raise ValueError(f"案例 ID 或分組不符 {row['id']}")
            data = archive(row)
            validate_gold(row, targets[row["id"]], data)
            inputs[row["id"]] = data
        issuers.update(tickers)
        cases.extend(rows)
        gold.update(targets)
    return cases, gold, inputs


def seal(out, cases, inputs):
    out.mkdir(parents=True, exist_ok=True)
    protocol = {
        "hypothesis": "From the same complete releases, deterministic table lineage and range verification "
                      "should increase fully correct usable decisions over the legacy excerpt checker, "
                      "while generating no unsupported monetary adjustment.",
        "scope": "Point-in-time guidance and preliminary issuer figures, no actual/reported results scoring.",
        "model": MODEL,
        "effort": EFFORT,
        "calls_per_case_per_arm": 1,
        "timeout_seconds": TIMEOUT,
        "tool_search_budget": 0,
        "token_limit": "Same model and context limits. No separate Codex CLI token cap; actual usage recorded.",
        "primary": "Exact disposition, endpoints, signed adjustment and approved issuer block anchors.",
        "citation_rule": "All refs must be visible block IDs. Their source documents must cover the required "
                         "issuer sources and the cited block occurrences must cover all frozen anchor text.",
        "unsupported_adjustment": "Any nonzero adjustment when any primary condition is false.",
        "pilot_gate": "At least 80% exact, one exact eligible, exact count higher than current, "
                      "zero unsupported adjustments and all 3 arms returned.",
        "holdout_gate": "At least 75% exact, one exact eligible, exact count higher than current, "
                        "zero unsupported adjustments and all 3 arms returned.",
        "lead_gate": "Pass holdout gate and strictly more exact decisions than both current and Pure Astra.",
        "stop": "Evaluate sealed pilot once. If pilot fails, preserve output and end. Otherwise evaluate sealed "
                "issuer-disjoint holdout once and end. Failed model responses consume the assigned budget.",
        "known_regression_excluded": ["HOLX"],
        "manifest_sha256": {split: prior.digest(manifest_path(split)) for split in SPLITS},
        "gold_sha256": {split: prior.digest(manifest_path(split, gold=True)) for split in SPLITS},
        "code_sha256": {Path(path).name: prior.digest(Path(path)) for path in (
            __file__, full_revision.__file__, revision_bridge.__file__,
        )},
        "archive_sha256": {document["id"]: document["sha256"] for case in cases
                           for document in case["documents"]},
        "cases": {split: [case["id"] for case in cases if case["split"] == split] for split in SPLITS},
        "inputs": "inputs.json; one complete, identically serialized case payload delivered to each arm.",
        "common_prompt": POLICY,
        "arm_prompts": PROMPTS,
    }
    freeze_json(out / "inputs.json", inputs)
    protocol["model_input_sha256"] = prior.digest(out / "inputs.json")
    freeze_json(out / "protocol.json", protocol)
    lines = [
        "# 完整公告營收指引覆核預註冊", "",
        "假說是從完整公告定位表頭、財季與新數值後，以程式核對區間和差額，"
        "會比現版摘錄核對有更多可用且全對的決策，並維持零誤調。", "",
        f"三組共用同一份完整公告正文、封存現估及截止時間，每案各一次 {MODEL} "
        f"{EFFORT} 呼叫，工具與搜尋關閉，每次上限 {TIMEOUT} 秒。"
        "現版提報數字和舊版引文構造，新版只選公告位置，純 Astra 直接作答。"
        "CLI 共用模型上下文限制，實際詞元與耗時另列。", "",
        "一案全對需處置、兩端、帶符號差額及必要原文引文均正確。"
        "未全對的非零差額視為誤調。Hologic 留給已知回歸驗證。", "",
        f"- 先導固定 {len(protocol['cases']['pilot'])} 案，至少 80% 全對才續跑。",
        f"- 保留集固定 {len(protocol['cases']['holdout'])} 案，發行人與先導不重疊，至少 75% 全對。",
        "- 兩階段都須有至少一筆正確的非零差額、零誤調、三組回覆齊全，以及全對數高於現版。",
        "- 保留集須另外高於純 Astra 的全對數才記為領先。模型失敗也耗用一次額度。"
        "先導未過即停，保留集跑一次即停。", "",
        "[細則與 SHA-256](protocol.json) · [封存模型輸入](inputs.json)",
    ]
    (out / "protocol.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def invoke(case, data, arm, out):
    path = out / "calls" / f"{case['id']}-{arm}.json"
    if path.exists():
        return prior.load(path)
    events = []
    started = perf_counter()
    try:
        response = Codex(audit=events.extend, reasoning_effort=EFFORT, call_timeout=TIMEOUT)._generate(
            SCHEMAS[arm], f"{POLICY} {PROMPTS[arm]}", data,
        )
        record = {"output": response.model_dump(mode="json")}
    except AdapterError as exc:
        record = {"error": str(exc)}
    items = [event["item"] for event in events if event.get("type") == "item.completed"]
    tool_types = [item["type"] for item in items if item.get("type") in {
        "web_search", "command_execution", "mcp_tool_call", "dynamic_tool_call", "collab_tool_call",
    }]
    if tool_types:
        record = {"error": "模型使用預算外的工具。", "tool_types": tool_types,
                  "rejected_output": record.get("output")}
    usage = [event["usage"] for event in events if event.get("type") == "turn.completed"]
    record["elapsed_seconds"] = round(perf_counter() - started, 2)
    record["events"] = events
    record["usage"] = {key: sum(turn.get(key, 0) for turn in usage) for key in (
        "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    )}
    write_json(path, record)
    return record


def source_map(data):
    return {block["id"]: {**block, "document_id": document["id"], "source_url": document["source_url"]}
            for document in data["documents"] for block in document["blocks"]}


def blocked(evidence_ids, reason):
    return {"status": "blocked", "new_low": None, "new_high": None, "remaining_delta": None,
            "evidence_ids": evidence_ids, "reason": reason}


def legacy(data, output):
    if output["quote"] is None:
        return blocked(output["evidence_ids"], "未找到可用的舊版原文定位。")
    key = MetricKey.model_validate(data["target"])
    baseline = data["incumbent"]
    incumbent = revision_bridge.RevisionQuote(
        key=key, available_at=baseline["available_at"], low=baseline["amount"], high=baseline["amount"],
        evidence_ids=["frozen_incumbent"],
    )
    try:
        disclosure = revision_bridge.RevisionQuote.model_validate(output["quote"])
    except ValidationError:
        return blocked(output["evidence_ids"], "舊版原文定位資料格式不符。")
    request = revision_bridge.RevisionRequest(
        key=key, event_at=data["event_at"], incumbent=incumbent, disclosure=disclosure,
    )
    evidence = [
        {"id": block["id"], "source": document["source_url"], "document_id": document["id"],
         "quote": block["text"], "kind": "disclosure", "text_format": "excerpt", "synthetic": False,
         "published_at": document["published_at"], "obtained_at": document["obtained_at"]}
        for document in data["documents"] for block in document["blocks"]
    ]
    evidence.append({
        "id": "frozen_incumbent", "source": baseline["source_url"], "document_id": "frozen_incumbent",
        "quote": "Frozen issuer evidence for the incumbent.", "kind": "disclosure", "text_format": "excerpt",
        "synthetic": False, "published_at": baseline["available_at"], "obtained_at": baseline["available_at"],
    })
    result = revision_bridge.evaluate_revision(request, evidence, as_of=prior.instant(data["as_of"]),
                                               fiscal_label=data["fiscal_label"])
    if result["status"] == "blocked":
        return {**blocked(output["evidence_ids"], result["reason"]), "audit": result}
    return {"status": result["status"], "remaining_delta": result["remaining_delta"],
            "new_low": result["disclosure"]["low"], "new_high": result["disclosure"]["high"],
            "evidence_ids": [ref for ref in result["evidence_ids"] if ref != "frozen_incumbent"],
            "reason": result["reason"], "audit": result}


def candidate(data, output):
    if output["selection"] is None:
        return blocked(output["evidence_ids"], "原文中未找到符合條件的數值與財季。")
    result = full_revision.check_filing_revision(
        key=MetricKey.model_validate(data["target"]), incumbent=Decimal(data["incumbent"]["amount"]),
        event_at=prior.instant(data["event_at"]), as_of=prior.instant(data["as_of"]),
        documents=data["documents"], selection=output["selection"], fiscal_label=data["fiscal_label"],
    )
    evidence_ids = result.get("evidence_ids") or output["evidence_ids"]
    if result["status"] == "blocked":
        return {**blocked(evidence_ids, result["reason"]), "audit": result}
    return {**result, "evidence_ids": evidence_ids}


def assess(decision, expected, refs):
    measures = ("exact", "delta_exact", "range_exact", "citations", "unsafe", "eligible_exact", "missing")
    if decision is None:
        return {**dict.fromkeys(measures, False), "missing": True}
    delta = decision["remaining_delta"]
    effective = Decimal(delta) if delta is not None else Decimal(0)
    delta_ok = effective == Decimal(expected["delta"])
    bounds_ok = raw.pair_amounts(decision["new_low"], decision["new_high"]) == raw.pair_amounts(
        expected["new_low"], expected["new_high"],
    )
    disposition_ok = decision["status"] == expected["disposition"] and (
        (delta is None) == (decision["status"] == "blocked")
    )
    citations = set(decision["evidence_ids"])
    supplied = [refs[value] for value in sorted(citations & refs.keys())]
    cited_text = [normalize(block["text"]) for block in supplied if block["document_id"] in expected["source_ids"]]
    sources = {block["document_id"] for block in supplied}
    citations_ok = (bool(citations) and citations <= refs.keys() and set(expected["source_ids"]) <= sources
                    and all(any(normalize(text) in block for block in cited_text)
                            for text in expected["required_text"]))
    exact = disposition_ok and delta_ok and bounds_ok and citations_ok
    return {"exact": exact, "delta_exact": delta_ok, "range_exact": bounds_ok, "citations": citations_ok,
            "unsafe": bool(effective) and not exact, "eligible_exact": exact and decision["status"] == "eligible",
            "missing": False}


def score(case, data, expected, calls):
    decisions = {arm: calls[arm].get("output") for arm in ARMS}
    for arm, evaluator in (("current", legacy), ("candidate", candidate)):
        if decisions[arm] is not None:
            decisions[arm] = evaluator(data, decisions[arm])
    refs = source_map(data)
    cited = {ref for decision in decisions.values() if decision for ref in decision["evidence_ids"]}
    return {key: case[key] for key in ("id", "split", "ticker", "issuer")} | {
        "target": data["target"], "event_at": data["event_at"], "as_of": data["as_of"],
        "baseline": case["baseline"], "expected": expected, "decisions": decisions,
        "citations": {ref: refs[ref] for ref in sorted(cited & refs.keys())},
        "scores": {arm: assess(decision, expected, refs) for arm, decision in decisions.items()},
        "calls": {arm: {key: value for key, value in record.items() if key != "events"}
                  for arm, record in calls.items()},
    }


def run_split(cases, inputs, gold, out, workers):
    rows = {}
    for directory in ("calls", "cases"):
        (out / directory).mkdir(exist_ok=True)
    calls = {case["id"]: {} for case in cases}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(invoke, case, inputs[case["id"]], arm, out): (case, arm)
                   for case in cases for arm in ARMS}
        for future in as_completed(futures):
            case, arm = futures[future]
            case_id = case["id"]
            calls[case_id][arm] = future.result()
            if len(calls[case_id]) == len(ARMS):
                row = score(case, inputs[case_id], gold[case_id], calls[case_id])
                rows[case_id] = row
                write_json(out / "cases" / f"{case_id}.json", row)
                print(f"{case['split']} {case_id} scored", flush=True)
    return [rows[case["id"]] for case in cases]


def aggregate(rows, split):
    counts = {arm: {key: sum(row["scores"][arm][key] for row in rows)
                    for key in rows[0]["scores"][arm]} for arm in ARMS}
    usage = {arm: {key: sum(row["calls"][arm]["usage"][key] for row in rows)
                   for key in rows[0]["calls"][arm]["usage"]} for arm in ARMS}
    for arm in ARMS:
        usage[arm]["elapsed_seconds"] = round(sum(row["calls"][arm]["elapsed_seconds"] for row in rows), 2)
    new, current, astra = (counts[arm] for arm in ("candidate", "current", "astra"))
    numerator, denominator = (4, 5) if split == "pilot" else (3, 4)
    gate = (new["exact"] * denominator >= len(rows) * numerator and new["eligible_exact"] > 0
            and new["exact"] > current["exact"] and not new["unsafe"]
            and not any(values["missing"] for values in counts.values()))
    return {"n": len(rows), "scores": counts, "usage": usage, "gate": gate,
            "lead_over_both": gate and new["exact"] > astra["exact"]}


def csv_file(path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def reviewed_answer(decision):
    if decision is None:
        return {"status": None, "new_low": None, "new_high": None, "remaining_delta": None, "evidence_ids": []}
    return {key: decision[key] for key in ("status", "new_low", "new_high", "remaining_delta", "evidence_ids")}


def fragment(case, ref):
    return f"{case['id']}-{ref}"


def review_header(title):
    return (
        '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{escape(title)}</title>'
        '<style>body{max-width:950px;margin:3rem auto;padding:0 1rem;color:#162437;'
        'font:16px/1.6 system-ui,sans-serif}h1,h2,h3{line-height:1.3}'
        'a{color:#115585}article,section{margin:2rem 0}dl{display:grid;grid-template-columns:9rem auto;'
        'margin:0}dd{margin:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit}'
        'div.source{border-left:3px solid #bccada;padding-left:1rem;margin:1rem 0}'
        ':target{background:#fff2c6}details{margin:.25rem 0}code{overflow-wrap:anywhere}</style>'
    )


def source_html(case, documents, *, backlink=None):
    parts = []
    for document in documents:
        source = escape(document["source_url"], quote=True)
        published = escape(document["published_at"])
        parts.append(f'<h3>{escape(document["id"])}</h3><p>公告時點 {published}。'
                     f'<a href="{source}" target="_blank" rel="noopener noreferrer">開啟發行人公告</a></p>')
        for block in document["blocks"]:
            block_id = escape(fragment(case, block["id"]), quote=True)
            parts.append(f'<div class="source" id="{block_id}"><code>{escape(block["id"])}</code>'
                         f'<pre>{escape(block["text"])}</pre>')
            if backlink:
                parts.append(f'<a href="#{backlink}">返回該案的待覆核回答</a>')
            parts.append("</div>")
    return "\n".join(parts)


def delivery_pack(out, rows, inputs, protocol):
    pack = out / "analyst-review"
    pack.mkdir(exist_ok=True)
    filing_views = out / "filing-view"
    filing_views.mkdir(exist_ok=True)
    header = "完整公告營收覆核"
    rubric = ("請獨立核對財季、會計與合併口徑、更新後指引區間、封存現估的差額，以及原文是否足以覆核。"
              "結果欄請填 1（可採用）、0（需退回）或 u（無法確認）。如有重大錯誤或補件要求請附原文位置。")
    pages = [review_header(header), f"<h1>{header}</h1><p>{rubric}</p>",
             '<p><a href="review-form.csv">下載空白評分表</a></p>',
             '<nav aria-label="案例">' + " · ".join(
                 f'<a href="#answers-{row["id"]}">{escape(row["ticker"])}</a>' for row in rows
             ) + "</nav>"]
    records, answer_key = [], {}
    for row in rows:
        data = inputs[row["id"]]
        case_id = row["id"]
        links = source_html(row, data["documents"], backlink=f"answers-{case_id}")
        source_title = f"{row['ticker']} 封存公告全文"
        (filing_views / f"{case_id}.html").write_text(
            review_header(source_title) + f"<h1>{escape(source_title)}</h1>" + source_html(row, data["documents"]),
            encoding="utf-8",
        )
        pages.append(f'<article id="answers-{case_id}"><h2>{escape(row["issuer"])}</h2>'
                     f'<p>目標財季 {escape(row["target"]["period_end"])}。'
                     f'使用截至 {escape(row["as_of"])} 可見的資料。'
                     f'現估 {Decimal(row["baseline"]["amount"]):,f} {escape(row["target"]["currency"])}。</p>')
        order = sorted(ARMS, key=lambda arm: sha256(
            f"{protocol['model_input_sha256']}:{case_id}:{arm}".encode()
        ).digest())
        for slot, arm in enumerate(order, 1):
            anonymous_id = f"{case_id}-R{slot}"
            answer_key[anonymous_id] = arm
            decision = reviewed_answer(row["decisions"][arm])
            citations = [
                f'<a href="#{escape(fragment(row, ref), quote=True)}">{escape(ref)}</a>'
                for ref in decision["evidence_ids"] if ref in row["citations"]
            ]
            known_decision = decision if decision["status"] else None
            pages.append(f'<section><h3>回答 {slot}</h3>'
                         f'<p>{escape(raw.show_decision(known_decision))}</p>'
                         '<p>原文定位 ' + (" · ".join(citations) or "未提供") + '</p></section>')
            records.append({"review_item": anonymous_id, "issuer": row["ticker"], "reviewer": "",
                            "scope_ok": "", "range_ok": "", "delta_ok": "", "sources_ok": "",
                            "ready_to_use": "", "severity": "", "notes": ""})
        pages.append(f"<h3>完整公告證據</h3>{links}</article>")
    (pack / "review.html").write_text("\n".join(pages), encoding="utf-8")
    csv_file(pack / "review-form.csv", list(records[0]), records)
    with ZipFile(out / "analyst-review.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for name in ("review.html", "review-form.csv"):
            bundle.write(pack / name, arcname=name)
    write_json(out / "review-key.restricted.json", answer_key)


def scorecard(out, rows):
    flat = []
    for row in rows:
        for arm in ARMS:
            decision = reviewed_answer(row["decisions"][arm])
            call = row["calls"][arm]
            flat.append({"case": row["id"], "split": row["split"], "ticker": row["ticker"], "arm": arm,
                         **{key: value for key, value in decision.items() if key != "evidence_ids"},
                         "evidence_ids": " ".join(decision["evidence_ids"]),
                         **{key: int(value) for key, value in row["scores"][arm].items()},
                         **call["usage"], "seconds": call["elapsed_seconds"],
                         "failure": call.get("error", "")})
    csv_file(out / "scores.csv", list(flat[0]), flat)


def render(out, rows, summary):
    lines = [
        "# 完整公告的營收指引覆核", "",
        "三組取得同一份截止前封存的完整公司公告及現估。正文依原順序保存段落及表格，"
        "每案各一次模型呼叫，搜尋與工具關閉。正文及模型回傳均可逐案檢查。", "",
        "[預註冊與停止條件](protocol.md) · [封存輸入](inputs.json) · [評分表](scores.csv)"
        " · [數字摘要](summary.json) · [分析師匿名覆核包](analyst-review.zip)", "",
    ]
    for split, label in (("pilot", "先導"), ("holdout", "保留集")):
        lines.extend([f"## {label}", ""])
        result = summary["splits"].get(split)
        if result is None:
            lines.extend(["依預註冊停止規則，未執行保留集。", ""])
            continue
        lines.extend([f"流程門檻 **{'通過' if result['gate'] else '未通過'}**，共 {result['n']} 案。", ""])
        if split == "holdout":
            lines.extend([f"領先現版和純 Astra 的門檻 **{'通過' if result['lead_over_both'] else '未通過'}**。", ""])
        lines.extend(["| 組別 | 全對 | 金額 | 區間 | 引文 | 誤調 | 缺少回覆 |",
                      "|---|---:|---:|---:|---:|---:|---:|"])
        for arm, label in ARMS.items():
            metrics = result["scores"][arm]
            columns = ("exact", "delta_exact", "range_exact", "citations", "unsafe", "missing")
            lines.append(f"| {label} | " + " | ".join(str(metrics[key]) for key in columns) + " |")
        lines.extend(["", "| 組別 | 輸入詞元 | 快取輸入詞元 | 輸出詞元 | 累計秒數 |",
                      "|---|---:|---:|---:|---:|"])
        for arm, label in ARMS.items():
            usage = result["usage"][arm]
            lines.append(f"| {label} | {usage['input_tokens']:,} | {usage['cached_input_tokens']:,} | "
                         f"{usage['output_tokens']:,} | {usage['elapsed_seconds']:.2f} |")
        lines.extend(["", "| 案例 | 裁定 | 現版 | 新版 | 純 Astra |", "|---|---|---|---|---|"])
        for row in rows:
            if row["split"] != split:
                continue
            expected = row["expected"]
            allowed = expected["disposition"] != "blocked"
            gold = raw.show_decision({**expected, "status": expected["disposition"],
                                      "remaining_delta": expected["delta"] if allowed else None})
            ticker, case_id = row["ticker"], row["id"]
            decisions = " | ".join(raw.show_decision(decision) for decision in row["decisions"].values())
            lines.append(f"| [{ticker}](cases/{case_id}.json) | {gold} | {decisions} |")
        lines.append("")
        for row in rows:
            if row["split"] == split:
                new = row["decisions"]["candidate"]
                case_id = row["id"]
                evidence = []
                if new:
                    evidence = [
                        f"[{ref}](filing-view/{case_id}.html#{fragment(row, ref)})"
                        for ref in new["evidence_ids"] if ref in row["citations"]
                    ]
                note = (" " + " · ".join(evidence)) if evidence else ""
                lines.append(f"- **{row['ticker']}** [公告正文](filing-view/{case_id}.html){note}")
        lines.append("")
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--run-model", action="store_true")
    args = parser.parse_args()
    cases, gold, inputs = load_inputs()
    seal(args.out, cases, inputs)
    protocol = prior.load(args.out / "protocol.json")
    print(f"Frozen protocol: {args.out / 'protocol.json'}", flush=True)
    if not args.run_model:
        return
    os.environ["RESEARCH_CODEX_MODEL"] = MODEL
    summary = {"model": MODEL, "effort": EFFORT, "splits": {}, "holdout_attempted": False}
    rows = []
    for split in SPLITS:
        selected = [case for case in cases if case["split"] == split]
        group = run_split(selected, inputs, gold, args.out, args.workers)
        summary["splits"][split] = result = aggregate(group, split)
        summary["holdout_attempted"] = split == "holdout"
        rows.extend(group)
        write_json(args.out / "summary.json", summary)
        scorecard(args.out, rows)
        delivery_pack(args.out, rows, inputs, protocol)
        render(args.out, rows, summary)
        print(f"{split}: {json.dumps(result, ensure_ascii=False)}", flush=True)
        if not result["gate"]:
            break


if __name__ == "__main__":
    main()
