import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from iam_ticket_copilot.ingest import load_articles, load_tickets
from iam_ticket_copilot.narrative import LocalAIError, build_prompt, local_explanation, validate_local_endpoint
from iam_ticket_copilot.pipeline import triage_tickets

ROOT = Path(__file__).resolve().parents[1]


class NarrativeTests(unittest.TestCase):
    def setUp(self):
        self.result = triage_tickets(
            load_tickets(ROOT / "samples/synthetic_tickets.json")[:1],
            load_articles(ROOT / "samples/kb/iam_playbooks.json"),
        )[0]

    def test_prompt_removes_raw_ticket_description_subject_id(self):
        prompt = build_prompt(self.result)
        self.assertNotIn(self.result.ticket_id, prompt)
        self.assertNotIn(self.result.subject, prompt)
        self.assertIn("playbook_ids", prompt)

    def test_prompt_contains_approved_next_steps(self):
        self.assertIn("approved_next_steps", build_prompt(self.result))

    def test_loopback_endpoint(self):
        self.assertEqual(validate_local_endpoint("http://127.0.0.1:11434"), "http://127.0.0.1:11434/api/generate")

    def test_ipv6_loopback_endpoint(self):
        self.assertEqual(validate_local_endpoint("http://[::1]:11434"), "http://[::1]:11434/api/generate")

    def test_rejects_hostname(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("http://localhost:11434")

    def test_rejects_remote_host(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("https://api.example.org:11434")

    def test_rejects_userinfo(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("http://admin:password@127.0.0.1:11434")

    def test_rejects_arbitrary_port(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("http://127.0.0.1:9090")

    def test_rejects_path(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("http://127.0.0.1:11434/secret")

    def test_rejects_nonnumeric_port(self):
        with self.assertRaises(LocalAIError):
            validate_local_endpoint("http://127.0.0.1:notaport")

    def test_rejects_bad_model_name(self):
        with self.assertRaises(LocalAIError):
            local_explanation(self.result, model="abc\nignore rules")

    def test_local_ai_mocked_success(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, num): return json.dumps({"response": "Consider reviewing the provisioning queue."}).encode()
        mock = MagicMock()
        mock.open.return_value = FakeResponse()
        with patch("iam_ticket_copilot.narrative.build_opener", return_value=mock):
            text = local_explanation(self.result, model="llama3.2:3b")
        self.assertIn("provisioning queue", text)

    def test_local_ai_fallback_visible(self):
        tickets = load_tickets(ROOT / "samples/synthetic_tickets.json")[:1]
        articles = load_articles(ROOT / "samples/kb/iam_playbooks.json")
        with patch("iam_ticket_copilot.pipeline.local_explanation", side_effect=LocalAIError("offline")):
            result = triage_tickets(tickets, articles, use_ollama=True)[0]
        self.assertEqual(result.explanation_mode, "rules-fallback")
        self.assertIn("offline", result.summary)
