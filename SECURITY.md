# Security policy

## Intended deployment

This is an **offline, synthetic-data portfolio demonstration**. It is not approved for production IAM operations, corporate support records, privileged actions or regulated personal data.

The tool is read-only relative to any external system and **has no ServiceNow, Jira, Entra ID, Active Directory, Okta, SailPoint, NetIQ, or corporate authentication connector**. It writes only explicitly requested local report files or temporary files for the optional Streamlit demo. It does not grant, revoke, reset or approve anything.

## Data handling

- Input is normalized local ticket JSON/CSV and local KB JSON, not live API traffic.
- Input file size limit: 3 MB. Ticket limit: 1,000; KB article limit: 250. Field lengths and IDs are validated.
- Reports preserve ticket subjects and IDs: treat generated HTML/JSON/CSV as potentially sensitive if using your own data. Avoid real employee/customer data unless explicitly authorized.
- HTML fields are escaped; CSV cells with dangerous leading spreadsheet formula prefixes are neutralized.
- No telemetry, tracking, embedded scripts from CDNs, external images, cookies or external analytics.
- Duplicate detection does not merge tickets or claim that similarity is identity.

## Local AI design

AI is disabled by default. When opted in, a local model is contacted only via `http://127.0.0.1:11434` or `http://[::1]:11434` through a fixed `/api/generate` path. Hostnames, remote hosts, userinfo, redirects and proxy forwarding are disallowed. This reduces accidental forwarding to external APIs but does not constitute formal sandboxing of an untrusted local model.

Prompt construction excludes the original ticket subject and description, requester identity and ticket IDs; it includes only code-controlled classification signals, category, priority suggestion, approved next steps and strictly validated KB article IDs. Model outputs are untrusted; they are not evidence or permission to act. The generated summary may contain errors and should be checked against the cited SOP and original ticket.

## Known limitations

- No authentication, authorization, encryption-at-rest, data residency or enterprise retention policy for user-provided records.
- Rules can misclassify unusual language. Priority suggestions are not authoritative SLA calculations.
- KB retrieval ranking scores are heuristics, not confidence or correctness probabilities.
- Lexical duplicate similarity is not a semantic equivalence or identity guarantee.
- Streamlit upload processes bytes in memory and temporary files for demo use only.
- HTML output contains inline CSS and a small filtering script protected by a restrictive HTML CSP with inline allowances; this is not an enterprise web-app security boundary.
- No external system write actions exist, but report files can be stored in a location chosen by the local operator.

## Reporting a vulnerability

Please report security issues privately via GitHub's private vulnerability reporting feature, if enabled, rather than creating a public issue containing exploit details or sensitive records.
