"""Defensive parsing for normalized, strictly read-only synthetic tickets and KB articles."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

from .models import Article, Ticket

MAX_FILE_BYTES = 3_000_000
MAX_TICKETS = 1_000
MAX_ARTICLES = 250
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,49}$")
ALLOWED_SOURCES = {"servicenow", "jira"}


class InputError(ValueError):
    """Input is malformed or outside documented demo limits."""


def _get_file(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
        raise InputError(f"Input must be a file of at most {MAX_FILE_BYTES} bytes")
    return p


def _text(row: dict, key: str, maximum: int, *, required: bool = True) -> str:
    value = row.get(key, "")
    if not isinstance(value, str):
        raise InputError(f"{key} must be a string")
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        raise InputError(f"Invalid {key}: required={required}, maximum length={maximum}")
    return value


def _date(value: str) -> str:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            raise ValueError("Timezone required")
        return parsed.isoformat()
    except ValueError as exc:
        raise InputError("created_at must be ISO 8601 with a timezone") from exc


def load_tickets(path: str | Path) -> list[Ticket]:
    p = _get_file(path)
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif p.suffix.lower() == ".json":
        try:
            rows = json.loads(p.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise InputError("Ticket JSON is invalid") from exc
    else:
        raise InputError("Ticket files must be .csv or .json")
    if not isinstance(rows, list) or len(rows) > MAX_TICKETS:
        raise InputError(f"Expected a list of up to {MAX_TICKETS} tickets")
    result: list[Ticket] = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise InputError("Each ticket must be an object")
        ident = _text(row, "ticket_id", 50)
        if not ID_RE.fullmatch(ident) or ident in seen:
            raise InputError("Ticket IDs must be unique and contain safe characters")
        seen.add(ident)
        source = _text(row, "source", 30).lower()
        if source not in ALLOWED_SOURCES:
            raise InputError("source must be servicenow or jira")
        result.append(Ticket(
            ticket_id=ident, source=source,
            subject=_text(row, "subject", 180),
            description=_text(row, "description", 4000),
            created_at=_date(_text(row, "created_at", 40)),
            state=_text(row, "state", 60, required=False) or "new",
        ))
    return result


def load_articles(path: str | Path) -> list[Article]:
    p = _get_file(path)
    try:
        rows = json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InputError("Knowledge-base JSON is invalid") from exc
    if not isinstance(rows, list) or not rows or len(rows) > MAX_ARTICLES:
        raise InputError("Expected a nonempty list of knowledge-base articles")
    result: list[Article] = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise InputError("Each article must be an object")
        ident = _text(row, "article_id", 50)
        if not ID_RE.fullmatch(ident) or ident in seen:
            raise InputError("Knowledge-base IDs must be unique and contain safe characters")
        seen.add(ident)
        result.append(Article(
            article_id=ident, title=_text(row, "title", 180),
            category=_text(row, "category", 80), body=_text(row, "body", 3000),
        ))
    return result
