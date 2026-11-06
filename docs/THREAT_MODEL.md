# Threat model (MVP)

## Assets and trust boundaries

1. **Local input tickets**: untrusted content, possibly sensitive if substituted for synthetic fixtures. Validated size and field types; never trusted as workflow instructions.
2. **Local KB articles**: untrusted prose that is searched and displayed, not directly passed to the AI prompt. Article IDs are validated.
3. **Deterministic evidence engine**: uses known phrase rules, retrieval rankings and duplicate scores to generate draft recommendations.
4. **Optional Ollama**: independent local process contacted only on loopback port 11434. Text outputs are not trusted. The engine never executes model output.
5. **Exported files**: can leak user-supplied ticket identifiers, subjects and notes if shared improperly. Operator must control retention and permissions.

## Risks / mitigations

| Threat | MVP mitigation | Residual risk |
| --- | --- | --- |
| Malicious HTML in ticket | `html.escape` and restrictive report CSP | Consumer browser/Streamlit configuration still matters |
| Spreadsheet formula in ticket | Prefix dangerous CSV cell values with apostrophe | Some spreadsheet import workflows may normalize cells differently |
| Malformed or oversized ticket file | Strict schema, ISO timezone, file/row/field limits | No antivirus or DLP; don't import corporate files |
| Prompt injection in ticket description | No raw ticket text is passed to LLM; code-controlled prompt metadata | AI output may still hallucinate or be misleading |
| SSRF or cloud AI leakage | Numerically verified loopback IP + fixed port/path, redirects/proxy disabled | Local Ollama process itself must be trusted and configured safely |
| Unapproved IAM actions | No write connectors; explicit manual approval guidance | Analyst may still follow a bad recommendation |
| False positive duplicate/priority | Heuristic scores explained, manual review | Not calibrated on production labels |
| Data retention | No server-side database, local report output only | User controls local artifacts and Streamlit memory lifecycle |

## Validation / audit guidance

- Never use genuine enterprise credentials or employee PII in public demo data.
- Review code and dependencies before evaluating against permitted real data.
- Evaluate category and KB accuracy on an approved, labeled dataset.
- Configure storage/retention, RBAC, monitoring and incident response prior to any enterprise deployment.
