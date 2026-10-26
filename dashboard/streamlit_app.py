"""RegWatch dashboard on Streamlit — live regulatory monitoring, compliance and risk.

Local run from the repository root:
    streamlit run dashboard/streamlit_app.py

Streamlit Community Cloud:
- Main file path: dashboard/streamlit_app.py
- Secrets (app settings):
      SUPABASE_URL = "https://...supabase.co"
      SUPABASE_KEY = "..."
Streamlit injects secrets as environment variables, which
regwatch.settings (pydantic-settings) reads automatically.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import data  # noqa: E402

st.set_page_config(page_title="RegWatch", page_icon="🛡️", layout="wide")

CSS = """
<style>
h1, h2, h3 { font-family: Georgia, 'Iowan Old Style', serif !important; }
.block-container { padding-top: 2rem; }
.vchip { display:inline-block; padding:2px 9px; border-radius:999px; font-size:11px;
         font-weight:700; white-space:nowrap; }
.v-ok { background:#dff0e6; color:#157f4e; } .v-bad { background:#fbe3df; color:#c0392b; }
.v-warn { background:#fbeed2; color:#9a6a00; } .v-mute { background:#e9e7e2; color:#5b6470; }
.meter { display:block; height:8px; background:#e9e7e2; border-radius:99px; overflow:hidden; }
.meter > span { display:block; height:100%; border-radius:99px; }
.kpi-label { font-size:11px; font-weight:700; letter-spacing:.07em; text-transform:uppercase;
             color:#8a94a0; min-height:2.8em; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

VERDICT_TONE = {"compliant": "ok", "non_compliant": "bad", "needs_review": "warn", "no_policy": "mute"}


def chip(verdict: str) -> str:
    tone = VERDICT_TONE.get(verdict, "mute")
    return f'<span class="vchip v-{tone}">{data.VERDICT_LABELS.get(verdict, verdict)}</span>'


@contextmanager
def live_data():
    try:
        yield
    except data.DashboardUnavailable as exc:
        st.error(f"**Data source unavailable.** {exc}")
        st.stop()


@st.cache_data(ttl=30, show_spinner="Reading live data…")
def cached_overview() -> dict:
    return data.get_overview()


@st.cache_data(ttl=30, show_spinner="Searching documents…")
def cached_documents(**kwargs):
    return data.search_documents(**kwargs)


@st.cache_data(ttl=15, show_spinner="Reading versions…")
def cached_changes(regulation_id: int | None):
    return data.get_change_review(regulation_id)


@st.cache_data(ttl=30, show_spinner="Reading compliance results…")
def cached_compliance(**kwargs):
    return data.get_compliance(**kwargs)


TONES = {"ok": "#157f4e", "bad": "#c0392b", "warn": "#9a6a00", "mute": "#5b6470"}


def meter(count: int, total: int, tone: str) -> str:
    return (f'<span class="meter"><span style="width:{data.pct(count, total)}%;'
            f'background:{TONES[tone]}"></span></span>')


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


def page_overview() -> None:
    st.title("Operations overview")
    st.caption("Live monitoring, compliance verdicts and risk signals across the regulatory watchlist.")

    with live_data():
        ctx = cached_overview()

    cols = st.columns(5, gap="medium")
    kpis = [
        ("Documents tracked", data.fmt_num(ctx["documents"]),
         f"{data.pct(ctx['with_snapshot'], ctx['documents'])}% with a saved snapshot"),
        ("Snapshots stored", data.fmt_num(ctx["snapshots"]), "captured full-text copies"),
        ("Changes detected", data.fmt_num(ctx["changes"]), "second versions recorded"),
        ("Non-compliant checks", data.fmt_num(ctx["verdict_counts"]["non_compliant"]),
         f"of {data.fmt_num(ctx['checks_total'])} assessments"),
        ("Risks scored", data.fmt_num(ctx["risk_total"]),
         f"{ctx['jobs_pending']:,} queued · {ctx['jobs_failed']} failed jobs"),
    ]
    for col, (label, value, sub) in zip(cols, kpis):
        with col:
            st.markdown(f'<p class="kpi-label">{label}</p>', unsafe_allow_html=True)
            st.markdown(f"### {value}")
            st.caption(sub)

    st.progress(data.pct(ctx["with_snapshot"], ctx["documents"]) / 100,
                text=f"Snapshot coverage — {ctx['with_snapshot']:,} of {ctx['documents']:,} documents")

    st.divider()
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Verdict distribution")
        st.caption(f"{ctx['checks_total']} compliance assessments on record")
        for key in ("compliant", "non_compliant", "needs_review", "no_policy"):
            c1, c2, c3 = st.columns([1.4, 2, 0.4])
            c1.markdown(f"**{data.VERDICT_LABELS[key]}**")
            c2.markdown(meter(ctx["verdict_counts"][key], ctx["checks_total"], VERDICT_TONE[key]),
                        unsafe_allow_html=True)
            c3.markdown(f"**{ctx['verdict_counts'][key]}**")
    with right:
        st.subheader("Latest activity")
        if ctx["recent_versions"]:
            st.caption("Snapshots captured")
            for v in ctx["recent_versions"][:4]:
                st.markdown(f"**{v['title'][:48]}**  \nv{v['version_no']} · {data.fmt_date(v['created_at'])}")
        if ctx["recent_checks"]:
            st.caption("Recent verdicts")
            for c in ctx["recent_checks"][:4]:
                st.markdown(f"{chip(c['verdict'])} **{c['company_name']}** · "
                            f"{data.fmt_date(c['created_at'])}", unsafe_allow_html=True)


def page_documents() -> None:
    st.title("Document library")
    st.caption("Every regulation we watch. Search by title, number or department.")

    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    q = c1.text_input("Search", key="doc_q", placeholder="e.g. mutual fund")
    legal_type = c2.selectbox("Type", options=["(any type)"] + list(data.LEGAL_TYPES.values()))
    snapshot = c3.selectbox("Snapshot", options=["Any state", "Snapshot captured", "Awaiting snapshot"])
    sort = c4.selectbox("Sort by", options=list(data.DOC_SORTS.values()))
    oldest_first = c5.checkbox("Oldest first")

    label_to_type = {v: k for k, v in data.LEGAL_TYPES.items()}
    snapshot_to_key = {"Any state": "", "Snapshot captured": "captured", "Awaiting snapshot": "pending"}
    sort_to_key = {v: k for k, v in data.DOC_SORTS.items()}

    with live_data():
        result = cached_documents(
            q=q, legal_type=label_to_type.get(legal_type, ""),
            snapshot=snapshot_to_key[snapshot], sort=sort_to_key[sort],
            direction="asc" if oldest_first else "desc",
            page=st.session_state.get("doc_page", 1),
        )
    if st.session_state.get("doc_page", 1) > result["pages"]:
        st.session_state["doc_page"] = 1
        st.rerun()

    if not result["total"]:
        st.info("**No documents match.** Try a shorter search word, or clear the filters.")
        return

    st.markdown(f"**{result['total']:,}** documents match. Page {result['page']} of {result['pages']}.")
    df = pd.DataFrame(
        [
            {
                "Document": r["title"],
                "Type": data.LEGAL_TYPES.get(r.get("legal_type"), r.get("legal_type", "—")),
                "Issuer": r.get("regulator") or "Unknown",
                "Published": data.fmt_date(r.get("published_date")),
                "Last checked": data.fmt_dt(r.get("last_checked_at")),
                "Saved copy": "Captured" if r.get("has_snapshot") else "Pending",
                "Source": r.get("url") or "",
            }
            for r in result["rows"]
        ]
    )
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "Document": st.column_config.TextColumn(width="large"),
            "Source": st.column_config.LinkColumn(disabled=True, display_text="Open ↗"),
        },
    )
    b1, _, b2 = st.columns([1, 4, 1])
    if b1.button("← Previous", disabled=result["page"] <= 1):
        st.session_state["doc_page"] = result["page"] - 1
        st.rerun()
    if b2.button("Next →", disabled=result["page"] >= result["pages"]):
        st.session_state["doc_page"] = result["page"] + 1
        st.rerun()


def page_changes() -> None:
    st.title("Change review")
    st.caption("Stored version history for every document, with line-level diffs when a re-crawl finds new text.")

    with live_data():
        ctx = cached_changes(None)

    st.markdown(f"**{ctx['snapshots']:,}** snapshots saved · **{ctx['changes']:,}** second versions recorded")
    if ctx["changes"] == 0:
        st.info("All stored snapshots are currently version 1. Re-crawl a document to capture version 2; "
                "any text difference will appear here as a line-by-line diff.")

    options = {f"{v['title'][:52]} (v{v['version_no']} · {data.fmt_date(v['created_at'])})": v["regulation_id"]
               for v in ctx["recent_versions"]}
    picked = st.selectbox("Pick a document to see its stored history",
                          options=options.keys() if options else [])
    if not picked:
        return

    with live_data():
        detail = cached_changes(options[picked])["detail"]

    if not detail:
        st.warning("That document's stored history is unavailable.")
        return
    if detail.get("missing"):
        st.warning("That document isn't in the database.")
        return
    doc = detail["doc"]
    st.subheader(doc["title"])
    st.caption(f"{doc.get('regulator') or 'Unknown issuer'} · {doc.get('legal_type', '').replace('_', ' ').title()}")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Version": f"v{v['version_no']}",
                    "Captured": data.fmt_dt(v.get("created_at")),
                    "Size": f"{v.get('chars', 0):,} chars",
                    "Fingerprint": data.short_hash(v.get("raw_sha256"), 12),
                    "Stored summary": v.get("diff_summary") or "—",
                }
                for v in detail["versions"]
            ]
        ),
        use_container_width=True, hide_index=True,
    )

    diff = detail.get("diff")
    if diff and not diff.get("too_large") and not diff.get("identical"):
        st.markdown(f"🟢 **+{diff['added']} lines added** · 🔴 **−{diff['removed']} lines removed**")
        st.code("\n".join(diff["lines"]), language="diff")
        if diff.get("truncated"):
            st.caption("Diff compacted to the first 160 lines.")
    elif diff and diff.get("identical"):
        st.success("**No text change:** both versions captured the exact same words.")
    elif diff and diff.get("too_large"):
        st.caption("Both versions exist but are too large to diff in the browser — the fingerprints above are the record.")
    elif len(detail["versions"]) >= 2:
        st.caption("Two versions are stored, but their full text wasn't saved, so a side-by-side diff isn't possible.")
    else:
        st.caption("One version so far. The next re-crawl of this document creates version 2 "
                   "and any change will be compared line by line here.")


