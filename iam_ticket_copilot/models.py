"""Small typed data structures for a deterministic and auditable pipeline."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    source: str
    subject: str
    description: str
    created_at: str
    state: str = "new"


@dataclass(frozen=True)
class Article:
    article_id: str
    title: str
    category: str
    body: str


@dataclass(frozen=True)
class Citation:
    article_id: str
    title: str
    snippet: str
    retrieval_score: float


@dataclass
class Triage:
    ticket_id: str
    source: str
    subject: str
    category: str
    match_strength: str
    evidence_signals: list[str]
    priority: str
    priority_reasons: list[str]
    assignment_group: str
    summary: str
    next_steps: list[str]
    citations: list[Citation] = field(default_factory=list)
    possible_duplicates: list[dict[str, Any]] = field(default_factory=list)
    explanation_mode: str = "rules"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
