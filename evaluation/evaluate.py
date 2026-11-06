"""Reproducible triage evaluation with synthetic reference and challenge cases."""
from __future__ import annotations

import json
from pathlib import Path

from iam_ticket_copilot.ingest import load_articles, load_tickets
from iam_ticket_copilot.pipeline import triage_tickets

ROOT = Path(__file__).resolve().parents[1]


def score(reference: dict, predictions: list, *, with_kb: bool) -> dict:
    by_id = {p.ticket_id: p for p in predictions}
    categories = [(ident, expected[0], by_id[ident].category)
                  for ident, expected in reference.items()]
    priorities = [(ident, expected[1], by_id[ident].priority)
                  for ident, expected in reference.items()]
    output = {
        "n": len(reference),
        "category_correct": sum(expected == actual for _, expected, actual in categories),
        "priority_correct": sum(expected == actual for _, expected, actual in priorities),
        "category_errors": [{"id": ident, "expected": exp, "actual": act}
                            for ident, exp, act in categories if exp != act],
        "priority_errors": [{"id": ident, "expected": exp, "actual": act}
                            for ident, exp, act in priorities if exp != act],
    }
    if with_kb:
        output["kb_recall_at_1"] = sum(
            bool(by_id[ident].citations) and by_id[ident].citations[0].article_id == expected[2]
            for ident, expected in reference.items()
        )
    return output


def main() -> int:
    truth = json.loads((ROOT / "evaluation/ground_truth.json").read_text(encoding="utf-8"))
    articles = load_articles(ROOT / "samples/kb/iam_playbooks.json")
    demo = triage_tickets(load_tickets(ROOT / "samples/synthetic_tickets.json"), articles)
    challenge = triage_tickets(load_tickets(ROOT / "evaluation/challenge_tickets.json"), articles)
    expected_pairs = {tuple(sorted(pair)) for pair in truth["expected_duplicate_pairs"]}
    found_pairs = {tuple(sorted((r.ticket_id, item["ticket_id"])))
                   for r in demo for item in r.possible_duplicates}
    output = {
        "label": "Small hand-labeled synthetic scenarios; NOT production accuracy",
        "demo": score(truth["core"], demo, with_kb=True),
        "challenge": score(truth["challenge"], challenge, with_kb=False),
        "duplicate_pairs_expected": len(expected_pairs),
        "duplicate_pairs_found": len(found_pairs),
        "duplicate_pairs_matched": len(expected_pairs & found_pairs),
        "unexpected_duplicate_pairs": sorted(found_pairs - expected_pairs),
        "missed_duplicate_pairs": sorted(expected_pairs - found_pairs),
        "limitations": "Curated, small synthetic test sets; not independent enterprise ground truth. LLM is not scored."
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not output["demo"]["category_errors"] and not output["demo"]["priority_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
