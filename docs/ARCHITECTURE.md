# Architecture and evaluation strategy

## Components

- `ingest.py`: normalize and validate files, IDs, timezones and sizes.
- `classifier.py`: fixed weighted signals for seven IAM categories. Mixed signals and unknown cases are downgraded to manual review rather than being presented as high-confidence classifications.
- `duplicates.py`: candidate pairs using token-set Jaccard similarity. A threshold of 0.48 is a discovery heuristic only, not a machine-learned classifier.
- `retrieval.py`: BM25-style local lexical retrieval using token frequency and document frequency. The category match contributes a transparent boost. The result includes KB article ID, title, snippet and score. No API or embedding model is required.
- `narrative.py`: opt-in local Ollama explanation generator. A code-controlled metadata-only prompt deliberately omits raw ticket subject and description, KB body and ticket ID. Explanations are untrusted, optional and do not drive assignments or actions.
- `pipeline.py`: assembles recommendation records; no calls to enterprise systems and no external system mutations.
- `reporting.py`: static offline HTML and CSV/JSON, including output encoding mitigations.
- `app.py`: optional Streamlit front end with local file upload/download for demonstration.

## Priority examples (heuristic only)

- **P1 suggestion**: explicit broad impact phrase (e.g., "company-wide") AND outage/failure term.
- **P2 suggestion**: potential critical, executive, production or multi-user impact.
- **P3 suggestion**: default; human must assess urgency and policy.

These do **not** represent true business criticality, live SLA, incident declaration or severity confidence.

## Evaluation

The test suite checks correct routing on hand-written synthetic examples and controls against malformed files, HTML injection, spreadsheet formula injection and unsafe local-model URLs. This is an MVP demonstration, **not** a benchmark of precision, recall, semantic accuracy or LLM grounding. A production-grade evaluation must include a representative, approved, labeled dataset and error analysis.

Suggested evaluation metrics:

- Category macro-F1 and confusion matrix against analyst-reviewed ground truth
- False-positive rate and review-queue rate
- Duplicate pair precision at multiple thresholds and difficult near-duplicate cases
- KB recall@3 / MRR with human-labeled relevance
- Priority escalation accuracy under organization-specific policy
- AI explanation factuality and citation attribution under adversarial prompts
- Latency and cost for local-only versus paid-model variants

## Non-goals

- No production connectors or sign-in.
- No auto-resolution, ticket close, ticket edit, entitlement modify or approval bypass.
- No ML training, semantic embeddings or statistical confidence claims in v0.1.0.
