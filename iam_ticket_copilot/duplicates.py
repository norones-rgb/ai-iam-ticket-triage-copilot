"""Potential duplicate identification using traceable lexical overlap."""
from __future__ import annotations

from collections import defaultdict
from .models import Ticket
from .retrieval import tokenize


def _shingles(ticket: Ticket) -> set[str]:
    # Set similarity is useful for a transparent MVP; semantics and negation
    # must be reviewed by a person. Use title AND short description.
    return set(tokenize(f"{ticket.subject} {ticket.description}"))


def possible_duplicates(tickets: list[Ticket], categories: dict[str, str], *, threshold: float = 0.48) -> dict[str, list[dict]]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    result: dict[str, list[dict]] = defaultdict(list)
    tokens = [_shingles(ticket) for ticket in tickets]
    for i, left in enumerate(tickets):
        for j in range(i + 1, len(tickets)):
            right = tickets[j]
            if categories[left.ticket_id] != categories[right.ticket_id] or categories[left.ticket_id] == "Needs Analyst Review":
                continue
            # Require enough content to avoid false positives on generic tickets.
            if min(len(tokens[i]), len(tokens[j])) < 5:
                continue
            union = tokens[i] | tokens[j]
            score = len(tokens[i] & tokens[j]) / len(union) if union else 0.0
            if score >= threshold:
                result[left.ticket_id].append({"ticket_id": right.ticket_id, "similarity": round(score, 3)})
                result[right.ticket_id].append({"ticket_id": left.ticket_id, "similarity": round(score, 3)})
    for values in result.values():
        values.sort(key=lambda row: (-row["similarity"], row["ticket_id"]))
    return dict(result)
