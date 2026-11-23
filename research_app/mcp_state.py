"""Local attachment and request records shared across MCP sessions."""

import base64
import hashlib
import json
import re
from pathlib import Path

from mcp.server.fastmcp.exceptions import ToolError

from .hypothesis_inputs import FILE_TYPES, MAX_FILE_BYTES
from .store import encode


class ConversationState:
    def __init__(self, store, inbox):
        self.store = store
        self.inbox = inbox.resolve()
        with store.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS mcp_attachments (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, content BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mcp_requests (
                    tool TEXT NOT NULL, id TEXT NOT NULL, digest TEXT NOT NULL,
                    status TEXT NOT NULL, result TEXT,
                    PRIMARY KEY (tool, id)
                );
            """)

    def attach(self, filename):
        path = (self.inbox / filename).resolve()
        if Path(filename).name != filename or path.parent != self.inbox:
            raise ToolError("請指定 Hypogen 收件目錄中的單一檔名。")
        if path.suffix.lower() not in FILE_TYPES | {".html", ".htm"} or not path.is_file():
            raise ToolError("收件目錄中找不到此檔案，或檔案格式不支援。")
        with path.open("rb") as file:
            content = file.read(MAX_FILE_BYTES + 1)
        if not 0 < len(content) <= MAX_FILE_BYTES:
            raise ToolError("附件須有內容，且最多 2 MB。")
        attachment_id = hashlib.sha256(filename.encode() + b"\0" + content).hexdigest()
        with self.store.connection() as db:
            db.execute("INSERT OR IGNORE INTO mcp_attachments VALUES (?, ?, ?)",
                       (attachment_id, filename, content))
        return {"attachment_id": attachment_id, "filename": filename, "bytes": len(content)}

    def attachment(self, attachment_id):
        with self.store.connection() as db:
            row = db.execute("SELECT filename, content FROM mcp_attachments WHERE id = ?", (attachment_id,)).fetchone()
        if not row:
            raise ToolError("這個附件 ID 在目前的研究資料庫不存在。")
        return row

    def branch_file(self, attachment_id, available_on):
        filename, content = self.attachment(attachment_id)
        if Path(filename).suffix.lower() not in FILE_TYPES:
            raise ToolError("假說分支支援 PDF、TXT、CSV、JSON 和 Markdown 附件。")
        return {"kind": "file", "filename": filename, "data": base64.b64encode(content).decode("ascii"),
                "available_on": available_on.isoformat() if available_on else None}

    def attachment_text(self, attachment_id):
        _, content = self.attachment(attachment_id)
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ToolError("公告或共識資料須為 UTF-8 文字檔。") from exc

    async def once(self, tool, request_id, payload, action):
        if not re.fullmatch(r"[A-Za-z0-9_-]{12,80}", request_id):
            raise ToolError("request_id 須為 UUID 或 12–80 個英數、底線及連字號。")
        digest = hashlib.sha256(encode(payload).encode()).hexdigest()
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT digest, status, result FROM mcp_requests WHERE tool = ? AND id = ?",
                             (tool, request_id)).fetchone()
            if row:
                if row[0] != digest:
                    raise ToolError("request_id 已用於不同輸入。")
                if row[1] == "complete":
                    return json.loads(row[2])
                if row[1] == "failed":
                    raise ToolError(row[2])
                raise ToolError("此請求已送出。請先查報告或假說樹確認是否已保存，再決定是否另開請求。")
            db.execute("INSERT INTO mcp_requests VALUES (?, ?, ?, 'sent', NULL)", (tool, request_id, digest))
        try:
            result = await action()
        except ToolError as exc:
            with self.store.connection() as db:
                db.execute("UPDATE mcp_requests SET status = 'failed', result = ? WHERE tool = ? AND id = ?",
                           (str(exc), tool, request_id))
            raise
        with self.store.connection() as db:
            db.execute("UPDATE mcp_requests SET status = 'complete', result = ? WHERE tool = ? AND id = ?",
                       (encode(result), tool, request_id))
        return result
