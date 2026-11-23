import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep

import pytest

from benchmarks import v9_equal as run
from benchmarks import v9_equal_review as review
from benchmarks.hypothesis_pilot import read


def test_seal_keeps_v9_and_astra_evidence_equal_and_blocks_holdout(tmp_path):
    cases, requests = run.seal(tmp_path)
    assert [len([case for case in cases.values() if case["split"] == split])
            for split in ("pilot", "holdout")] == [4, 8]
    for key, case in cases.items():
        context = {arm: json.loads(request["prompt"].split("\n\n", 1)[1])
                   for arm, request in requests[key].items()}
        assert all(context["astra"][field] == context["v9"][field] == value
                   for field, value in case["input"].items())
    check = subprocess.run([sys.executable, "-m", "benchmarks.v9_equal", "--out", str(tmp_path),
                            "--phase", "holdout"], capture_output=True, timeout=5)
    assert check.returncode == 2
    assert not (tmp_path / "jobs").exists()
    archive = tmp_path / "requests.json"
    archive.write_text("{}")
    with pytest.raises(ValueError, match="被改動"):
        run.seal(tmp_path)


def test_signal_preserves_started_call_and_resumes_queued_calls(tmp_path):
    cli = tmp_path / "codex"
    cli.write_text(f"""#!{sys.executable}
import json, os, sys, time
from pathlib import Path
from research_app.adapters import Fixture
with Path(os.environ['V9_TEST_MARKER']).open('a') as handle:
    handle.write('started\\n')
print(json.dumps({{'type': 'turn.started'}}), flush=True)
if os.environ.get('V9_TEST_BLOCK'):
    time.sleep(30)
prompt = sys.stdin.read()
context = json.loads(prompt.split('\\n\\n', 1)[1])
if 'claims' in context:
    reply = Fixture().hypotheses(context).model_dump_json()
else:
    row = {{k: 'fixture' for k in ('company','mechanism','catalyst','prediction','invalidation','materiality')}}
    row['evidence_ids'] = [context['evidence'][0]['id']]
    reply = json.dumps({{'first': row, 'second': row}})
Path(sys.argv[sys.argv.index('--output-last-message') + 1]).write_text(reply)
print(json.dumps({{'type': 'turn.completed', 'usage': {{'input_tokens': 42}}}}), flush=True)
""")
    cli.chmod(0o755)
    output = tmp_path / "formal"
    marker = tmp_path / "attempts"
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}", "V9_TEST_MARKER": str(marker),
        "PYTHONPATH": str(Path(run.__file__).resolve().parents[1]),
    }
    command = [sys.executable, "-m", "benchmarks.v9_equal", "--phase", "pilot", "--out", str(output)]
    with subprocess.Popen(command, env=env | {"V9_TEST_BLOCK": "yes"}) as process:
        journal = output / "jobs/V-01-astra/events.jsonl"
        deadline = monotonic() + 6
        while (not journal.exists() or not journal.read_text()) and monotonic() < deadline:
            sleep(0.02)
        assert journal.exists()
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=6) == 2
    active = run.receipt(output, "V-01", "astra")
    assert active["status"] == "interrupted"
    assert active["usage"] is None
    assert read(output / "jobs/V-01-v9/state.json")["status"] == "queued"
    resumed = subprocess.run(command, env=env, timeout=10)
    assert resumed.returncode == 2
    assert len(marker.read_text().splitlines()) == 8
    assert active == run.receipt(output, "V-01", "astra")
    assert run.receipt(output, "V-02", "astra")["usage"]["input_tokens"] == 42
    assert run.receipt(output, "V-02", "v9")["status"] == "completed"


def test_limit_events_stop_stage_and_queued_calls_are_preserved(tmp_path, monkeypatch):
    cases, requests = run.seal(tmp_path)
    initiated = []

    def rejected(root, job, case, request, stop, deadline, timeout):
        state = run.journal.restore(root, job)
        initiated.append((state["case"], state["call"]))
        return run.journal.finish(root, job, state, status="error", reason="rate_limit")

    monkeypatch.setattr(run, "attempt", rejected)
    assert run.rate_event({"type": "error", "message": "HTTP 429"})
    run.run(tmp_path, cases, requests, "pilot", run.Event())
    run.run(tmp_path, cases, requests, "pilot", run.Event())
    assert initiated == [("V-01", "astra")]
    assert read(tmp_path / "jobs/V-01-v9/state.json")["status"] == "queued"
    assert len(list((tmp_path / "batches").glob("*.json"))) == 1


def test_cli_rate_limit_on_stderr_is_detected_without_waiting(tmp_path, monkeypatch):
    cli = tmp_path / "codex"
    cli.write_text(f"""#!{sys.executable}
import sys, time
print('sampling_error=exceeded retry limit, last status: 429 Too Many Requests', file=sys.stderr, flush=True)
time.sleep(30)
""")
    cli.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    output = tmp_path / "run"
    with run.journal.exclusive(output):
        cases, requests = run.seal(output)
        run.run(output, cases, requests, "pilot", run.Event())
    rejected = run.receipt(output, "V-01", "astra")
    assert rejected["reason"] == "rate_limit" and rejected["rate_limit_source"] == "stderr"
    assert rejected["elapsed_seconds"] < 2
    assert read(output / "jobs/V-01-v9/state.json")["status"] == "queued"


def test_review_uses_complete_holdout_pairs_and_local_identity_key(tmp_path):
    cases, _ = run.frozen_cases()
    calls = review.read_calls(tmp_path, cases)
    archived = {
        "astra": read(review.REF / "V-01/astra-direct.json")["hypotheses"],
        "v9": read(review.REF / "V-01/current-harness.json")["hypotheses"],
    }
    for key, case in cases.items():
        if case["split"] == "holdout":
            for arm in run.ARMS:
                calls[key, arm] |= {"status": "completed", "elapsed_seconds": 1, "hypotheses": archived[arm]}
    selected = review.review_set(cases, calls)
    mapping = review.anonymous_keys(tmp_path, selected)
    assert review.anonymous_keys(tmp_path, selected) == mapping
    public = tmp_path / "public"
    public.mkdir()
    review.blind_files(public, selected, mapping)
    assert not list(public.glob("*restricted*"))
    with (public / "review-form.csv").open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if not row["case"].startswith("E-"):
            continue
        arm = mapping[row["case"]][row["code"]]["arm"]
        ready = "1" if arm == "v9" else "0"
        row.update({field: ready for field in review.RATINGS})
        row.update(analyst_id="reviewer-1", major_errors="0", ready=ready, edit_seconds="10")
    filled = tmp_path / "ratings.csv"
    review.write_csv(filled, review.REVIEW_FIELDS, rows)
    reviews = review.import_ratings(filled, selected, mapping)
    assert review.review_metrics(cases, calls, {})["passed"] is None
    assert review.review_metrics(cases, calls, reviews)["passed"] is True
    reviews["E-01", "v9"]["major_errors"] = 1
    assert review.review_metrics(cases, calls, reviews)["passed"] is False
