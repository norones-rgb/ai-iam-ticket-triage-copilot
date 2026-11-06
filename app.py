"""Optional Streamlit UI. Run: streamlit run app.py"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from iam_ticket_copilot.ingest import InputError, load_articles, load_tickets
from iam_ticket_copilot.narrative import LocalAIError
from iam_ticket_copilot.pipeline import stats, triage_tickets
from iam_ticket_copilot.reporting import save_reports

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="IAM Ticket Triage Copilot", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.block-container {max-width:1180px;padding-top:2rem}
.kicker {font-size:0.8rem;letter-spacing:0.14em;font-weight:750;color:#b77c51}
.smallnote {color:#64748b;font-size:0.9rem}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="kicker">IDENTITY OPERATIONS · PORTFOLIO DEMO</div>', unsafe_allow_html=True)
st.title("IAM Ticket Triage Copilot")
st.caption("Transparent routing rules + cited local playbooks + duplicate flags + optional loopback-only LLM. No ticket modifications.")

with st.sidebar:
    st.header("Data & settings")
    ticket_file = st.file_uploader("Ticket data (JSON / CSV)", type=["json", "csv"])
    kb_file = st.file_uploader("Knowledge base (JSON)", type=["json"], key="kb")
    st.caption("No upload? The app uses synthetic sample data included with the project.")
    local_ai = st.checkbox("Use optional local Ollama explanations", value=False)
    model = st.text_input("Installed Ollama model", value="llama3.2:3b", disabled=not local_ai)
    st.info("No ServiceNow/Jira API connection. Never upload corporate records or secrets to a public demo.")

if st.button("Analyze tickets", type="primary"):
    try:
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            ticket_path = ROOT / "samples" / "synthetic_tickets.json"
            kb_path = ROOT / "samples" / "kb" / "iam_playbooks.json"
            if ticket_file is not None:
                ticket_path = folder / ("uploaded.csv" if ticket_file.name.lower().endswith(".csv") else "uploaded.json")
                ticket_path.write_bytes(ticket_file.getvalue())
            if kb_file is not None:
                kb_path = folder / "uploaded-kb.json"
                kb_path.write_bytes(kb_file.getvalue())
            results = triage_tickets(load_tickets(ticket_path), load_articles(kb_path),
                                     use_ollama=local_ai, model=model)
            paths = save_reports(results, folder / "reports")
            st.session_state["report"] = {kind: path.read_bytes() for kind, path in paths.items()}
            st.session_state["result"] = [r.to_dict() for r in results]
            st.session_state["summary"] = stats(results)
    except (OSError, InputError, LocalAIError, ValueError) as exc:
        st.error(f"Unable to analyze data: {exc}")

if "result" in st.session_state:
    summary = st.session_state["summary"]
    a, b, c, d = st.columns(4)
    a.metric("Tickets", summary["tickets_processed"])
    b.metric("Routing categories", len(summary["category_counts"]))
    c.metric("Potential duplicate pairs", summary["possible_duplicate_pairs"])
    d.metric("Manual review", summary["needs_analyst_review"])
    st.subheader("Ticket queue")
    category_filter = st.selectbox("Filter category", ["All categories"] + list(summary["category_counts"]))
    filtered = [r for r in st.session_state["result"] if category_filter == "All categories" or r["category"] == category_filter]
    for r in filtered:
        with st.expander(f"{r['ticket_id']} · {r['subject']}  |  {r['priority']}"):
            st.write(f"**Category:** {r['category']}  |  **Group:** {r['assignment_group']}")
            st.write(f"**Matched signals:** {', '.join(r['evidence_signals']) or 'None'}")
            st.write(r["summary"])
            st.write("**Recommended investigation:**")
            for item in r["next_steps"]:
                st.write(f"- {item}")
            st.write("**Retrieved playbooks:**")
            for source in r["citations"]:
                st.write(f"- {source['article_id']}: {source['title']}")
            if r["possible_duplicates"]:
                st.warning(f"Potential duplicates: {', '.join(d['ticket_id'] for d in r['possible_duplicates'])}")
    st.subheader("Export advisory reports")
    one, two, three = st.columns(3)
    one.download_button("Download HTML", st.session_state["report"]["html"], "iam-ticket-triage.html", "text/html")
    two.download_button("Download JSON", st.session_state["report"]["json"], "iam-ticket-triage.json", "application/json")
    three.download_button("Download CSV", st.session_state["report"]["csv"], "iam-ticket-triage.csv", "text/csv")
else:
    st.info("Click **Analyze tickets** to explore the included synthetic IAM tickets.")
