"""Orchestrate triage without mutating tickets or calling ticketing APIs."""
from __future__ import annotations

from collections import Counter

from .classifier import ASSIGNMENTS, PLAYBOOKS, classify, prioritize
from .duplicates import possible_duplicates
from .models import Article, Ticket, Triage
from .narrative import LocalAIError, local_explanation
from .retrieval import retrieve


def triage_tickets(
    tickets: list[Ticket], articles: list[Article], *,
    use_ollama: bool = False, model: str = "llama3.2:3b",
    endpoint: str = "http://127.0.0.1:11434",
) -> list[Triage]:
    categories = {ticket.ticket_id: classify(ticket)[0] for ticket in tickets}
    duplicates = possible_duplicates(tickets, categories)
    results: list[Triage] = []
    for ticket in tickets:
        category, strength, signals = classify(ticket)
        priority, reasons = prioritize(ticket, category)
        citations = retrieve(f"{ticket.subject} {ticket.description} {category}", category, articles)
        result = Triage(
            ticket_id=ticket.ticket_id, source=ticket.source, subject=ticket.subject,
            category=category, match_strength=strength, evidence_signals=signals,
            priority=priority, priority_reasons=reasons,
            assignment_group=ASSIGNMENTS[category],
            summary=(f"Suggested {category.lower()} triage based on matched text signals. "
                     "Verify ticket context, identity and impact before acting."),
            next_steps=list(PLAYBOOKS[category]),
            citations=citations,
            possible_duplicates=duplicates.get(ticket.ticket_id, []),
        )
        if use_ollama:
            try:
                result.summary = local_explanation(result, model=model, endpoint=endpoint)
                result.explanation_mode = "ollama-local"
            except LocalAIError as exc:
                # Clear degraded-mode note; never pretend the AI was available.
                result.summary += f" Local AI skipped: {str(exc)[:140]}"
                result.explanation_mode = "rules-fallback"
        results.append(result)
    return results


def stats(results: list[Triage]) -> dict:
    return {
        "tickets_processed": len(results),
        "category_counts": dict(sorted(Counter(r.category for r in results).items())),
        "priority_counts": dict(sorted(Counter(r.priority for r in results).items())),
        "possible_duplicate_pairs": sum(len(r.possible_duplicates) for r in results) // 2,
        "needs_analyst_review": sum(r.category == "Needs Analyst Review" for r in results),
        "local_ai_used": sum(r.explanation_mode == "ollama-local" for r in results),
    }
