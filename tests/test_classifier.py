import unittest
from iam_ticket_copilot.classifier import ASSIGNMENTS, PLAYBOOKS, classify, prioritize
from iam_ticket_copilot.models import Ticket


def ticket(text, title="IAM ticket"):
    return Ticket("INC123", "servicenow", title, text, "2026-11-01T00:00:00+00:00")


class ClassifierTests(unittest.TestCase):
    def test_provisioning(self):
        category, strength, signals = classify(ticket("NetIQ driver stopped and provisioning failed"))
        self.assertEqual(category, "Provisioning Failure")
        self.assertEqual(strength, "strong")
        self.assertIn("provisioning failed", signals)

    def test_mixed_grant_revoke_forces_review(self):
        self.assertEqual(classify(ticket("Request access to A and revoke access to B"))[0], "Needs Analyst Review")

    def test_whole_word_matching(self):
        self.assertEqual(classify(ticket("How to download the client"))[0], "Needs Analyst Review")

    def test_offboarding(self):
        self.assertEqual(classify(ticket("Terminated employee requires offboarding"))[0], "Offboarding")

    def test_lockout(self):
        self.assertEqual(classify(ticket("Account locked for user"))[0], "Account Lockout")

    def test_mfa(self):
        self.assertEqual(classify(ticket("MFA app authenticator not working"))[0], "MFA Support")

    def test_mover(self):
        self.assertEqual(classify(ticket("Department transfer and role mapping missing"))[0], "Mover / Role Change")

    def test_request(self):
        self.assertEqual(classify(ticket("Request access to application"))[0], "Access Request")

    def test_license(self):
        self.assertEqual(classify(ticket("Jira license seat unavailable"))[0], "License / Entitlement")

    def test_unknown(self):
        self.assertEqual(classify(ticket("We need help with something"))[0], "Needs Analyst Review")

    def test_default_priority(self):
        self.assertEqual(prioritize(ticket("Account locked"), "Account Lockout")[0], "P3")

    def test_critical_priority(self):
        self.assertEqual(prioritize(ticket("Executive MFA recovery"), "MFA Support")[0], "P2")

    def test_large_outage(self):
        self.assertEqual(prioritize(ticket("Company-wide provisioning outage"), "Provisioning Failure")[0], "P1")

    def test_no_priority_escalation_for_download(self):
        self.assertEqual(prioritize(ticket("All employees need to download a PDF"), "Access Request")[0], "P3")

    def test_all_categories_have_playbook_and_route(self):
        for key in ASSIGNMENTS:
            self.assertIn(key, PLAYBOOKS)
            self.assertGreater(len(PLAYBOOKS[key]), 0)
