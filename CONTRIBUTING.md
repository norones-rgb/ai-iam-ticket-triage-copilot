# Contributing

Thank you for contributing to the IAM Ticket Triage Copilot.

1. Use Python 3.10+ and keep the core engine standard-library only.
2. Use **synthetic-only** test cases and fixtures. Never commit user accounts, credentials, company tickets or internal knowledge articles.
3. Include tests for each category, retrieval behavior, output encoding and failures.
4. Run `python -m unittest discover -s tests -v` before submitting changes.
5. Keep all ticket routing, priority and remediation steps advisory. No write APIs, autonomous approvals or access changes.
6. If changing the Ollama interface, maintain the strict loopback-only restriction and absence of raw ticket information in model prompts.
7. Describe the limitations, potential false positives and manual review steps in the PR.

Contributions that add real company logos/records, secret material, prompt exfiltration or unapproved access changes will not be accepted.
