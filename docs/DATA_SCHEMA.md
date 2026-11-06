# Normalized data schemas

All data in the repository is synthetic. CSV input uses the same ticket column names as the JSON keys. The tool does not directly ingest arbitrary ServiceNow/Jira API payloads.

## Ticket fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `ticket_id` | string | Yes | 2–50 safe alphanumeric, dot, dash or underscore characters; unique |
| `source` | string | Yes | `servicenow` or `jira` |
| `subject` | string | Yes | 1–180 characters |
| `description` | string | Yes | 1–4,000 characters |
| `created_at` | ISO 8601 string | Yes | Explicit timezone, e.g., `2026-11-02T08:44:00Z` |
| `state` | string | No | E.g., `new` or `open`; defaults to `new` |

Example:

```json
{
  "ticket_id": "INC1001",
  "source": "servicenow",
  "subject": "Provisioning failed for new hire",
  "description": "NetIQ driver stopped, no account created.",
  "created_at": "2026-11-02T08:44:00Z",
  "state": "new"
}
```

## Knowledge-base fields

A KB JSON file contains a list of objects with these required strings:

- `article_id` — unique, validated safe ID; maximum 50 characters
- `title` — article title; maximum 180 characters
- `category` — routing category; maximum 80 characters
- `body` — SOP body; maximum 3,000 characters

## Outputs

- `triage.json` — schema version, generation timestamp, summary counts and full ticket recommendation objects (includes subject and IDs)
- `triage.csv` — spreadsheet-friendly one-row-per-ticket summary with formula sanitization
- `index.html` — interactive static report with client-side search and filters; does not call APIs or load remote resources

Ticket source strings, group assignments and priority hints are only examples. Customize them to organizational procedures before any supervised pilot.
