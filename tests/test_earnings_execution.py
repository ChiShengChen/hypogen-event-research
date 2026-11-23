import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep

from benchmarks import earnings_execution as execution


def test_budget_accounts_for_every_wave():
    assert execution.budget(8, 4) == 2 * (240 + 10) + 60
    assert execution.budget(5, 4) == 2 * (240 + 10) + 60


def test_restart_accounts_for_abruptly_lost_running_job(tmp_path):
    job, _ = execution.schedule(tmp_path, [{"id": "applied"}])
    state = execution.restore(tmp_path, job)
    execution.save_state(job, state, status="running")
    record = execution.restore(tmp_path, job)
    assert record["status"] == "interrupted"
    assert record["elapsed_seconds"] is None
    assert execution.restore(tmp_path, job) == record


def test_process_signal_preserves_active_attempt_and_resumes_only_queued(tmp_path):
    codex = tmp_path / "codex"
    marker = tmp_path / "attempts"
    codex.write_text(f"""#!{sys.executable}
import json, os, sys, time
from pathlib import Path
with Path(os.environ['ATTEMPTS']).open('a') as handle:
    handle.write('started\\n')
print(json.dumps({{'type': 'turn.started'}}), flush=True)
if os.getenv('BLOCK_CALL'):
    time.sleep(60)
output = Path(sys.argv[sys.argv.index('--output-last-message') + 1])
output.write_text(json.dumps({{'status':'blocked', 'new_low':None, 'new_high':None,
                             'remaining_delta':None, 'evidence_ids':[], 'reason':'test'}}))
print(json.dumps({{'type':'turn.completed', 'usage':{{'input_tokens':1}}}}), flush=True)
""")
    codex.chmod(0o755)
    program = """
from pathlib import Path
from threading import Event
import signal, sys
from benchmarks.earnings_execution import run_batch, exclusive
stop = Event()
signal.signal(signal.SIGTERM, lambda *_: stop.set())
out = Path(sys.argv[1])
with exclusive(out):
    run_batch(out, [{'id':'fixture'}], {'fixture':{'archive':'test'}}, 1, stop)
"""
    env = os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}", "ATTEMPTS": str(marker)}
    command = [sys.executable, "-c", program, str(tmp_path)]
    with subprocess.Popen(command, env=env | {"BLOCK_CALL": "1"}) as process:
        journal = tmp_path / "jobs/fixture-extract/events.jsonl"
        deadline = monotonic() + 7
        while (not journal.exists() or not journal.read_text()) and monotonic() < deadline:
            sleep(0.02)
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=7) == 0
    active = json.loads((tmp_path / "calls/fixture-extract.json").read_text())
    queued = json.loads((tmp_path / "jobs/fixture-astra/state.json").read_text())
    assert active["status"] == "interrupted"
    assert "turn.started" in active["event_seconds"]
    assert queued["status"] == "queued"
    assert marker.read_text().splitlines() == ["started"]

    subprocess.run(command, env=env, check=True, timeout=7)
    assert marker.read_text().splitlines() == ["started", "started"]
    assert json.loads((tmp_path / "calls/fixture-extract.json").read_text()) == active
    assert json.loads((tmp_path / "calls/fixture-astra.json").read_text())["status"] == "completed"
