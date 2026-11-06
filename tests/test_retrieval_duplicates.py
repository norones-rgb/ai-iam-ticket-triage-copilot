import unittest
from pathlib import Path
from iam_ticket_copilot.duplicates import possible_duplicates
from iam_ticket_copilot.ingest import load_articles, load_tickets
from iam_ticket_copilot.models import Ticket
from iam_ticket_copilot.retrieval import retrieve, tokenize
from iam_ticket_copilot.classifier import classify

ROOT = Path(__file__).resolve().parents[1]


class RetrievalAndDuplicatesTests(unittest.TestCase):
    def setUp(self):
        self.tickets = load_tickets(ROOT / "samples/synthetic_tickets.json")
        self.articles = load_articles(ROOT / "samples/kb/iam_playbooks.json")

    def test_retrieves_expected_playbook(self):
        matches = retrieve("authenticator push notification MFA", "MFA Support", self.articles)
        self.assertEqual(matches[0].article_id, "KB-IAM-004")

    def test_kb_citations_include_excerpt(self):
        matches = retrieve("provisioning failed", "Provisioning Failure", self.articles)
        self.assertTrue(matches[0].snippet)
        self.assertGreater(matches[0].retrieval_score, 0)

    def test_empty_kb(self):
        self.assertEqual(retrieve("anything", "unknown", []), [])

    def test_invalid_top_k(self):
        self.assertEqual(retrieve("anything", "unknown", self.articles, top_k=0), [])

    def test_case_insensitive_tokens(self):
        self.assertEqual(tokenize("MFA authenticator"), tokenize("mfa AUTHENTICATOR"))

    def test_duplicate_pair(self):
        cats = {t.ticket_id: classify(t)[0] for t in self.tickets}
        found = possible_duplicates(self.tickets, cats, threshold=0.3)
        self.assertIn("INC1002", [d["ticket_id"] for d in found["INC1001"]])

    def test_symmetric_duplicate_pair(self):
        cats = {t.ticket_id: classify(t)[0] for t in self.tickets}
        found = possible_duplicates(self.tickets, cats, threshold=0.3)
        self.assertIn("INC1001", [d["ticket_id"] for d in found["INC1002"]])

    def test_different_categories_not_duplicates(self):
        cats = {t.ticket_id: classify(t)[0] for t in self.tickets}
        found = possible_duplicates(self.tickets, cats, threshold=0.25)
        self.assertNotIn("INC1003", [d["ticket_id"] for d in found.get("INC1001", [])])

    def test_empty_list(self):
        self.assertEqual(possible_duplicates([], {}), {})

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            possible_duplicates([], {}, threshold=1.5)

    def test_short_tickets_not_duplicate(self):
        t1 = Ticket("INC1", "jira", "MFA", "MFA", "2026-11-01T00:00:00Z")
        t2 = Ticket("INC2", "jira", "MFA", "MFA", "2026-11-01T00:00:00Z")
        self.assertEqual(possible_duplicates([t1, t2], {"INC1": "MFA Support", "INC2": "MFA Support"}), {})
