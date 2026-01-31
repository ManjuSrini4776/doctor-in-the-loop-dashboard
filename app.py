import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Review Dashboard",
    layout="wide"
)

st.title("Doctor-in-the-Loop Clinical Review Dashboard")
st.caption("Doctor-approved AI medical reporting with controlled patient communication")

# ==================== SIDEBAR ====================
st.sidebar.header("Case Selection")

case_choice = st.sidebar.selectbox(
    "Select case",
    ["Latest CT Brain Case"]
)

# ==================== JSON SOURCE ====================
DATA_PATH = Path("data/ct_demo_with_rag.json")

if not DATA_PATH.exists():
    st.error("Required CT review JSON not found: data/ct_demo_with_rag.json")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================
patient = data.get("patient_details", {})
ct_out = data.get("ct_model_output", {})
fusion = data.get("ai_severity_fusion", {})
imaging = data.get("imaging_evidence", {})

validation_decision = data.get("validation_decision", "-")
validation_reason   = data.get("validation_reason", "-")
rag_imaging_sources = data.get("rag_imaging_sources", [])
rag_pathway_sources = data.get("rag_pathway_sources", [])
doctor_summary      = data.get("doctor_facing_summary", "-")

# ==================== SESSION ====================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

if "case_status" not in st.session_state:
    st.session_state.case_status = "PENDING"

if "timeline" not in st.session_state:
    st.session_state.timeline = []

def log_event(msg):
    st.session_state.timeline.append(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}"
    )

# ==================== STATUS BAR ====================
if st.session_state.case_status == "PENDING":
    st.warning("Case status: Pending doctor review")
elif st.session_state.case_status == "APPROVED":
    st.success("Case status: Approved by doctor")
elif st.session_state.case_status == "REJECTED":
    st.error("Case status: Rejected by doctor")

# ==================== MAIN TABS ====================
tab_overview, tab_evidence, tab_rag, tab_action, tab_comm = st.tabs(
    [
        "Overview",
        "Clinical Evidence",
        "Guideline Summary",
        "Doctor Decision",
        "Patient Communication"
    ]
)

# =====================================================
# OVERVIEW
# =====================================================
with tab_overview:

    st.subheader("Patient overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Patient ID:", patient.get("patient_id", "-"))
        st.write("Modality:", patient.get("modality", "CT Brain"))

    with col2:
        st.metric(
            label="CT AI prediction",
            value=ct_out.get("prediction", "-")
        )

    st.divider()

    try:
        conf = round(float(ct_out.get("confidence", 0)) * 100, 2)
    except:
        conf = "-"

    st.subheader("AI model output")
    st.write("Prediction:", ct_out.get("prediction", "-"))
    st.write("Confidence:", conf, "%")

    st.divider()

    st.subheader("Final severity (fusion engine)")
    st.write("Derived severity:", fusion.get("derived_severity", "-"))
    st.write("Patient context:", patient.get("context", "-"))

    st.divider()

    st.subheader("Guideline and safety validation (CT-RAG pipeline)")
    st.write("Validation decision:", validation_decision)
    st.write("Reason:", validation_reason)

    st.divider()

    st.subheader("Case activity log")

    if len(st.session_state.timeline) == 0:
        st.write("No activity yet.")
    else:
        for t in st.session_state.timeline:
            st.write("-", t)

# =====================================================
# CLINICAL EVIDENCE
# =====================================================
with tab_evidence:

    st.subheader("Clinical evidence for doctor verification")

    st.write("Modality: CT Brain")
    st.write("CT image ID:", imaging.get("image_id", "-"))
    st.write("Prediction:", ct_out.get("prediction", "-"))
    st.write("Confidence:", conf, "%")

    st.divider()

    st.subheader("Imaging evidence references")

    if rag_imaging_sources:
        for s in rag_imaging_sources:
            st.write("-", s)
    else:
        st.write("No imaging references available.")

# =====================================================
# GUIDELINE SUMMARY (RAG)
# =====================================================
with tab_rag:

    st.subheader("Doctor-facing guideline grounded summary")

    st.write(doctor_summary)

    st.divider()

    with st.expander("Retrieved guideline evidence (audit view)"):

        st.markdown("Imaging guideline sources")
        if rag_imaging_sources:
            for s in rag_imaging_sources:
                st.write("-", s)
        else:
            st.write("None")

        st.markdown("Clinical pathway sources")
        if rag_pathway_sources:
            for s in rag_pathway_sources:
                st.write("-", s)
        else:
            st.write("None")

# =====================================================
# DOCTOR DECISION
# =====================================================
with tab_action:

    st.subheader("Doctor decision and verification")

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
        log_event("Doctor edited the clinical summary")
        st.success("Edited summary saved.")

    if approve:
        st.session_state.case_status = "APPROVED"
        st.session_state.doctor_decision = "APPROVED"
        log_event("Doctor approved the case")
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

        st.divider()
        st.subheader("Doctor approved output")
        st.json(final_output)

        st.download_button(
            label="Download doctor approved JSON",
            data=json.dumps(final_output, indent=4),
            file_name=f"{patient.get('patient_id','CT')}_doctor_output.json",
            mime="application/json"
        )

    if reject:
        if reject_reason.strip() == "":
            st.error("Rejection reason is required.")
        else:
            st.session_state.case_status = "REJECTED"
            st.session_state.doctor_decision = "REJECTED"
            log_event("Doctor rejected the case")
            st.error("Case rejected.")

# =====================================================
# PATIENT COMMUNICATION
# =====================================================
with tab_comm:

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
            "Patient message preview (SMS / WhatsApp)",
            patient_message,
            height=220
        )
