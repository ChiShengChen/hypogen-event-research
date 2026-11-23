"""New point-in-time Q2 cases for the T+2 residual study."""

import csv
from datetime import date
from pathlib import Path

from .earnings_horizon_inputs import CIKS, revenue_history
from .earnings_turns import reserved_cases

CASE_FILE = Path(__file__).with_name("earnings_residual_cases.csv")
DRIVER_LEDGER = Path(__file__).with_name("earnings_residual_driver_ledger.csv")


def load_holdout(sec_dir):
    """Withhold the matching fourth-quarter results from all model input packets."""
    directory = Path(sec_dir)
    history = revenue_history(directory, CIKS)
    for case in reserved_cases(directory, history, cases_path=CASE_FILE, method="guided_absolute"):
        yield {**case, "driver_inputs": []}


def load_driver_ledger(cases):
    """Load watchpoints separately so they cannot become forecast increments implicitly."""
    cutoffs = {case["id"]: case["event"].as_of.date() for case in cases}
    records = []
    with DRIVER_LEDGER.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            available = date.fromisoformat(row["available_on"])
            if available > cutoffs[row["case"]]:
                raise ValueError(f"{row['case']} 的營運訊號晚於研究截止時點")
            records.append(row)
    return records
