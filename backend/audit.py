"""Audit trail: one entry per agent run, appended to output/audit_trail.json.

The file is always a valid JSON array, and it is APPEND-ONLY at the byte level: a new entry
is written over the closing "]" at the end of the file, so earlier entries are never
rewritten, and nothing is lost when the server restarts. A lock (thread + OS file lock)
keeps two simultaneous chats from interleaving their writes.

If the file is ever found damaged, it is NOT wiped: it's renamed to
audit_trail.damaged-<timestamp>.json and a fresh file is started next to it.

Privacy: entries record "guest" or "user:<id>" (never names or emails), and any email
address in messages or tool results is replaced with "[email]".
"""

import fcntl
import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import ModelMessage, RetryPromptPart, ToolCallPart, ToolReturnPart

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
SHORT = 200  # max characters kept for any one input/output
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
OUTPUT_TOOL = "final_result"  # PydanticAI's internal tool for the structured answer

log = logging.getLogger("campus_customs.audit")
_lock = threading.Lock()


def short(value: Any, limit: int = SHORT) -> str:
    """Compact, email-free text for the log."""
    as_data = lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o)  # noqa: E731
    text = value if isinstance(value, str) else json.dumps(value, default=as_data, ensure_ascii=False)
    text = EMAIL_RE.sub("[email]", " ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def tool_steps(messages: list[ModelMessage]) -> tuple[list[dict], list[str]]:
    """Each tool call with a short version of its input and output, plus any times an
    output validator sent Buddy's answer back (with the reason)."""
    calls: dict[str, dict] = {}
    order: list[str] = []
    retries: list[str] = []
    for msg in messages:
        for part in getattr(msg, "parts", []):
            if isinstance(part, ToolCallPart) and part.tool_name != OUTPUT_TOOL:
                calls[part.tool_call_id] = {"tool": part.tool_name, "input": short(part.args), "output": None}
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["output"] = short(part.content)
            elif isinstance(part, RetryPromptPart):
                retries.append(short(part.content, 160))
    return [calls[i] for i in order], retries


def append_entry(entry: dict) -> None:
    """Append one entry without ever rewriting what's already there."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(entry, ensure_ascii=False, indent=2)
    with _lock, open(AUDIT_PATH, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0, 2)
            if f.tell() == 0:
                f.write(f"[\n{body}\n]\n".encode())
                return
            # find the closing bracket at the end and write the new entry over it
            f.seek(max(0, f.tell() - 64))
            tail = f.read()
            end = tail.rstrip()
            if not end.endswith(b"]"):
                raise ValueError("audit file does not end with ']'")
            close_at = f.tell() - len(tail) + len(end) - 1
            f.seek(0)
            empty = close_at < 16 and f.read(close_at).strip() == b"["  # file is just "[ ]"
            f.truncate(close_at)  # removes only the final "]" (+ trailing newline)
            # opened in append mode, so this write lands at the (new) end of the file
            f.write(((b"\n" if empty else b",\n") + body.encode() + b"\n]\n"))
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def record(entry: dict) -> None:
    """Write an entry; never let logging problems break a chat."""
    try:
        append_entry(entry)
    except ValueError:
        damaged = AUDIT_PATH.with_name(f"audit_trail.damaged-{datetime.now():%Y%m%d-%H%M%S}.json")
        AUDIT_PATH.rename(damaged)  # keep it, never wipe it
        log.error("audit trail was damaged; kept as %s and started a new file", damaged.name)
        append_entry(entry)
    except Exception:
        log.exception("could not write audit entry")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
