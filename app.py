import json
import streamlit as st
from pathlib import Path

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Doctor-approved AI medical reporting with secure patient access")

# -------------------- PATIENT FILE MAP --------------------
PATIENT_FILES = {
    "PREG_001 (Normal)": "pregnancy_normal.json",
    "PREG_002 (Abnormal)": "pregnancy_abnormal.json"
}

# -------------------- SIDEBAR --------------------
st.sidebar.header("👤 Select Patient")
patient_choice = st.sidebar.selectbox(
    "Patient ID",
    list(PATIENT_FILES.keys())
)

json_file = PATIENT_FILES[patient_choice]

if not Path(json_file).exists():
    st.error(f"JSON file not found: {json_file}")
    st.stop()

# -------------------- LOAD JSON --------------------
with open(json_file, "r") as f:
    data = json.load(f)

# -------------------- SAFE EXTRACTION --------------------
patient = data.get("patient_details", {})
doctor = data.get("assigned_doctor", {})
lab = data.get("lab_summary", {})
ultrasound = data.get("ultrasound_summary", {})
system = data.get("system_decisions", {})
reports = data.get("hospital_reports", {})

# -------------------- LAYOUT --------------------
left, right = st.columns(2)

# ==================== LEFT ====================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient.get('patient_id', '-')}")
    st.write(f"**Age:** {patient.get('age', '-')}")
    st.write(f"**Gender:** {patient.get('gender', '-')}")
    st.write(f"**Clinical Context:** {patient.get('clinical_context', '-')}")

    st.divider()

    if lab:
        st.subheader("📄 Lab Summary")
        st.write(f"**Parameter:** {lab.get('lab_parameter', '-')}")
        st.write(f"**Patient Value:** {lab.get('patient_value', '-')}")
        st.write(f"**Guideline:** {lab.get('guideline_reference', '-')}")
        st.write(f"**Range:** {lab.get('guideline_range', '-')}")
        st.write(f"**AI Severity:** {lab.get('ai_severity', '-')}")
        st.write(f"**Risk Level:** {lab.get('risk_level', '-')}")
        st.write(f"**Action:** {lab.get('recommended_action', '-')}")

    st.divider()

    if ultrasound:
        st.subheader("🖥️ Ultrasound Summary")
        st.write(f"**Last Scan:** {ultrasound.get('last_ultrasound', '-')}")
        st.write(f"**AI Note:** {ultrasound.get('ai_note', '-')}")
        st.write(f"**Clinical Note:** {ultrasound.get('clinical_note', '-')}")

    st.divider()

    st.subheader("📝 Doctor-Facing Summary")
    st.info(data.get("doctor_facing_short_summary", "Not available"))

# ==================== RIGHT ====================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {doctor.get('doctor_name', '-')}")
    st.write(f"**Department:** {doctor.get('department', '-')}")
    st.write(f"**Routing Reason:** {doctor.get('routing_reason', '-')}")

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {system.get('guideline_validation', '-')}")
    st.write(f"**Routing Decision:** {system.get('routing_decision', '-')}")

    st.divider()

    st.subheader("✏️ Follow-up Instructions")
    followup = data.get("doctor_followup_instructions", {})
    st.write(f"**Next Visit:** {followup.get('next_visit', '-')}")
    st.write(f"**Next Ultrasound:** {followup.get('next_ultrasound', '-')}")

    st.divider()

    st.subheader("📎 Reports")
    if reports.get("lab_report_pdf"):
        st.write(f"📄 Lab Report: {reports['lab_report_pdf']}")
    if reports.get("ultrasound_report_pdf"):
        st.write(f"📄 Ultrasound Report: {reports['ultrasound_report_pdf']}")

    st.info("Reports will be shared with the patient only after doctor approval.")

    st.divider()
st.subheader("✏️ Doctor Action")

# Initialize session state
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Approve"):
        st.session_state.doctor_decision = "APPROVED"

with col2:
    if st.button("✏️ Edit"):
        st.session_state.doctor_decision = "EDIT"

with col3:
    if st.button("❌ Reject"):
        st.session_state.doctor_decision = "REJECTED"
st.divider()
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision is None:
    st.warning("Awaiting doctor decision. Patient communication is locked.")

elif st.session_state.doctor_decision == "APPROVED":
    st.success("Doctor approved the report.")
    st.info(
        "Your pregnancy report has been reviewed by the doctor. "
        "Please follow the recommended medical advice and attend follow-up visits as scheduled."
    )

elif st.session_state.doctor_decision == "EDIT":
    st.warning(
        "Doctor chose to edit the report. Patient communication is temporarily on hold."
    )

elif st.session_state.doctor_decision == "REJECTED":
    st.error(
        "Doctor rejected the AI report. No patient communication will be sent."
    )

