"""Command line runner for the offline IAM ticket triage demo."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .ingest import InputError, load_articles, load_tickets
from .narrative import LocalAIError, validate_local_endpoint
from .pipeline import stats, triage_tickets
from .reporting import save_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only IAM ticket triage with local playbook retrieval")
    parser.add_argument("--tickets", required=True, help="Normalized ServiceNow/Jira JSON or CSV")
    parser.add_argument("--kb", required=True, help="Local KB articles JSON")
    parser.add_argument("--output", default="out", help="Folder for HTML, JSON and CSV reports")
    parser.add_argument("--ollama", action="store_true", help="Opt in to local AI explanations")
    parser.add_argument("--model", default="llama3.2:3b", help="Installed Ollama model name")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434", help="Numeric loopback Ollama base URL")
    args = parser.parse_args(argv)
    try:
        tickets = load_tickets(args.tickets)
        articles = load_articles(args.kb)
        if args.ollama:
            validate_local_endpoint(args.endpoint)
        results = triage_tickets(tickets, articles, use_ollama=args.ollama,
                                 model=args.model, endpoint=args.endpoint)
        paths = save_reports(results, Path(args.output))
    except (InputError, OSError, ValueError, LocalAIError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    counts = stats(results)
    print(f"Triage complete: {counts['tickets_processed']} tickets, "
          f"{counts['possible_duplicate_pairs']} potential duplicate pairs, "
          f"{counts['needs_analyst_review']} analyst-review cases")
    for name, path in paths.items():
        print(f"  {name.upper()}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
