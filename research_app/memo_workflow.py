"""Freeze draft content and record authenticated internal review decisions."""

from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
import json
import os
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import HTTPException
from pydantic import Field

from .earnings import EarningsError
from .revision_memo import fingerprint
from .schema import Amount, Nonempty, Schema
from .store import MissingReport, encode


class MemoSignoff(Schema):
    decision: Literal["approved", "changes_requested"]
    note: Annotated[Nonempty, Field(max_length=6000)]
    conflict_check: Literal["clear", "disclosed", "unresolved"]
    duration_seconds: Annotated[Amount, Field(ge=0)] | None = None


def identity(header, *, required=False):
    if not header and not required:
        return None
    try:
        identities = json.loads(os.getenv("RESEARCH_MEMO_IDENTITIES", "{}"))
        if not isinstance(identities, dict):
            raise ValueError
        for name, entry in identities.items():
            if (not name or not isinstance(entry, dict) or entry.get("role") not in {"author", "reviewer", "approver"}
                    or not isinstance(entry.get("token_sha256"), str) or len(entry["token_sha256"]) != 64):
                raise ValueError
        if len({entry["token_sha256"] for entry in identities.values()}) != len(identities):
            raise ValueError
    except ValueError as exc:
        raise HTTPException(503, "研究覆核身分設定無效。") from exc
    if not identities:
        raise HTTPException(503, "此部署尚未設定研究覆核身分。")
    prefix, _, supplied = (header or "").partition(" ")
    if prefix.lower() == "bearer" and supplied:
        digest = sha256(supplied.encode()).hexdigest()
        for name, entry in identities.items():
            if compare_digest(entry["token_sha256"], digest):
                return {"name": name, "role": entry["role"]}
    raise HTTPException(401, "需要已配置的研究身分憑證。", headers={"WWW-Authenticate": "Bearer"})


def freeze(store, memo, actor):
    memo = {**memo, "author": actor["name"] if actor else None}
    report_id, revision = memo["report_id"], memo["report_revision"]
    store._earnings_action(report_id, revision, "revision_memo", fingerprint(memo), memo, datetime.now(timezone.utc))
    return load(store, report_id, revision, fingerprint(memo))


def _load(db, report_id, revision, memo_id):
    row = db.execute("""
        SELECT payload, recorded_at FROM earnings_log WHERE report_id=? AND revision=? AND kind='revision_memo'
          AND action_key=?
    """, (report_id, revision, memo_id)).fetchone()
    if not row:
        raise MissingReport("找不到財報預估修正稿。")
    memo = json.loads(row[0])
    if fingerprint(memo) != memo_id:
        raise EarningsError("修正稿內容與凍結指紋不符。")
    reviews = []
    for key, at, value in db.execute("""
        SELECT action_key, recorded_at, payload FROM earnings_log
        WHERE report_id=? AND revision=? AND kind='revision_memo_signoff' AND action_key LIKE ? ORDER BY rowid
    """, (report_id, revision, memo_id + ":%")):
        reviews.append({"id": key, "recorded_at": at, **json.loads(value)})
    status = "draft"
    if reviews:
        last = reviews[-1]
        status = ("changes_requested" if last["decision"] == "changes_requested" else
                  "approved_internal" if last["role"] == "approver" else "reviewed")
    return {"memo_id": memo_id, "memo": memo, "created_at": row[1], "status": status, "reviews": reviews}


def load(store, report_id, revision, memo_id):
    with store.connection() as db:
        return _load(db, report_id, revision, memo_id)


def sign(store, report_id, revision, memo_id, review, actor):
    if actor["role"] not in {"reviewer", "approver"}:
        raise HTTPException(403, "此身分無覆核權限。")
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        current = _load(db, report_id, revision, memo_id)
        memo = current["memo"]
        if current["status"] == "approved_internal":
            raise EarningsError("已內部核准的修正稿已凍結，請以新報告版次重開覆核。")
        if actor["name"] == memo["author"]:
            raise HTTPException(403, "作者須由不同身分覆核。")
        if review.decision == "approved" and review.conflict_check == "unresolved":
            raise EarningsError("利益衝突狀態須先釐清。")
        if actor["role"] == "approver":
            if current["status"] != "reviewed" or current["reviews"][-1]["actor"] == actor["name"]:
                raise EarningsError("須先由另一位已驗證的分析師覆核。")
            if review.decision == "approved" and (not memo["author"] or memo["gaps"]):
                raise EarningsError("內部核准須有具名作者，且已補齊修正稿上的重大證據缺口。")
        payload = {**review.model_dump(mode="json"), "actor": actor["name"], "role": actor["role"], "memo_id": memo_id}
        db.execute("INSERT INTO earnings_log VALUES (?, ?, ?, ?, ?, ?)", (
            report_id, revision, "revision_memo_signoff", f"{memo_id}:{uuid4().hex}",
            datetime.now(timezone.utc).isoformat(), encode(payload),
        ))
        return _load(db, report_id, revision, memo_id)
