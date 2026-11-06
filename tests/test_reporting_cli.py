import csv
import json
import tempfile
import unittest
from pathlib import Path
from iam_ticket_copilot.cli import main
from iam_ticket_copilot.ingest import load_articles, load_tickets
from iam_ticket_copilot.models import Triage
from iam_ticket_copilot.pipeline import stats, triage_tickets
from iam_ticket_copilot.reporting import _safe_csv, render_html, save_reports

ROOT = Path(__file__).resolve().parents[1]


class ReportingAndCLITests(unittest.TestCase):
    def setUp(self):
        tickets = load_tickets(ROOT / "samples/synthetic_tickets.json")
        articles = load_articles(ROOT / "samples/kb/iam_playbooks.json")
        self.results = triage_tickets(tickets, articles)

    def test_all_records_returned(self):
        self.assertEqual(len(self.results), 18)

    def test_stats_total(self):
        s = stats(self.results)
        self.assertEqual(sum(s["category_counts"].values()), 18)
        self.assertEqual(s["tickets_processed"], 18)

    def test_priorities_are_advisory(self):
        priorities = {r.ticket_id: r.priority for r in self.results}
        self.assertEqual(priorities["INC1016"], "P1")
        self.assertEqual(priorities["INC1017"], "P2")

    def test_responds_to_unknown(self):
        self.assertEqual(next(r for r in self.results if r.ticket_id == "INC1015").category, "Needs Analyst Review")

    def test_html_escapes_subject(self):
        r = self.results[0]
        r.subject = '<img src=x onerror="alert(1)">'
        html = render_html([r], generated="2026-11-06")
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;img', html)

    def test_html_has_search_and_category_filters(self):
        html = render_html(self.results, generated="2026-11-06")
        self.assertIn('id="search"', html)
        self.assertIn('id="category"', html)
        self.assertIn('KB-IAM-', html)

    def test_spreadsheet_injection_prefix(self):
        for v in ('=HYPERLINK("evil")', '+SUM(1,1)', ' -1+1', '@NOW()'):
            self.assertTrue(_safe_csv(v).startswith("'"))
        self.assertEqual(_safe_csv("Normal text"), "Normal text")

    def test_export_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            paths = save_reports(self.results, td, clock="2026-11-06T12:00:00Z")
            self.assertEqual(set(paths), {"json", "csv", "html"})
            self.assertTrue(all(path.is_file() for path in paths.values()))
            payload = json.loads(paths["json"].read_text())
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(len(payload["tickets"]), 18)
            with paths["csv"].open(newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 18)

    def test_cli_success(self):
        with tempfile.TemporaryDirectory() as td:
            rc = main(["--tickets", str(ROOT / "samples/synthetic_tickets.csv"),
                       "--kb", str(ROOT / "samples/kb/iam_playbooks.json"),
                       "--output", td])
            self.assertEqual(rc, 0)
            self.assertTrue((Path(td) / "index.html").exists())

    def test_cli_invalid_data(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text('{"not":"a list"}')
            rc = main(["--tickets", str(bad),
                       "--kb", str(ROOT / "samples/kb/iam_playbooks.json"),
                       "--output", td])
            self.assertEqual(rc, 2)

    def test_cli_invalid_endpoint(self):
        with tempfile.TemporaryDirectory() as td:
            rc = main(["--tickets", str(ROOT / "samples/synthetic_tickets.json"),
                       "--kb", str(ROOT / "samples/kb/iam_playbooks.json"),
                       "--output", td, "--ollama", "--endpoint", "http://8.8.8.8:11434"])
            self.assertEqual(rc, 2)
