import json
import tempfile
import unittest
from pathlib import Path

from iam_ticket_copilot.ingest import InputError, load_articles, load_tickets

ROOT = Path(__file__).resolve().parents[1]


class IngestTests(unittest.TestCase):
    def test_load_json(self):
        self.assertEqual(len(load_tickets(ROOT / "samples/synthetic_tickets.json")), 18)

    def test_load_csv(self):
        self.assertEqual(len(load_tickets(ROOT / "samples/synthetic_tickets.csv")), 18)

    def test_load_articles(self):
        self.assertEqual(len(load_articles(ROOT / "samples/kb/iam_playbooks.json")), 9)

    def _write(self, rows, suffix=".json"):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / ("tickets" + suffix)
        path.write_text(json.dumps(rows), encoding="utf-8")
        return path

    def test_duplicate_ids_rejected(self):
        row = load_tickets(ROOT / "samples/synthetic_tickets.json")[0]
        data = [{"ticket_id": row.ticket_id, "source": row.source,
                 "subject": row.subject, "description": row.description,
                 "created_at": row.created_at}]
        with self.assertRaises(InputError):
            load_tickets(self._write(data + data))

    def test_timezone_required(self):
        row = json.loads((ROOT / "samples/synthetic_tickets.json").read_text())[0]
        row["created_at"] = "2026-11-02T08:44:00"
        with self.assertRaises(InputError):
            load_tickets(self._write([row]))

    def test_numeric_description_rejected(self):
        row = json.loads((ROOT / "samples/synthetic_tickets.json").read_text())[0]
        row["description"] = 321
        with self.assertRaises(InputError):
            load_tickets(self._write([row]))

    def test_unexpected_source_rejected(self):
        row = json.loads((ROOT / "samples/synthetic_tickets.json").read_text())[0]
        row["source"] = "external_url"
        with self.assertRaises(InputError):
            load_tickets(self._write([row]))

    def test_unsafe_ticket_id_rejected(self):
        row = json.loads((ROOT / "samples/synthetic_tickets.json").read_text())[0]
        row["ticket_id"] = "../../etc/passwd"
        with self.assertRaises(InputError):
            load_tickets(self._write([row]))

    def test_oversized_description_rejected(self):
        row = json.loads((ROOT / "samples/synthetic_tickets.json").read_text())[0]
        row["description"] = "x" * 4001
        with self.assertRaises(InputError):
            load_tickets(self._write([row]))

    def test_non_list_rejected(self):
        with self.assertRaises(InputError):
            load_tickets(self._write({"tickets": []}))

    def test_unknown_extension_rejected(self):
        with self.assertRaises(InputError):
            load_tickets(self._write([], suffix=".txt"))

    def test_empty_kb_rejected(self):
        with self.assertRaises(InputError):
            load_articles(self._write([]))
