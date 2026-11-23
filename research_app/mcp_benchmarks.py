"""Run only registered benchmark presets and keep their original execution ledgers."""

import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from mcp.server.fastmcp.exceptions import ToolError

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = {
    "v9_equal_recovery": ("v9-equal-recovery", "summary.json"),
    "guidance_tables": ("guidance-table", "summary-holdout.json"),
    "guidance_ytd": ("guidance-ytd", "summary-holdout.json"),
}
RUNNER = "benchmarks.v9_equal_recovery"


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def job_dir(base, job_id):
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise ToolError("job_id / request_id 須為 32 位小寫十六進位 UUID。")
    return base / job_id


def archive_status(preset):
    name, summary = ARCHIVES[preset]
    directory = ROOT / "docs" / name
    return {"preset": preset, "source": "archived", "summary": read(directory / summary),
            "artifacts": [str(path) for path in sorted(directory.iterdir()) if path.suffix in {".csv", ".pdf", ".md"}]}


def job_status(base, job_id):
    directory = job_dir(base, job_id)
    state = read(directory / "status.json")
    if state is None:
        raise ToolError("找不到此正式評測任務。")
    if state["status"] in {"starting", "running", "publishing"}:
        with (directory / ".mcp-job.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                state = read(directory / "status.json")
                if state["status"] in {"starting", "running", "publishing"}:
                    state = state | {"status": "interrupted"}
    protocol = read(directory / "protocol.json")
    started = sum(1 for path in directory.glob("*/jobs/*/state.json")
                  if (read(path) or {}).get("started_at"))
    return state | {"job_id": job_id, "directory": str(directory), "started_calls": started,
                    "protocol": protocol, "summary": read(directory / "publication/summary.json"),
                    "execution_log": str(directory / "runner.log")}


def start(base, job_id, resume):
    directory = job_dir(base, job_id)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".mcp-job.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if not (directory / "status.json").exists():
                return {"job_id": job_id, "preset": "v9_equal_recovery", "status": "starting"}
            return job_status(base, job_id)
        previous = read(directory / "status.json")
        if previous and (not resume or previous["status"] == "complete" or previous.get("cooldown_blocked")):
            fcntl.flock(lock, fcntl.LOCK_UN)
            return job_status(base, job_id)
        if resume and previous is None:
            raise ToolError("續跑需要既有的 job_id。")
        with (base / ".active.lock").open("a") as active:
            try:
                fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ToolError("已有 Hypogen 正式批次在執行。") from exc
            state = {"preset": "v9_equal_recovery", "status": "starting"}
            save(directory / "status.json", state)
            try:
                with (directory / "runner.log").open("ab") as log:
                    locks = (lock.fileno(), active.fileno())
                    subprocess.Popen([sys.executable, "-m", "research_app.mcp_benchmarks", str(directory), *map(str, locks)],
                                     cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                     start_new_session=True, pass_fds=locks)
            except OSError:
                save(directory / "status.json", state | {"status": "launch_failed"})
                raise
    return job_status(base, job_id)


def worker(directory, locks):
    state_path = directory / "status.json"
    state = read(state_path)
    if state is None:
        raise ValueError("Expected a registered benchmark job")
    save(state_path, state | {"status": "running"})
    command = [sys.executable, "-m", RUNNER, "--out", str(directory)]
    result = subprocess.run([*command, "--phase", "run"], cwd=ROOT, check=False, pass_fds=locks)
    if result.returncode not in {0, 2} or not (directory / "protocol.json").is_file():
        save(state_path, state | {"status": "stopped", "run_exit": result.returncode})
        return
    save(state_path, state | {"status": "publishing", "run_exit": result.returncode})
    report = subprocess.run([*command, "--phase", "report"], cwd=ROOT, check=False, pass_fds=locks)
    summary = read(directory / "publication/summary.json")
    status = "report_failed"
    if report.returncode == 0 and summary is not None:
        status = "complete" if summary["recovery_passed"] else "below_gate"
    blocked = any(read(path)["status"] == "blocked" for path in directory.glob("cooldowns/*.json"))
    save(state_path, state | {"status": status, "run_exit": result.returncode, "report_exit": report.returncode,
                              "cooldown_blocked": blocked})


if __name__ == "__main__":
    worker(Path(sys.argv[1]), tuple(map(int, sys.argv[2:])))
