# ui.py (project root)
# Run:
#   Terminal A: python -m uvicorn app.main:app --reload
#   Terminal B: streamlit run ui.py

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/run"

st.set_page_config(
    page_title="Verified B2B Lead Generator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Session State ----------
if "history" not in st.session_state:
    st.session_state.history: List[Dict[str, Any]] = []  # store past runs


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _api_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(API_URL, json=payload, timeout=300)
    if r.status_code >= 400:
        # show body (FastAPI detail) if available
        raise RuntimeError(f"API {r.status_code}: {r.text}")
    return r.json()


def _save_uploaded_csv(uploaded_file) -> str:
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "uploaded_leads.csv")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


# ---------- Header ----------
top = st.container()
with top:
    st.markdown("## Verified B2B Lead Generator for Marketing Agencies")
    st.caption(
        "Generate targeted leads by niche & location, discover + verify emails, dedupe, score leads, "
        "and create outreach-ready cold emails. Export a clean CSV."
    )

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### Inputs")

    niche = st.text_input("Niche", value="dentists")
    location = st.text_input("Location", value="Berlin")

    source = st.selectbox("Lead source", ["serpapi", "csv", "directory_stub"], index=0)
    limit = st.number_input("Limit", min_value=1, max_value=500, value=50, step=1)

    st.markdown("---")
    st.markdown("### Enrichment")
    discover_emails = st.checkbox("Discover emails from websites", value=True)

    # Note: if you later add toggles in backend, keep them here.
    # verify_emails toggle is not needed because your backend verifies when email exists.

    st.markdown("---")
    st.markdown("### CSV source (only when source = csv)")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    csv_path = st.text_input("Or use existing CSV path", value="data/sample_leads.csv")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        run_btn = st.button("Run", type="primary", use_container_width=True)
    with col_b:
        demo_btn = st.button("Demo", type="secondary", use_container_width=True)

    with st.expander("Advanced"):
        only_qualified_default = st.checkbox("Default: show only qualified", value=True)
        show_debug_default = st.checkbox("Show debug panel", value=False)
        max_email_previews = st.slider("Emails to preview", 1, 20, 6)

    if st.session_state.history:
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# ---------- Validate / Prepare payload ----------
trigger = run_btn or demo_btn

if trigger:
    # Demo overrides (fast recording)
    if demo_btn:
        niche = "dentists"
        location = "Berlin"
        source = "serpapi"
        limit = 10
        discover_emails = True
        uploaded = None
        csv_path = "data/sample_leads.csv"

    niche_clean = (niche or "").strip()
    location_clean = (location or "").strip()

    if not niche_clean or not location_clean:
        st.error("Please fill both Niche and Location.")
        st.stop()

    final_csv_path = csv_path
    if source == "csv":
        if uploaded is not None:
            final_csv_path = _save_uploaded_csv(uploaded)
        if not final_csv_path or not os.path.exists(final_csv_path):
            st.error("CSV source selected, but the CSV file path is missing or does not exist.")
            st.stop()

    payload = {
        "niche": niche_clean,
        "location": location_clean,
        "source": source,
        "limit": int(limit),
        "csv_path": final_csv_path,
        "discover_emails": bool(discover_emails),
    }

    # ---------- Run ----------
    with st.spinner("Running agent… fetching leads, discovering/validating emails, scoring, drafting outreach…"):
        start = time.time()
        try:
            data = _api_post(payload)
        except Exception as e:
            st.error("Request failed.")
            st.code(str(e))
            st.stop()
        elapsed = round(time.time() - start, 2)

    # save to history
    meta = data.get("meta", {}) or {}
    data["_ui"] = {
        "timestamp": _now_str(),
        "payload": payload,
        "elapsed_local": elapsed,
    }
    st.session_state.history.insert(0, data)

# ---------- Choose current run (latest by default) ----------
current = st.session_state.history[0] if st.session_state.history else None

# ---------- History selector ----------
if st.session_state.history:
    with st.container():
        st.markdown("### Runs")
        labels = []
        for i, run in enumerate(st.session_state.history[:15]):
            ui = run.get("_ui", {})
            p = ui.get("payload", {})
            labels.append(
                f"{ui.get('timestamp', '')}  •  {p.get('source','?')}  •  {p.get('niche','?')} @ {p.get('location','?')}  •  leads={run.get('count','?')}"
            )
        selected = st.selectbox("Select a run", options=list(range(len(labels))), format_func=lambda i: labels[i])
        current = st.session_state.history[selected]
else:
    st.info("Run the agent to see results here.")
    st.stop()

# ---------- Metrics bar ----------
meta = current.get("meta", {}) or {}
ui = current.get("_ui", {}) or {}
leads = current.get("leads", []) or []

