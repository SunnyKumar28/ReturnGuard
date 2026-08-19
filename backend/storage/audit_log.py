"""
Append-only audit log. Every decision trace (planner choices, fetcher outputs, rule
verdict, analyzer rationale, guardrail result) is written here so any action can be
explained after the fact.
"""
import json
import threading
from pathlib import Path

from backend.config import settings
from backend.models.schemas import DecisionTrace

_lock = threading.Lock()


def _log_path() -> Path:
    return Path(settings.audit_log_path)


def append_audit_record(trace: DecisionTrace) -> None:
    with _lock:
        with _log_path().open("a", encoding="utf-8") as f:
            f.write(trace.model_dump_json() + "\n")


def read_all_records() -> list[DecisionTrace]:
    path = _log_path()
    if not path.exists():
        return []
    records: list[DecisionTrace] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(DecisionTrace.model_validate(json.loads(line)))
    return records


def get_record(order_id: str) -> DecisionTrace | None:
    for record in reversed(read_all_records()):
        if record.order_id == order_id:
            return record
    return None
