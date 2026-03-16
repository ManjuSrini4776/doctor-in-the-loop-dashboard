# ============================================================
# app.py — Doctor-in-the-Loop Clinical Dashboard
# Streamlit Cloud deployable
# ManjuSrini4776 / doctor-in-the-loop-dashboard
# ============================================================

import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
from pipeline import run_rag_pipeline

# ── Page config
st.set_page_config(
    page_title="Doctor-in-the-Loop Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Header */
.dash-header {
    background: linear-gradient(135deg, #0f2744 0%, #1a3f6f 100%);
    padding: 1.2rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.dash-title { color: white; font-size: 1.4rem; font-weight: 600; margin: 0; }
.dash-sub   { color: rgba(255,255,255,0.65); font-size: 0.8rem; margin-top: 2px; }

/* Cards */
.metric-card {
    background: white;
    border: 1px solid #e8edf2;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.metric-val  { font-size: 1.8rem; font-weight: 600; }
.metric-label{ font-size: 0.72rem; color: #6b7280; text-transform: uppercase;
               letter-spacing: 0.05em; margin-top: 2px; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-pending  { background: #FFF3E0; color: #854F0B; }
.badge-approved { background: #E8F5E9; color: #2E7D32; }
.badge-rejected { background: #FFEBEE; color: #C62828; }
.badge-severe   { background: #FFEBEE; color: #C62828; }
.badge-moderate { background: #FFF3E0; color: #854F0B; }
.badge-mild     { background: #E8F5E9; color: #2E7D32; }
.badge-normal   { background: #E3F2FD; color: #1565C0; }

/* Report box */
.report-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #1a3f6f;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.88rem;
    line-height: 1.75;
    color: #1e293b;
    font-family: 'DM Sans', sans-serif;
    white-space: pre-wrap;
}

/* Evidence chips */
.evidence-chip {
    display: inline-block;
    background: #EBF5FB;
    color: #185FA5;
    border: 1px solid #B5D4F4;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.72rem;
    margin: 2px;
    font-family: 'DM Mono', monospace;
}

/* Section divider */
.section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.6rem;
    margin-top: 0.2rem;
}

/* Severity bar */
.sev-bar-wrap {
    background: #e2e8f0;
    border-radius: 4px;
    height: 7px;
    margin-top: 4px;
}
.sev-bar {
    height: 7px;
    border-radius: 4px;
}

/* Patient row */
.patient-item {
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s;
}
.patient-item:hover { background: #f1f5f9; border-color: #e2e8f0; }
.patient-item.active { background: #EBF5FB; border-color: #B5D4F4; }

/* Action buttons */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s !important;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DATA HELPERS
# ══════════════════════════════════════════════
DATA_PATH   = "data/fusion_patient_context.csv"
RAG_PATH    = "rag_output.json"
REVIEW_PATH = "doctor_review_output.json"

@st.cache_data
def load_patients():
    """Load patient fusion data"""
    try:
        df = pd.read_csv(DATA_PATH)
        # Normalise column names
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        return df
    except Exception:
        # Demo data if CSV not found
        return pd.DataFrame([
            {"case_id":"23529134","lab_score":2.0,"ct_score":None,
             "ct_disease":None,"ultrasound_score":None,"ultrasound_disease":None,
             "fusion_score":2.0,"final_severity":"Moderate"},
            {"case_id":"Tr-gl_0042","lab_score":2.0,"ct_score":3.0,
             "ct_disease":"glioma","ultrasound_score":None,"ultrasound_disease":None,
             "fusion_score":3.0,"final_severity":"Severe"},
            {"case_id":"216","lab_score":None,"ct_score":None,
             "ct_disease":None,"ultrasound_score":3.0,"ultrasound_disease":"Fetal brain",
             "fusion_score":3.0,"final_severity":"Severe"},
            {"case_id":"25259089","lab_score":2.0,"ct_score":None,
             "ct_disease":None,"ultrasound_score":None,"ultrasound_disease":None,
             "fusion_score":2.0,"final_severity":"Moderate"},
            {"case_id":"Tr-me_0010","lab_score":None,"ct_score":2.0,
             "ct_disease":"meningioma","ultrasound_score":None,"ultrasound_disease":None,
             "fusion_score":2.0,"final_severity":"Moderate"},
        ])

def load_rag_outputs():
    """Load pre-generated RAG reports"""
    try:
        with open(RAG_PATH, "r") as f:
            data = json.load(f)
        return {str(item["case_id"]): item for item in data} if isinstance(data, list) else data
    except Exception:
        return {}

def load_reviews():
    """Load saved doctor reviews"""
    try:
        with open(REVIEW_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_review(case_id, decision, edited_report, notes, delivery):
    """Save doctor decision to JSON"""
    reviews = load_reviews()
    reviews[str(case_id)] = {
        "case_id":       str(case_id),
        "decision":      decision,
        "edited_report": edited_report,
        "doctor_notes":  notes,
        "delivery":      delivery,
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(REVIEW_PATH, "w") as f:
        json.dump(reviews, f, indent=2)
    return reviews

def severity_color(sev):
    if not sev or str(sev).lower() in ["nan","none",""]:
        return "#94a3b8"
    s = str(sev).lower()
    if "severe" in s:   return "#C62828"
    if "moderate" in s: return "#F28E2B"
    if "mild" in s:     return "#2E7D32"
    return "#1565C0"

def severity_badge_class(sev):
    if not sev or str(sev).lower() in ["nan","none",""]:
        return "badge-normal"
    s = str(sev).lower()
    if "severe" in s:   return "badge-severe"
    if "moderate" in s: return "badge-moderate"
    if "mild" in s:     return "badge-mild"
    return "badge-normal"

def score_pct(score):
    try:
        return min(int(float(score) / 3 * 100), 100)
    except Exception:
        return 0

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 0.5rem;'>
        <div style='font-size:2rem;'>🏥</div>
        <div style='font-weight:600;font-size:1rem;color:#0f2744;'>MedAI Dashboard</div>
        <div style='font-size:0.72rem;color:#94a3b8;margin-top:2px;'>Doctor-in-the-Loop</div>
    </div>
    <hr style='border:none;border-top:1px solid #e2e8f0;margin:0.8rem 0;'>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Overview", "👨‍⚕️ Review Queue", "📊 RAG Analytics", "📁 Approved Reports"],
        label_visibility="collapsed"
    )

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:0.8rem 0;'>",
                unsafe_allow_html=True)

    # Filters
    st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)
    filter_severity = st.multiselect(
        "Severity",
        ["Severe", "Moderate", "Mild", "Normal"],
        default=["Severe", "Moderate"]
    )
    filter_status = st.multiselect(
        "Status",
        ["Pending", "Approved", "Rejected"],
        default=["Pending"]
    )

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:0.8rem 0;'>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.72rem;color:#94a3b8;text-align:center;'>"
        "Medical AI Project · Manju<br>RAG-based Report Generation</div>",
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════
patients_df  = load_patients()
rag_outputs  = load_rag_outputs()
reviews      = load_reviews()

# Add status column
patients_df["status"] = patients_df["case_id"].apply(
    lambda cid: reviews.get(str(cid), {}).get("decision", "Pending")
)

# Apply filters
filtered_df = patients_df.copy()
if filter_severity:
    filtered_df = filtered_df[
        filtered_df["final_severity"].apply(
            lambda s: any(f.lower() in str(s).lower() for f in filter_severity)
        )
    ]
if filter_status:
    filtered_df = filtered_df[filtered_df["status"].isin(filter_status)]

# ══════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════
if page == "🏠 Overview":

    st.markdown(f"""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>🏥 Doctor-in-the-Loop Dashboard</div>
            <div class='dash-sub'>Clinical AI Report Review System · {datetime.now().strftime("%d %b %Y")}</div>
        </div>
        <div style='color:rgba(255,255,255,0.8);font-size:0.8rem;text-align:right;'>
            Multimodal AI · RAG-based<br>
            <span style='color:#7dd3fc;'>Page Index RAG · Faithfulness 0.692</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metric cards
    total     = len(patients_df)
    pending   = len(patients_df[patients_df["status"] == "Pending"])
    approved  = len(patients_df[patients_df["status"] == "Approved"])
    rejected  = len(patients_df[patients_df["status"] == "Rejected"])
    severe    = len(patients_df[patients_df["final_severity"].str.contains("Severe", na=False)])

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, label, color in [
        (c1, total,    "Total Patients",    "#0f2744"),
        (c2, pending,  "Pending Review",    "#854F0B"),
        (c3, approved, "Approved",          "#2E7D32"),
        (c4, rejected, "Rejected",          "#C62828"),
        (c5, severe,   "Severe Cases",      "#C62828"),
    ]:
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-val' style='color:{color};'>{val}</div>
            <div class='metric-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent patients table
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("<div class='section-title'>Recent Patients</div>", unsafe_allow_html=True)
        display_cols = ["case_id","final_severity","fusion_score","ct_disease",
                        "ultrasound_disease","status"]
        show_cols    = [c for c in display_cols if c in patients_df.columns]
        st.dataframe(
            patients_df[show_cols].head(15),
            use_container_width=True,
            hide_index=True,
            column_config={
                "case_id":           st.column_config.TextColumn("Patient ID"),
                "final_severity":    st.column_config.TextColumn("Severity"),
                "fusion_score":      st.column_config.NumberColumn("Score", format="%.1f"),
                "ct_disease":        st.column_config.TextColumn("CT Finding"),
                "ultrasound_disease":st.column_config.TextColumn("US Finding"),
                "status":            st.column_config.TextColumn("Status"),
            }
        )

    with col_right:
        st.markdown("<div class='section-title'>Severity Distribution</div>", unsafe_allow_html=True)
        sev_counts = patients_df["final_severity"].value_counts()
        colors_map = {"Severe":"#C62828","Moderate":"#F28E2B","Mild":"#2E7D32","Normal":"#1565C0"}
        for sev, cnt in sev_counts.items():
            pct = int(cnt / len(patients_df) * 100)
            color = colors_map.get(str(sev), "#94a3b8")
            st.markdown(f"""
            <div style='margin-bottom:10px;'>
                <div style='display:flex;justify-content:space-between;
                            font-size:0.82rem;margin-bottom:3px;'>
                    <span style='font-weight:500;'>{sev}</span>
                    <span style='color:#64748b;'>{cnt} ({pct}%)</span>
                </div>
                <div class='sev-bar-wrap'>
                    <div class='sev-bar' style='width:{pct}%;background:{color};'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Review Progress</div>", unsafe_allow_html=True)
        reviewed = approved + rejected
        pct_done = int(reviewed / max(total, 1) * 100)
        st.markdown(f"""
        <div style='font-size:0.82rem;display:flex;
                    justify-content:space-between;margin-bottom:3px;'>
            <span>Reviewed</span>
            <span style='color:#64748b;'>{reviewed}/{total} ({pct_done}%)</span>
        </div>
        <div class='sev-bar-wrap'>
            <div class='sev-bar' style='width:{pct_done}%;background:#1a3f6f;'></div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# PAGE: REVIEW QUEUE
# ══════════════════════════════════════════════
elif page == "👨‍⚕️ Review Queue":

    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>👨‍⚕️ Patient Review Queue</div>
            <div class='dash-sub'>Review · Edit · Approve or Reject AI-generated reports</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if filtered_df.empty:
        st.info("No patients match your current filters. Adjust the sidebar filters.")
        st.stop()

    # ── Patient selector (left) + detail (right)
    col_queue, col_detail = st.columns([1, 2.5])

    with col_queue:
        st.markdown("<div class='section-title'>Patient Queue</div>", unsafe_allow_html=True)

        if "selected_patient" not in st.session_state:
            st.session_state.selected_patient = str(filtered_df.iloc[0]["case_id"])

        for _, row in filtered_df.iterrows():
            cid    = str(row["case_id"])
            sev    = str(row.get("final_severity","Unknown"))
            status = str(row.get("status","Pending"))
            score  = row.get("fusion_score", "—")
            is_active = cid == st.session_state.selected_patient

            badge_cls = f"badge-{status.lower()}"
            sev_cls   = severity_badge_class(sev)
            color     = severity_color(sev)

            if st.button(
                f"{'▶ ' if is_active else ''}Patient #{cid}",
                key=f"btn_{cid}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_patient = cid
                st.rerun()

            st.markdown(f"""
            <div style='font-size:0.72rem;color:#64748b;
                        margin:-8px 0 6px 4px;display:flex;gap:6px;'>
                <span class='badge {sev_cls}'>{sev}</span>
                <span class='badge {badge_cls}'>{status}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Patient detail panel
    with col_detail:
        cid = st.session_state.selected_patient
        patient = patients_df[patients_df["case_id"].astype(str) == cid]

        if patient.empty:
            st.warning("Patient not found.")
            st.stop()

        p = patient.iloc[0]
        sev   = str(p.get("final_severity","Unknown"))
        score = p.get("fusion_score", None)

        # Patient header
        st.markdown(f"""
        <div style='background:#f8fafc;border:1px solid #e2e8f0;
                    border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='font-size:1.1rem;font-weight:600;color:#0f2744;'>
                        Patient #{cid}
                    </div>
                    <div style='font-size:0.78rem;color:#64748b;margin-top:2px;'>
                        Multimodal AI Assessment
                    </div>
                </div>
                <span class='badge {severity_badge_class(sev)}'
                      style='font-size:0.82rem;padding:5px 14px;'>
                    {sev}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Scores row
        s1, s2, s3, s4 = st.columns(4)
        modalities = [
            (s1, "Lab Score",       p.get("lab_score"),        "#1565C0"),
            (s2, "CT Score",        p.get("ct_score"),         "#C62828"),
            (s3, "Ultrasound",      p.get("ultrasound_score"), "#2E7D32"),
            (s4, "Fusion Score",    score,                     severity_color(sev)),
        ]
        for col, label, val, color in modalities:
            display = f"{float(val):.1f}" if val and str(val) not in ["nan","None"] else "—"
            col.markdown(f"""
            <div class='metric-card' style='border-top:3px solid {color};'>
                <div class='metric-val' style='color:{color};font-size:1.5rem;'>{display}</div>
                <div class='metric-label'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Findings row
        findings = []
        if str(p.get("ct_disease","")).lower() not in ["nan","none",""]:
            findings.append(f"CT: {p['ct_disease']}")
        if str(p.get("ultrasound_disease","")).lower() not in ["nan","none",""]:
            findings.append(f"US: {p['ultrasound_disease']}")
        if findings:
            st.markdown(
                " &nbsp;|&nbsp; ".join(
                    [f"<span class='evidence-chip'>{f}</span>" for f in findings]
                ),
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

        # ── RAG Report section
        st.markdown("<div class='section-title'>AI-Generated Clinical Report</div>",
                    unsafe_allow_html=True)

        # Get existing RAG report or generate
        existing_review = reviews.get(cid, {})
        rag_data = rag_outputs.get(cid, {})
        default_report = rag_data.get("report", "")

        if not default_report:
            if st.button("⚡ Generate RAG Report", type="primary", key=f"gen_{cid}"):
                with st.spinner("Running RAG pipeline..."):
                    try:
                        result = run_rag_pipeline(p.to_dict())
                        default_report = result.get("report","Report generation failed.")
                        # Save to rag_output.json
                        rag_outputs[cid] = result
                        with open(RAG_PATH,"w") as f:
                            json.dump(list(rag_outputs.values()), f, indent=2)
                        st.success("Report generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Pipeline error: {e}")
        else:
            # Show RAG metadata
            rag_type = rag_data.get("rag_type", "Page Index RAG")
            faith    = rag_data.get("faithfulness", 0.692)
            st.markdown(f"""
            <div style='display:flex;gap:8px;margin-bottom:8px;'>
                <span class='evidence-chip'>{rag_type}</span>
                <span class='evidence-chip'>Faithfulness: {faith:.3f}</span>
            </div>
            """, unsafe_allow_html=True)

            # Evidence sources
            sources = rag_data.get("sources", [])
            if sources:
                st.markdown(
                    "".join([f"<span class='evidence-chip'>📄 {s}</span>" for s in sources[:5]]),
                    unsafe_allow_html=True
                )
                st.markdown("<br>", unsafe_allow_html=True)

        # Editable report
        edited_report = st.text_area(
            "Clinical Report (editable)",
            value=existing_review.get("edited_report", default_report),
            height=200,
            key=f"report_{cid}",
            placeholder="RAG-generated report will appear here. You can edit before approving.",
            label_visibility="collapsed"
        )

        # Doctor notes
        st.markdown("<div class='section-title' style='margin-top:0.8rem;'>Doctor Notes</div>",
                    unsafe_allow_html=True)
        doctor_notes = st.text_area(
            "Notes",
            value=existing_review.get("doctor_notes",""),
            height=80,
            key=f"notes_{cid}",
            placeholder="Add clinical observations, corrections or follow-up instructions...",
            label_visibility="collapsed"
        )

        # Delivery options
        st.markdown("<div class='section-title' style='margin-top:0.8rem;'>Deliver Report Via</div>",
                    unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4)
        prev_delivery = existing_review.get("delivery", [])
        del_pdf  = d1.checkbox("📄 PDF",       value="PDF" in prev_delivery,       key=f"pdf_{cid}")
        del_wa   = d2.checkbox("💬 WhatsApp",  value="WhatsApp" in prev_delivery,  key=f"wa_{cid}")
        del_email= d3.checkbox("📧 Email",     value="Email" in prev_delivery,     key=f"email_{cid}")
        del_rec  = d4.checkbox("💾 Record",    value="Record" in prev_delivery,    key=f"rec_{cid}")
        delivery = ([" PDF"] * del_pdf + ["WhatsApp"] * del_wa +
                    ["Email"] * del_email + ["Record"] * del_rec)

        # Action buttons
        st.markdown("<br>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)

        with b1:
            if st.button("✅ Approve", key=f"approve_{cid}",
                         use_container_width=True, type="primary"):
                save_review(cid, "Approved", edited_report, doctor_notes, delivery)
                st.success(f"✅ Patient #{cid} report approved!")
                st.balloons()
                st.rerun()

        with b2:
            if st.button("✏️ Save Edit", key=f"edit_{cid}",
                         use_container_width=True):
                save_review(cid, "Edited", edited_report, doctor_notes, delivery)
                st.info("💾 Edits saved successfully.")
                st.rerun()

        with b3:
            if st.button("❌ Reject", key=f"reject_{cid}",
                         use_container_width=True):
                save_review(cid, "Rejected", edited_report, doctor_notes, delivery)
                st.warning(f"❌ Patient #{cid} report rejected.")
                st.rerun()

        # Download approved report as text
        current_status = reviews.get(cid, {}).get("decision","Pending")
        if current_status == "Approved" and edited_report:
            st.download_button(
                label="⬇️ Download Approved Report",
                data=f"APPROVED CLINICAL REPORT\nPatient ID: {cid}\n"
                     f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                     f"Severity: {sev}\n\n{edited_report}\n\n"
                     f"Doctor Notes:\n{doctor_notes}",
                file_name=f"report_{cid}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )


# ══════════════════════════════════════════════
# PAGE: RAG ANALYTICS
# ══════════════════════════════════════════════
elif page == "📊 RAG Analytics":

    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>📊 RAG Performance Analytics</div>
            <div class='dash-sub'>Baseline vs Hierarchical vs Page Index — V1 → V2 Comparison</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    import plotly.graph_objects as go

    # Results data
    rag_labels = ["Baseline", "Hierarchical", "Page Index"]
    faith_v1   = [0.5606, 0.4687, 0.4461]
    faith_v2   = [0.4568, 0.4180, 0.6919]
    relev_v1   = [0.4718, 0.3922, 0.5664]
    relev_v2   = [0.4634, 0.7012, 0.6050]
    latency    = [2.764,  2.559,  3.619]

    # Metric summary cards
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label, delta, color in [
        (c1, "0.692", "Best Faithfulness",  "+0.246 Page Index V2", "#2E7D32"),
        (c2, "0.701", "Best Relevancy",     "+0.309 Hierarchical V2","#2E7D32"),
        (c3, "2.56s", "Fastest RAG",        "Hierarchical V2",       "#1565C0"),
        (c4, "~0.62", "Avg Score V2",       "from ~0.51 V1",         "#854F0B"),
    ]:
        col.markdown(f"""
        <div class='metric-card' style='border-top:3px solid {color};'>
            <div class='metric-val' style='color:{color};'>{val}</div>
            <div class='metric-label'>{label}</div>
            <div style='font-size:0.7rem;color:#94a3b8;margin-top:4px;'>{delta}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grouped bar charts
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="V1 Original", x=rag_labels, y=faith_v1,
                             marker_color="#A8C4DC", text=[f"{v:.3f}" for v in faith_v1],
                             textposition="outside"))
        fig.add_trace(go.Bar(name="V2 Improved", x=rag_labels, y=faith_v2,
                             marker_color="#1F5F8B", text=[f"{v:.3f}" for v in faith_v2],
                             textposition="outside"))
        fig.update_layout(
            title="Faithfulness ↑", barmode="group",
            yaxis=dict(range=[0,1], title="Score"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.2),
            height=340, margin=dict(t=40,b=60,l=40,r=20)
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="V1 Original", x=rag_labels, y=relev_v1,
                              marker_color="#A8C4DC", text=[f"{v:.3f}" for v in relev_v1],
                              textposition="outside"))
        fig2.add_trace(go.Bar(name="V2 Improved", x=rag_labels, y=relev_v2,
                              marker_color="#1F5F8B", text=[f"{v:.3f}" for v in relev_v2],
                              textposition="outside"))
        fig2.update_layout(
            title="Answer Relevancy ↑", barmode="group",
            yaxis=dict(range=[0,1], title="Score"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.2),
            height=340, margin=dict(t=40,b=60,l=40,r=20)
        )
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(gridcolor="#f1f5f9")
        st.plotly_chart(fig2, use_container_width=True)

    # Radar chart
    col3, col4 = st.columns(2)

    with col3:
        max_lat = max(latency)
        categories = ["Faithfulness","Answer Relevancy","Speed (norm)","Faithfulness"]
        fig3 = go.Figure()
        for name, f, r, lat, color in [
            ("Baseline",     faith_v2[0], relev_v2[0], latency[0], "#4E79A7"),
            ("Hierarchical", faith_v2[1], relev_v2[1], latency[1], "#F28E2B"),
            ("Page Index",   faith_v2[2], relev_v2[2], latency[2], "#59A14F"),
        ]:
            speed = round(1 - lat/max_lat, 3)
            fig3.add_trace(go.Scatterpolar(
                r=[f, r, speed, f], theta=categories,
                fill="toself", name=name,
                line_color=color, fillcolor=color,
                opacity=0.25
            ))
        fig3.update_layout(
            title="V2 Quality Profile",
            polar=dict(radialaxis=dict(visible=True, range=[0,1])),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.15),
            height=360, margin=dict(t=50,b=60,l=40,r=40)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Delta comparison
        deltas_f = [round(f2-f1,4) for f1,f2 in zip(faith_v1,faith_v2)]
        deltas_r = [round(r2-r1,4) for r1,r2 in zip(relev_v1,relev_v2)]
        colors_f = ["#2E7D32" if d>=0 else "#C62828" for d in deltas_f]
        colors_r = ["#2E7D32" if d>=0 else "#C62828" for d in deltas_r]

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name="Faithfulness Δ", x=rag_labels, y=deltas_f,
            marker_color=colors_f, text=[f"{'+' if d>=0 else ''}{d:.3f}" for d in deltas_f],
            textposition="outside"
        ))
        fig4.add_trace(go.Bar(
            name="Relevancy Δ", x=rag_labels, y=deltas_r,
            marker_color=["#52b788" if d>=0 else "#e63946" for d in deltas_r],
            text=[f"{'+' if d>=0 else ''}{d:.3f}" for d in deltas_r],
            textposition="outside", opacity=0.75
        ))
        fig4.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
        fig4.update_layout(
            title="V1 → V2 Score Delta", barmode="group",
            yaxis=dict(title="Δ Score"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.2),
            height=360, margin=dict(t=50,b=60,l=40,r=20)
        )
        fig4.update_xaxes(showgrid=False)
        fig4.update_yaxes(gridcolor="#f1f5f9")
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════
# PAGE: APPROVED REPORTS
# ══════════════════════════════════════════════
elif page == "📁 Approved Reports":

    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>📁 Approved Reports Log</div>
            <div class='dash-sub'>All doctor-reviewed and approved clinical reports</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not reviews:
        st.info("No reviews yet. Go to Review Queue to approve reports.")
        st.stop()

    approved_list = [v for v in reviews.values() if v.get("decision") == "Approved"]
    rejected_list = [v for v in reviews.values() if v.get("decision") == "Rejected"]

    tab1, tab2, tab3 = st.tabs([
        f"✅ Approved ({len(approved_list)})",
        f"❌ Rejected ({len(rejected_list)})",
        f"📋 All Reviews ({len(reviews)})"
    ])

    def show_reviews_table(review_list):
        if not review_list:
            st.info("No records in this category.")
            return
        df = pd.DataFrame(review_list)
        show = [c for c in ["case_id","decision","timestamp","doctor_notes","delivery"]
                if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)

        # Download all as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download as CSV",
            data=csv,
            file_name=f"reviews_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with tab1:
        show_reviews_table(approved_list)
        for rev in approved_list:
            with st.expander(f"Patient #{rev['case_id']} — {rev.get('timestamp','')}"):
                st.markdown(f"""
                <div class='report-box'>{rev.get('edited_report','—')}</div>
                """, unsafe_allow_html=True)
                if rev.get("doctor_notes"):
                    st.markdown(f"**Doctor Notes:** {rev['doctor_notes']}")
                st.download_button(
                    "⬇️ Download",
                    data=rev.get("edited_report",""),
                    file_name=f"report_{rev['case_id']}.txt",
                    mime="text/plain",
                    key=f"dl_{rev['case_id']}"
                )

    with tab2:
        show_reviews_table(rejected_list)

    with tab3:
        show_reviews_table(list(reviews.values()))
