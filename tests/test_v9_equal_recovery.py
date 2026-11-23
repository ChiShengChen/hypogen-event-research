from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep

import pytest

from benchmarks import v9_equal_recovery as recovery
from benchmarks import v9_equal_recovery_review as report
from benchmarks.v9_equal import Event
from benchmarks.hypothesis_pilot import read


@pytest.fixture
def fake_cli(tmp_path):
    executable = tmp_path / "codex"
    marker = tmp_path / "starts.jsonl"
    executable.write_text(f"""#!{sys.executable}
import json, os, sys, time
from pathlib import Path
from research_app.adapters import Fixture

answer = Path(sys.argv[sys.argv.index('--output-last-message') + 1])
job, round_name = answer.parent.name, answer.parents[2].name
tag = f'{{round_name}}/{{job}}'
with Path(os.environ['V9_RECOVERY_MARKER']).open('a') as output:
    output.write(json.dumps(tag) + '\\n')
print(json.dumps({{'type': 'turn.started'}}), flush=True)
if tag == os.environ.get('V9_RECOVERY_BLOCK'):
    time.sleep(60)
if tag in os.environ.get('V9_RECOVERY_RATE', '').split(','):
    delay = os.environ.get('V9_RECOVERY_DELAY', '0s')
    print(f'retrying sampling request (1/5 in {{delay}})... sampling_error=last status: 429 Too Many Requests',
          file=sys.stderr, flush=True)
    time.sleep(60)
context = json.loads(sys.stdin.read().split('\\n\\n', 1)[1])
if 'claims' in context:
    result = Fixture().hypotheses(context).model_dump_json()
else:
    item = {{field: tag for field in ('company', 'mechanism', 'catalyst', 'prediction', 'invalidation', 'materiality')}}
    item['evidence_ids'] = [context['evidence'][0]['id']]
    result = json.dumps({{'first': item, 'second': item}})
answer.write_text(result)
print(json.dumps({{'type': 'turn.completed', 'usage': {{'input_tokens': 42}}}}), flush=True)
""")
    executable.chmod(0o755)
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}", "V9_RECOVERY_MARKER": str(marker),
        "PYTHONPATH": str(Path(recovery.__file__).resolve().parents[1]),
    }
    output = tmp_path / "run"
    command = [sys.executable, "-m", "benchmarks.v9_equal_recovery", "--phase", "run", "--out", str(output)]
    return output, command, env, marker


def spawned(marker):
    return [json.loads(line) for line in marker.read_text().splitlines()]


def wait_for_file(path):
    deadline = monotonic() + 5
    while (not path.exists() or not path.stat().st_size) and monotonic() < deadline:
        sleep(0.01)
    assert path.stat().st_size


def test_complete_pairs_only_use_same_round_and_reverse_call_order(fake_cli):
    output, command, env, marker = fake_cli
    env |= {"V9_RECOVERY_RATE": "first/V-01-v9,first/V-02-v9", "V9_RECOVERY_DELAY": "5ms"}
    subprocess.run(command, env=env, check=True, timeout=20)
    starts = spawned(marker)
    assert starts[:7] == ["first/V-01-astra", "first/V-01-v9", "recovery/V-01-v9", "recovery/V-01-astra",
                         "first/V-02-v9", "recovery/V-02-astra", "recovery/V-02-v9"]
    cases, _, protocol = recovery.read_sealed(output)
    calls = recovery.records(output, cases)
    assert protocol["generation_timeout_seconds"] == 180 and protocol["max_cooldown_seconds"] == 900
    assert calls["V-01", "first", "astra"]["usage"]["input_tokens"] == 42
    assert calls["V-01", "first", "v9"]["reason"] == "rate_limit"
    assert calls["V-02", "first", "astra"]["status"] == "queued"
    for key in ("V-01", "V-02"):
        assert recovery.complete_round(calls, key, "recovery")
        assert not recovery.complete_round(calls, key, "first")
        cool = read(output / "cooldowns" / f"{key}-first.json")
        assert cool["reported_wait_seconds"] == 0.005
        assert cool["elapsed_seconds"] >= 1
        first_arm, _ = protocol["orders"][key]["recovery"]
        assert datetime.fromisoformat(calls[key, "recovery", first_arm]["started_at"]) >= datetime.fromisoformat(cool["resume_at"])
    selected, origin = report.select_pairs(cases, calls)
    assert origin == {"V-01": "recovery", "V-02": "recovery", "V-03": "first", "V-04": "first"}
    assert selected["V-01"][1]["astra"]["first"]["company"] == "recovery/V-01-astra"
    calls["V-01", "recovery", "astra"] = {"status": "timeout"}
    assert "V-01" not in report.select_pairs(cases, calls)[0]
    subprocess.run(command, env=env, check=True, timeout=10)
    assert spawned(marker) == starts