count = int(current.get("count") or 0)
qualified_count = int(meta.get("qualified_count") or 0)
valid_emails = int(meta.get("email_valid_ok") or 0)
email_invalid = int(meta.get("email_invalid") or 0)
email_missing = int(meta.get("email_missing") or 0)
elapsed_sec = meta.get("elapsed_sec", ui.get("elapsed_local", ""))

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Leads", f"{count}")
m2.metric("Qualified", f"{qualified_count}")
m3.metric("Valid emails", f"{valid_emails}")
m4.metric("Invalid emails", f"{email_invalid}")
m5.metric("Missing emails", f"{email_missing}")

st.caption(f"Source: **{meta.get('source', ui.get('payload', {}).get('source', ''))}** • Time: **{elapsed_sec}s**")

# ---------- Tabs ----------
tab_leads, tab_outreach, tab_export, tab_debug = st.tabs(["Leads", "Outreach", "Export", "Debug"])

with tab_leads:
    st.markdown("#### Lead list")

    only_qualified = st.checkbox("Show only qualified", value=bool(only_qualified_default), key="only_qualified")
    search = st.text_input("Search (business / email / website)", value="", key="search")

    preview_rows = []
    search_l = search.strip().lower()

    for l in leads:
        if only_qualified and not l.get("qualified"):
            continue

        # search filter
        if search_l:
            hay = " ".join(
                [
                    str(l.get("business_name") or ""),
                    str(l.get("email") or ""),
                    str(l.get("website") or ""),
                    str(l.get("city") or ""),
                ]
            ).lower()
            if search_l not in hay:
                continue

        preview_rows.append(
            {
                "business_name": l.get("business_name"),
                "city": l.get("city"),
                "website": l.get("website"),
                "email": l.get("email"),
                "email_valid": l.get("email_valid"),
                "email_reason": l.get("email_validation_reason"),
                "score": l.get("score"),
                "qualified": l.get("qualified"),
            }
        )

    if preview_rows:
        st.dataframe(preview_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No leads match your filters.")

with tab_outreach:
    st.markdown("#### Outreach drafts (qualified leads)")

    show_only_with_email = st.checkbox("Show only leads that have an email", value=True)

    shown = 0
    for l in leads:
        if not l.get("qualified"):
            continue
        if show_only_with_email and not l.get("email"):
            continue

        name = l.get("business_name") or "(No name)"
        email = l.get("email") or ""
        email_valid_flag = l.get("email_valid")
        email_reason = l.get("email_validation_reason") or ""

        st.markdown(f"**{name}**")
        if email:
            st.caption(f"{email} • valid={email_valid_flag} ({email_reason})")
        else:
            st.caption("No email found")

        subj = (l.get("outreach_email_subject") or "").strip()
        body = (l.get("outreach_email_body") or "").strip()

        if subj:
            st.markdown(f"**Subject:** {subj}")

        if body:
            st.text(body)
        else:
            st.info("No outreach generated (lead may not be qualified).")

        st.divider()
        shown += 1
        if shown >= int(max_email_previews):
            break

    if shown == 0:
        st.info("No qualified leads to show yet. Try increasing the limit or changing niche/location.")

with tab_export:
    st.markdown("#### Export")

    export_path = meta.get("export_csv", "outputs/leads.csv")
    colx, coly = st.columns([2, 1])

    with colx:
        st.write("Export path (server-side):")
        st.code(export_path)

    with coly:
        st.write("Download:")
        if os.path.exists(export_path):
            with open(export_path, "rb") as f:
                st.download_button(
                    label="Download Clean Verified Leads (CSV)",
                    data=f,
                    file_name=f"leads_{(ui.get('timestamp','').replace(':','-').replace(' ','_') or 'export')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.warning("CSV not found. Run again and ensure export is enabled.")

    st.markdown("---")
    st.markdown("#### Recommended next action (for selling)")
    st.write(
        "- Record a 30–45s demo: run → show metrics → show outreach → download CSV.\n"
        "- Put the words **verified**, **deduplicated**, **ready-to-send outreach** in your gig."
    )

with tab_debug:
    show_debug = bool(show_debug_default)
    if not show_debug:
        st.info("Debug is disabled (enable it in Sidebar → Advanced).")
    else:
        st.markdown("#### Debug")
        st.markdown("**Payload**")
        st.code(json.dumps(ui.get("payload", {}), indent=2), language="json")

        st.markdown("**Meta**")
        st.code(json.dumps(meta, indent=2), language="json")

        st.markdown("**First lead (raw)**")
        if leads:
            st.code(json.dumps(leads[0], indent=2), language="json")
        else:
            st.write("No leads.")