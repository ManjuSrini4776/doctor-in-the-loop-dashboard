import json
import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd

# =====================================================
# Page config
# =====================================================
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Review Dashboard",
    layout="wide"
)

# =====================================================
# Simple dashboard CSS
# =====================================================
st.markdown("""
<style>
.card {
    padding: 16px;
    border-radius: 12px;
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
}

.kpi-blue { background:#e8f0fe; }
.kpi-green { background:#e6f7ee; }
.kpi-orange { background:#fff4e5; }

.kpi-title {
    font-size:13px;
    color:#374151;
}

.kpi-value {
    font-size:24px;
    font-weight:700;
    color:#111827;
}

.section-box{
    padding:16px;
    border-radius:12px;
    border:1px solid #e5e7eb;
    background:white;
    margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)

st.title("Doctor-in-the-Loop Clinical Review Dashboard")
st.caption("Workflow-driven AI clinical triage and reporting system")

# =====================================================
# Sidebar (left navigation)
# =====================================================
st.sidebar.header("Clinical workflow")

page = st.sidebar.radio(
    "",
    [
        "Overview",
        "Clinical Evidence",
        "Guideline Summary",
        "Doctor Decision",
        "Patient Communication"
    ]
)

st.sidebar.divider()

# =====================================================
# Load JSON
# =====================================================
DATA_PATH = Path("data/ct_demo_with_rag.json")

if not DATA_PATH.exists():
    st.error("Required CT review JSON not found.")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

# =====================================================
# Safe extraction
# =====================================================
patient = data.get("patient_details", {})
ct_out = data.get("ct_model_output", {})
fusion = data.get("ai_severity_fusion", {})
imaging = data.get("imaging_evidence", {})

validation_decision = data.get("validation_decision", "-")
validation_reason   = data.get("validation_reason", "-")
rag_imaging_sources = data.get("rag_imaging_sources", [])
rag_pathway_sources = data.get("rag_pathway_sources", [])
doctor_summary      = data.get("doctor_facing_summary", "-")

# Sidebar case info
st.sidebar.markdown("### Case information")
st.sidebar.write("Patient ID:", patient.get("patient_id", "-"))
st.sidebar.write("Modality:", patient.get("modality", "CT Brain"))

# =====================================================
# Session
# =====================================================
if "case_status" not in st.session_state:
    st.session_state.case_status = "PENDING"

if "timeline" not in st.session_state:
    st.session_state.timeline = []

def log_event(msg):
    st.session_state.timeline.append(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}"
    )

# =====================================================
# Header bar + workflow progress
# =====================================================
st.markdown(f"""
<div style="
padding:12px;
border-radius:10px;
background:#f1f5f9;
border:1px solid #e5e7eb;
font-size:14px;">
<b>Clinical review workspace</b> &nbsp; | &nbsp;
Case: {patient.get("patient_id","-")} &nbsp; | &nbsp;
Modality: {patient.get("modality","CT Brain")} &nbsp; | &nbsp;
Workflow: Doctor-in-the-loop validation
</div>
""", unsafe_allow_html=True)

progress_map = {
    "Overview": 20,
    "Clinical Evidence": 40,
    "Guideline Summary": 60,
    "Doctor Decision": 80,
    "Patient Communication": 100
}
st.progress(progress_map[page])

st.write("")

# =====================================================
# Status banner
# =====================================================
if st.session_state.case_status == "PENDING":
    st.warning("Case status: Pending doctor review")
elif st.session_state.case_status == "APPROVED":
    st.success("Case status: Approved by doctor")
elif st.session_state.case_status == "REJECTED":
    st.error("Case status: Rejected by doctor")

# Common confidence
try:
    conf = round(float(ct_out.get("confidence", 0)) * 100, 2)
except:
    conf = "-"

# =====================================================
# OVERVIEW
# =====================================================
if page == "Overview":

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="card kpi-blue">
            <div class="kpi-title">Patient ID</div>
            <div class="kpi-value">{patient.get("patient_id","-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card kpi-green">
            <div class="kpi-title">CT prediction</div>
            <div class="kpi-value">{ct_out.get("prediction","-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card kpi-orange">
            <div class="kpi-title">Final severity</div>
            <div class="kpi-value">{fusion.get("derived_severity","-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card kpi-blue">
            <div class="kpi-title">Model confidence</div>
            <div class="kpi-value">{conf}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        st.subheader("Imaging evidence")

        st.write("Modality:", "CT Brain")
        st.write("Image ID:", imaging.get("image_id", "-"))

        img_path = imaging.get("image_path", None)
        if img_path and Path(img_path).exists():
            st.image(img_path, use_container_width=True)
        else:
            st.info("CT image preview not available in this demo JSON.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        st.subheader("Clinical validation")

        st.write("Validation decision:")
        st.write(validation_decision)

        st.write("Validation reason:")
        st.write(validation_reason)

        st.write("Patient context:")
        st.write(patient.get("context", "-"))

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("Model confidence overview")

    try:
        df = pd.DataFrame({
            "Stage": ["CT model"],
            "Confidence": [float(conf)]
        })
    except:
        df = pd.DataFrame({"Stage": ["CT model"], "Confidence": [0]})

    st.bar_chart(df.set_index("Stage"))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("Case activity log")

    if len(st.session_state.timeline) == 0:
        st.write("No activity yet.")
    else:
        for t in st.session_state.timeline:
            st.write("-", t)

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# CLINICAL EVIDENCE
# =====================================================
elif page == "Clinical Evidence":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    st.subheader("Model evidence")
    st.write("Prediction:", ct_out.get("prediction", "-"))
    st.write("Confidence:", conf, "%")
    st.write("Image ID:", imaging.get("image_id", "-"))

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("Imaging guideline sources")

    if rag_imaging_sources:
        for s in rag_imaging_sources:
            st.write("-", s)
    else:
        st.write("No imaging sources available.")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# GUIDELINE SUMMARY
# =====================================================
elif page == "Guideline Summary":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    st.subheader("Doctor-facing guideline grounded summary")
    st.write(doctor_summary)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.subheader("Audit trail - retrieved guideline sources")

    st.write("Imaging sources")
    if rag_imaging_sources:
        for s in rag_imaging_sources:
            st.write("-", s)
    else:
        st.write("None")

    st.write("Clinical pathway sources")
    if rag_pathway_sources:
        for s in rag_pathway_sources:
            st.write("-", s)
    else:
        st.write("None")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# DOCTOR DECISION
# =====================================================
elif page == "Doctor Decision":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    st.subheader("Doctor verification and decision")

    edited_summary = st.text_area(
        "Editable clinical summary",
        doctor_summary,
        height=220
    )

    reject_reason = st.text_area(
        "Rejection reason (required only if rejecting)",
        height=120
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        approve = st.button("Approve")

    with col2:
        save_edit = st.button("Save edited summary")

    with col3:
        reject = st.button("Reject")

    if save_edit:
        doctor_summary = edited_summary
        log_event("Doctor edited clinical summary")
        st.success("Edited summary saved.")

    if approve:
        st.session_state.case_status = "APPROVED"
        log_event("Doctor approved case")
        st.success("Case approved.")

        final_output = {
            "patient_id": patient.get("patient_id"),
            "modality": "CT Brain",
            "image_id": imaging.get("image_id"),
            "ct_prediction": ct_out.get("prediction"),
            "confidence": ct_out.get("confidence"),
            "final_severity": fusion.get("derived_severity"),
            "patient_context": patient.get("context"),
            "validation_decision": validation_decision,
            "validation_reason": validation_reason,
            "rag_imaging_sources": rag_imaging_sources,
            "rag_pathway_sources": rag_pathway_sources,
            "doctor_facing_summary": edited_summary,
            "doctor_decision": "APPROVED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        st.subheader("Doctor approved output")
        st.json(final_output)

        st.download_button(
            "Download approved JSON",
            json.dumps(final_output, indent=4),
            file_name=f"{patient.get('patient_id','CT')}_doctor_output.json",
            mime="application/json"
        )

    if reject:
        if reject_reason.strip() == "":
            st.error("Rejection reason is required.")
        else:
            st.session_state.case_status = "REJECTED"
            log_event("Doctor rejected case")
            st.error("Case rejected.")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# PATIENT COMMUNICATION
# =====================================================
elif page == "Patient Communication":

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    st.subheader("Patient communication")

    if st.session_state.case_status != "APPROVED":
        st.warning("Patient communication is locked until doctor approval.")
    else:

        patient_message = (
            f"Hello,\n\n"
            f"Your CT brain report has been reviewed and approved by your doctor.\n\n"
            f"Patient ID: {patient.get('patient_id', '-')}\n"
            f"Result: {ct_out.get('prediction','-')}\n"
            f"Severity: {fusion.get('derived_severity', '-')}\n\n"
            f"If you have symptoms or concerns, please schedule a follow-up appointment with your doctor.\n\n"
            f"Hospital Care Team"
        )

        st.text_area(
            "Patient message preview",
            patient_message,
            height=220
        )

    st.markdown("</div>", unsafe_allow_html=True)