def test_over_cap_cooldown_stops_entire_batch(fake_cli):
    output, command, env, marker = fake_cli
    env |= {"V9_RECOVERY_RATE": "first/V-01-astra", "V9_RECOVERY_DELAY": "900.01s"}
    for _ in range(2):
        assert subprocess.run(command, env=env, timeout=7).returncode == 2
    decision = read(output / "cooldowns/V-01-first.json")
    assert decision["status"] == "blocked" and decision["reported_wait_seconds"] == 900.01
    assert spawned(marker) == ["first/V-01-astra"]


def test_sigterm_keeps_cooldown_and_only_starts_reverse_pair_once(fake_cli):
    output, command, env, marker = fake_cli
    env |= {"V9_RECOVERY_RATE": "first/V-01-astra", "V9_RECOVERY_DELAY": "2.1s"}
    with subprocess.Popen(command, env=env) as process:
        path = output / "cooldowns/V-01-first.json"
        wait_for_file(path)
        before = read(path)
        assert before["status"] == "waiting"
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=6) == 2
    assert read(path) == before
    assert spawned(marker) == ["first/V-01-astra"]
    subprocess.run(command, env=env, check=True, timeout=20)
    assert read(path)["resume_at"] == before["resume_at"]
    assert spawned(marker)[:3] == ["first/V-01-astra", "recovery/V-01-v9", "recovery/V-01-astra"]


def test_sigterm_during_cli_preserves_receipt_and_resumes_only_unstarted_arms(fake_cli):
    output, command, env, marker = fake_cli
    with subprocess.Popen(command, env=env | {"V9_RECOVERY_BLOCK": "first/V-01-astra"}) as process:
        wait_for_file(output / "first/jobs/V-01-astra/events.jsonl")
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=6) == 2
    path = output / "first/calls/V-01-astra.json"
    before = path.read_bytes()
    assert json.loads(before)["status"] == "interrupted"
    assert spawned(marker) == ["first/V-01-astra"]
    assert subprocess.run(command, env=env, timeout=15).returncode == 2
    assert path.read_bytes() == before
    assert len(spawned(marker)) == 8
    assert not (output / "recovery").exists()


def test_single_call_timeout_preserves_failure_and_queued_sibling(fake_cli, monkeypatch):
    output, _, env, marker = fake_cli
    for key, value in env.items():
        if key in {"PATH", "PYTHONPATH", "V9_RECOVERY_MARKER"}:
            monkeypatch.setenv(key, value)
    monkeypatch.setenv("V9_RECOVERY_BLOCK", "first/V-01-astra")
    with recovery.exclusive(output):
        cases, requests, protocol = recovery.seal(output)
        result = recovery.run_round(output / "first", "V-01", cases["V-01"], requests["V-01"],
                                    protocol["orders"]["V-01"]["first"], Event(), 0.5)
    assert result["status"] == "timeout" and result["reason"] == "per_call_deadline"
    assert read(output / "first/jobs/V-01-v9/state.json")["status"] == "queued"
    assert spawned(marker) == ["first/V-01-astra"]