def page_compliance() -> None:
    st.title("Compliance & risk")
    st.caption("Each check pairs one company policy with one regulatory obligation. "
               "Verdicts are stored results from completed runs.")

    c1, c2 = st.columns([2, 1])
    verdict_names = {"(all checks)": ""}
    verdict_names.update({data.VERDICT_LABELS[k]: k for k in data.VERDICTS})
    verdict_label = c1.pills("Verdict", options=list(verdict_names.keys()), default="(all checks)")
    with live_data():
        companies = cached_compliance()["companies"]

    # Duplicate company names exist in the database, so show the id when ambiguous.
    dup_names = {n for n in companies.values() if list(companies.values()).count(n) > 1}

    def company_label(cid: int | None) -> str:
        if cid is None:
            return "All companies"
        return f"{companies[cid]} · #{cid}" if companies[cid] in dup_names else companies[cid]

    company_id = c2.selectbox(
        "Company",
        options=[None, *sorted(companies, key=lambda cid: companies[cid])],
        format_func=company_label,
    )

    with live_data():
        ctx = cached_compliance(verdict=verdict_names[verdict_label], company=company_id,
                                page=st.session_state.get("cmp_page", 1))
    if st.session_state.get("cmp_page", 1) > ctx["pages"]:
        st.session_state["cmp_page"] = 1
        st.rerun()

    st.markdown(" · ".join(f"{data.VERDICT_LABELS[k]}: **{ctx['verdict_counts'][k]}**"
                           for k in data.VERDICTS))

    if not ctx["total"]:
        st.info("**No assessments match this filter.** " + (
            "Clear the filters to see all stored checks." if verdict_names[verdict_label] or company_id
            else "Assessments appear after the comparison pipeline runs."))
    else:
        st.markdown(f"**{ctx['total']:,}** assessments match. Page {ctx['page']} of {ctx['pages']}.")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Run": data.fmt_dt(r.get("created_at")),
                        "Company": r.get("company_name", "—"),
                        "Verdict": data.VERDICT_LABELS.get(r.get("verdict"), r.get("verdict")),
                        "Confidence": data.fmt_conf(r.get("confidence")),
                        "Method": data.METHOD_LABELS.get(r.get("method"), r.get("method", "—")),
                        "What was checked": r.get("explanation") or "—",
                        "Against policy": r.get("policy_title") or "—",
                    }
                    for r in ctx["rows"]
                ]
            ),
            use_container_width=True, hide_index=True,
            column_config={"What was checked": st.column_config.TextColumn(width="large")},
        )
        b1, _, b2 = st.columns([1, 4, 1])
        if b1.button("← Previous", key="cmp_prev", disabled=ctx["page"] <= 1):
            st.session_state["cmp_page"] = ctx["page"] - 1
            st.rerun()
        if b2.button("Next →", key="cmp_next", disabled=ctx["page"] >= ctx["pages"]):
            st.session_state["cmp_page"] = ctx["page"] + 1
            st.rerun()

    st.divider()
    lcol, rcol = st.columns(2, gap="large")
    with lcol:
        st.subheader("Risk register")
        st.caption(f"{ctx['risk_total']} scored risks by urgency level.")
        if ctx["risks"]:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Company": f.get("company_name", "—"),
                            "Level": data.LEVEL_LABELS.get(f.get("level"), f.get("level", "—")),
                            "Category": (f.get("category") or "—").replace("_", " "),
                            "Why": f.get("reason") or f.get("scope") or "—",
                        }
                        for f in ctx["risks"]
                    ]
                ),
                use_container_width=True, hide_index=True,
                column_config={"Why": st.column_config.TextColumn(width="large")},
            )
        else:
            st.caption("No risks scored yet.")
    with rcol:
        st.subheader("Alerts")
        st.caption(f"{ctx['alert_total']} recorded · delivery channel not configured")
        if ctx["alerts"]:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "When": data.fmt_dt(a.get("created_at")),
                            "Channel": a.get("channel", "—"),
                            "Status": a.get("status", "—"),
                            "Company": a.get("company_name", "—"),
                        }
                        for a in ctx["alerts"]
                    ]
                ),
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("No alerts recorded.")


# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #

pages = [
    st.Page(page_overview, title="Overview", icon="📊", url_path="overview", default=True),
    st.Page(page_documents, title="Documents", icon="📚", url_path="documents"),
    st.Page(page_changes, title="Change review", icon="🔄", url_path="changes"),
    st.Page(page_compliance, title="Compliance & risk", icon="⚖️", url_path="compliance"),
]
st.navigation(pages).run()

st.caption(f"Read-only · live Supabase data · times in IST "
           f"· rendered {data.fmt_dt(datetime.now(data.IST))}")
