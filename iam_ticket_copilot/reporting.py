"""Offline, portable triage exports with output escaping and CSV formula defenses."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

from .models import Triage
from .pipeline import stats


def _safe_csv(value: object) -> object:
    """Defend CSV consumers against cells interpreted as spreadsheet formulas."""
    if not isinstance(value, str):
        return value
    trimmed = value.lstrip(" \t\r\n")
    if trimmed.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def save_reports(results: list[Triage], folder: str | Path, *, clock: str | None = None) -> dict[str, Path]:
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    generated = clock or datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {"schema_version": "1.0", "generated_at": generated,
               "mode": "read-only advisory", "statistics": stats(results),
               "tickets": [r.to_dict() for r in results]}
    json_file = out / "triage.json"
    json_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_file = out / "triage.csv"
    with csv_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("ticket_id", "source", "subject", "category", "match_strength", "priority",
                         "assignment_group", "evidence_signals", "possible_duplicates", "kb_citations",
                         "summary", "explanation_mode"))
        for r in results:
            writer.writerow([_safe_csv(x) for x in (
                r.ticket_id, r.source, r.subject, r.category, r.match_strength, r.priority,
                r.assignment_group, "; ".join(r.evidence_signals),
                "; ".join(p["ticket_id"] for p in r.possible_duplicates),
                "; ".join(c.article_id for c in r.citations), r.summary, r.explanation_mode,
            )])
    html_file = out / "index.html"
    html_file.write_text(render_html(results, generated=generated), encoding="utf-8")
    return {"json": json_file, "csv": csv_file, "html": html_file}


def render_html(results: list[Triage], *, generated: str) -> str:
    s = stats(results)
    categories = s["category_counts"]
    count_max = max(categories.values(), default=1)
    esc = lambda value: escape(str(value), quote=True)
    bars = "".join(
        f'<div class="barrow"><div class="barlabel">{esc(label)}</div>'
        f'<div class="bartrack"><div class="barfill" style="width:{int(count/count_max*100)}%"></div></div>'
        f'<div class="barnum">{count}</div></div>'
        for label, count in sorted(categories.items(), key=lambda item: -item[1])
    )
    cards = []
    for r in results:
        signs = "".join(f"<span class='signal'>{esc(sig)}</span>" for sig in r.evidence_signals)
        steps = "".join(f"<li>{esc(step)}</li>" for step in r.next_steps)
        citations = "".join(
            f'<li><strong>{esc(c.article_id)}</strong> · {esc(c.title)}'
            f'<p>{esc(c.snippet)}</p></li>' for c in r.citations
        ) or "<li>No relevant playbook retrieved. Manual review required.</li>"
        duplicates = ", ".join(f"{esc(d['ticket_id'])} ({d['similarity']:.2f})" for d in r.possible_duplicates)
        dup_section = f'<p class="duplicates"><b>Possible duplicate:</b> {duplicates}</p>' if duplicates else ""
        card = f'''<article class="ticket" data-category="{esc(r.category)}" data-search="{esc(' '.join([r.ticket_id, r.subject, r.category, r.assignment_group]).lower())}">
          <div class="ticketheader"><div><span class="tag">{esc(r.source.upper())}</span><span class="ticketid">{esc(r.ticket_id)}</span></div>
          <span class="priority {esc(r.priority.lower())}">{esc(r.priority)}</span></div>
          <h3>{esc(r.subject)}</h3>
          <div class="classification"><div><small>AI-assisted routing suggestion</small><strong>{esc(r.category)}</strong></div>
          <div><small>Assignment group</small><strong>{esc(r.assignment_group)}</strong></div>
          <div><small>Signal strength</small><strong>{esc(r.match_strength)}</strong></div></div>
          <p class="summary">{esc(r.summary)}</p>
          <div class="signalrow">{signs if signs else '<span class="signal">No category signals matched</span>'}</div>
          {dup_section}
          <details><summary>Investigate · approved next steps</summary><ol>{steps}</ol></details>
          <details><summary>Evidence · playbook citations ({len(r.citations)})</summary><ul class="citations">{citations}</ul></details>
          <div class="foot">Read-only recommendation · {esc(r.explanation_mode)} · Human review required</div>
        </article>'''
        cards.append(card)
    options = ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in sorted(categories))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'none'; form-action 'none'; base-uri 'none'">
<title>IAM Ticket Triage Copilot · Evidence Dashboard</title>
<style>
:root{{--navy:#111b2c;--ink:#1c2c3b;--muted:#647486;--paper:#f4f5f3;--line:#e0e5e6;--accent:#bf7441;--teal:#1e6c6c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;line-height:1.5}}
header{{background:var(--navy);color:white;padding:46px max(24px,calc((100% - 1120px)/2)) 42px}}.eyebrow{{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#e0af88;font-weight:700}}h1{{font-size:clamp(30px,4vw,47px);line-height:1.08;letter-spacing:-1.5px;margin:12px 0}}header p{{color:#bfc9d5;max-width:690px}}.stamp{{font-size:12px;color:#bbc4cf}}
main{{max-width:1120px;margin:0 auto;padding:30px 24px 70px}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:-60px;position:relative}}.metric{{padding:22px;border-radius:12px;background:white;box-shadow:0 4px 16px #111b2c0b;border:1px solid #e9ebed}}.metric b{{font-size:31px;display:block;letter-spacing:-1px}}.metric span{{font-size:12px;color:var(--muted)}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}}.panel{{background:white;padding:24px;border-radius:12px;border:1px solid var(--line)}}h2{{font-size:20px;letter-spacing:-.4px;margin:0 0 8px}}.subtitle{{font-size:13px;color:var(--muted);margin:0 0 20px}}.barrow{{display:grid;grid-template-columns:155px 1fr 30px;align-items:center;gap:12px;margin:12px 0;font-size:12px}}.bartrack{{height:11px;background:#edf0f0;border-radius:12px;overflow:hidden}}.barfill{{height:100%;background:var(--teal);border-radius:12px}}.barnum{{text-align:right;font-weight:700}}.steps{{font-size:14px;color:#465766;padding-left:18px}}.steps li{{margin:8px 0}}.toolbar{{margin:30px 0 16px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;align-items:end}}.toolbar h2{{margin:0}}.filters{{display:flex;gap:8px;flex-wrap:wrap}}input,select{{font:inherit;padding:11px 13px;border:1px solid #d7dddf;border-radius:8px;background:white;color:var(--ink);min-width:175px}}input{{width:270px}}.tickets{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.ticket{{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;min-width:0}}.ticketheader{{display:flex;align-items:center;justify-content:space-between;gap:10px}}.tag{{background:#edf2f3;color:#36515d;padding:4px 8px;font-size:10px;letter-spacing:.7px;border-radius:5px;font-weight:800}}.ticketid{{font-size:12px;font-weight:750;margin-left:10px}}.priority{{font-size:12px;font-weight:750;background:#e9eef1;padding:5px 10px;border-radius:20px}}.p1{{background:#fde5df;color:#a33422}}.p2{{background:#fff0dd;color:#a05e12}}.p3{{background:#e7eee9;color:#31724b}}h3{{font-size:18px;line-height:1.4;margin:14px 0 17px}}.classification{{display:grid;grid-template-columns:1.2fr 1.2fr .7fr;gap:10px;border-top:1px solid var(--line);padding-top:13px}}small{{font-size:10px;color:var(--muted);display:block}}.classification strong{{font-size:12px;display:block;margin-top:4px}}.summary{{font-size:13px;color:#47576a;margin:15px 0}}.signalrow{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}}.signal{{font-size:11px;background:#eff5f4;color:#276866;padding:3px 7px;border-radius:4px}}details{{border-top:1px solid var(--line);padding:9px 0}}summary{{font-size:12px;font-weight:700;cursor:pointer}}details ol,details ul{{padding-left:19px;font-size:12px;color:#43596a}}details li{{margin:7px 0}}.citations p{{margin:2px 0;font-size:11px}}.duplicates{{font-size:12px;color:#9b581e}}.foot{{font-size:10px;color:#87919b;margin-top:11px}}.disclaimer{{font-size:12px;color:var(--muted);margin-top:35px}}.empty{{display:none;padding:25px;color:var(--muted);background:white;border-radius:10px}}
@media(max-width:800px){{.metrics{{grid-template-columns:1fr 1fr}}.cols,.tickets{{grid-template-columns:1fr}}.barrow{{grid-template-columns:125px 1fr 25px}}.classification{{grid-template-columns:1fr 1fr}}}}@media(max-width:500px){{.metrics{{grid-template-columns:1fr 1fr}}.metric{{padding:14px}}.metric b{{font-size:25px}}input{{width:100%}}.filters{{width:100%}}select{{width:100%}}}}
</style></head>
<body><header><div class="eyebrow">Identity operations / AI-assisted triage</div><h1>Ticket Triage Copilot</h1><p>Evidence-backed routing, duplicate review and cited IAM playbooks. All recommendations are advisory; no ticket or identity changes are made.</p><div class="stamp">Synthetic demo dataset · Generated {esc(generated)}</div></header>
<main><section class="metrics" aria-label="Ticket summary">
<div class="metric"><b>{s['tickets_processed']}</b><span>Tickets analyzed</span></div>
<div class="metric"><b>{len(categories)}</b><span>Routing categories</span></div>
<div class="metric"><b>{s['possible_duplicate_pairs']}</b><span>Possible duplicate pairs</span></div>
<div class="metric"><b>{s['needs_analyst_review']}</b><span>Needs analyst review</span></div></section>
<section class="cols"><div class="panel"><h2>Ticket distribution</h2><p class="subtitle">Classification determined by auditable phrase matching</p>{bars}</div>
<div class="panel"><h2>Workflow safeguards</h2><p class="subtitle">Designed for IAM analysts, not autonomous access management</p><ol class="steps"><li>Match ticket signals and suggest a queue.</li><li>Retrieve relevant SOPs with traceable article IDs.</li><li>Flag similar tickets for human duplicate review.</li><li>Optionally draft explanations using a local LLM.</li><li>Leave all access and ticket changes to authorized staff.</li></ol></div></section>
<div class="toolbar"><div><h2>Investigation queue</h2><p class="subtitle">Search or filter the {len(results)} sample tickets</p></div><div class="filters"><input id="search" type="search" aria-label="Search tickets" placeholder="Search tickets..."><select id="category" aria-label="Filter by category"><option value="">All categories</option>{options}</select></div></div>
<section class="tickets" id="ticket-list">{''.join(cards)}</section><p class="empty" id="empty">No tickets match the current filters.</p>
<p class="disclaimer">DEMO ONLY · Synthetic ticket content. Routing/priority suggestions are not authoritative. Retrieval scores are not probabilities. All changes require a documented, human-approved workflow.</p></main>
<script>
const search=document.getElementById('search'), category=document.getElementById('category');
function filterTickets(){{const q=search.value.toLowerCase().trim(),cat=category.value;let visible=0;document.querySelectorAll('.ticket').forEach(t=>{{const show=(!q||t.dataset.search.includes(q))&&(!cat||t.dataset.category===cat);t.hidden=!show;if(show)visible++;}});document.getElementById('empty').style.display=visible?'none':'block';}}
search.addEventListener('input',filterTickets);category.addEventListener('change',filterTickets);
</script></body></html>'''
