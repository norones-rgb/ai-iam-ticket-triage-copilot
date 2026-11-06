# Evaluation: familiar cases vs. lexical challenge

Run from the repository root:

```bash
python -m evaluation.evaluate
```

The script scores the deterministic rules and KB retriever with **explicit hand-written scenario labels**; it does not test an LLM.

| Metric | Original demo (18) | Challenge set (12) |
| --- | ---: | ---: |
| Correct category recommendations | **18 / 18** | **7 / 12** |
| Correct priority recommendations | **18 / 18** | **11 / 12** |
| Expected KB article ranked first | **18 / 18** | Not assessed |
| Expected candidate duplicate pair | **1 / 1** | Not assessed |

**Challenge error analysis (do not obscure these):** Five differently phrased category examples were missed or routed to the wrong category: CH001 (lockout paraphrase), CH002 and CH011 (access without rule keywords), CH004 (offboarding paraphrase), and CH010 (negated “account lockout” phrase). CH009 was incorrectly raised to P1 because the phrase “no confirmed service outage” was interpreted as an outage in conjunction with “company-wide.” This illustrates a missing **negation/context layer**.

These numbers describe only **small, curated synthetic data**, not real-world classification accuracy, model quality, or service-level priority compliance. The demo labels were written to match known scenarios; the challenge labels are deliberately adversarial. No analyst inter-rater agreement, representative sampling, statistical uncertainty, or deployment validation has been performed.

The right engineering next steps are to add context-aware negation handling, expand the approved vocabulary with holdout testing, evaluate manual-review thresholds, create a larger blind-labeled set, and measure retrieval relevance separately.

**Reproducibility:** All data and labels live in `evaluation/`; the script prints every missed case and leaves any challenge failures visible instead of masking them behind an overall score.
