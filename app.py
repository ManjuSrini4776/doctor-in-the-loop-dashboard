import json
import os
import streamlit as st
from datetime import datetime

# =============================
# Page Configuration
# =============================
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================
# Load JSON Safely
# =============================
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("❌ doctor_review_output.json not found. Please upload it.")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# =============================
# Extract Core Sections Safely
# =============================
patient = data.get("patient_details", {})
doctor = data.get("assigned_doctor", {})
summary = data.get("structured_summary", {})
system = data.get("system_decisions", {})
short_summary = data.get("short_summary", "")

# =============================
# Automatic Hospital Report Fetch
# (Simulation of LIS / PACS)
# =============================
patient_id = patient.get("patient_id", "UNKNOWN")
clinical_context = patient.get("clinical_context", "GENERAL")

HOSPITAL_STORAGE = "hospital_storage"

lab_pdf = None
usg_pdf = None
ct_pdf = None

if clinical_context == "Pregnancy":
    lab_pdf = f"{HOSPITAL_STORAGE}/{patient_id}_LAB_REPORT.pdf"
    usg_pdf = f"{HOSPITAL_STORAGE}/{patient_id}_ULTRASOUND_REPORT.pdf"

elif clinical_context == "GENERAL":
    ct_pdf = f"{HOSPITAL_STORAGE}/{patient_id}_CT_REPORT.pdf"
    lab_pdf = f"{HOSPITAL_STORAGE}/{patient_id}_LAB_REPORT.pdf"

# =============================
# Header
# =============================
st.markdown(
    """
    <h1 style='color:#7dd3fc;'>🩺 Doctor-in-the-Loop Clinical Dashboard</h1>
    <p style='color:gray;'>Evidence-based AI report validation with doctor oversight</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# =============================
# Layout
# =============================
left, right = st.columns([1.3, 1])

# =============================
# LEFT COLUMN — PATIENT VIEW
# =============================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient.get('patient_id', 'PREG_1023')}")
    st.write(f"**Age:** {patient.get('age', 28)}")
    st.write(f"**Gender:** {patient.get('gender', 'Female')}")
    st.write(f"**Clinical Context:** {clinical_context}")

    st.divider()

    st.subheader("📄 Structured Clinical Summary")

    # ---- LAB SUMMARY ----
    st.markdown("**🧪 Lab Report**")
    st.write(f"- **Lab Parameter:** {summary.get('lab_parameter', 'Fasting Blood Sugar')}")
    st.write(f"- **Patient Value:** {summary.get('patient_value', '92 mg/dL')}")
    st.write(f"- **Guideline Reference:** {summary.get('guideline_reference', 'WHO Antenatal Care Guidelines')}")
    st.write(f"- **Guideline Range:** {summary.get('guideline_range', '70–95 mg/dL')}")
    st.write(f"- **AI Severity:** {summary.get('ai_severity', 'Normal')}")
    st.write(f"- **Risk Level:** {summary.get('risk_level', 'Low')}")
    st.write(f"- **Recommended Action:** {summary.get('recommended_action', 'Continue routine antenatal follow-up')}")

    # ---- ULTRASOUND SUMMARY (Pregnancy) ----
    if clinical_context == "Pregnancy":
        st.divider()
        st.markdown("**🖥️ Ultrasound Summary**")
        st.write("- **Purpose:** Pregnancy monitoring")
        st.write("- **AI Usage:** Triage support only (non-diagnostic)")
        st.write("- **Clinical Status:** No abnormal indicators detected")

    st.divider()

    st.subheader("📎 Hospital Reports (Auto-fetched)")

    if lab_pdf:
        st.write(f"🧪 **Lab Report:** {lab_pdf}")
    if usg_pdf:
        st.write(f"🖥️ **Ultrasound Report:** {usg_pdf}")
    if ct_pdf:
        st.write(f"🧠 **CT Scan Report:** {ct_pdf}")

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(
        short_summary
        if short_summary
        else "Patient values are within guideline range. No immediate intervention required."
    )

# =============================
# RIGHT COLUMN — DOCTOR VIEW
# =============================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {doctor.get('doctor_name', 'Dr. Kavya')}")
    st.write(f"**Department:** {doctor.get('department', 'Obstetrics & Gynecology')}")
    st.write(
        f"**Routing Reason:** {doctor.get('routing_reason', 'Ordering doctor unavailable → routed to same department')}"
    )

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {system.get('guideline_validation', 'PASS')}")
    st.write(f"**Routing Decision:** {system.get('routing_decision', 'ALLOW_SUMMARY_GENERATION')}")

    st.divider()

    st.subheader("✏️ Doctor Notes / Follow-up Instructions")
    follow_up_notes = st.text_area(
        "Add follow-up instructions (next visit, ultrasound, tests, etc.)",
        placeholder="Example: Next ultrasound – Growth Scan at 28 weeks",
        height=120
    )

    st.divider()

    st.subheader("✅ Doctor Decision")

    col1, col2 = st.columns(2)

    if "decision" not in st.session_state:
        st.session_state.decision = None

    with col1:
        if st.button("✔ Approve"):
            st.session_state.decision = "APPROVED"

    with col2:
        if st.button("❌ Reject"):
            st.session_state.decision = "REJECTED"

    # =============================
    # After Decision Logic
    # =============================
    if st.session_state.decision == "APPROVED":
        st.success("Decision recorded: APPROVED")

        st.subheader("📨 Patient Communication (Auto-generated)")

        patient_message = f"""
Dear Patient,

Your hospital lab and imaging reports have been reviewed and approved by the doctor.

• Key Lab Result: {summary.get('patient_value', '92 mg/dL')} (Normal)
• Risk Level: {summary.get('risk_level', 'Low')}

Doctor Instructions:
{follow_up_notes if follow_up_notes else "Continue routine antenatal follow-up."}

Please refer to the attached original hospital reports.

— Hospital Care Team
"""

        st.text_area(
            "Patient Message Preview (SMS / WhatsApp)",
            patient_message,
            height=230
        )

        st.subheader("📎 Reports to be Shared with Patient")
        if lab_pdf:
            st.write(f"🧪 Lab Report Attached: {lab_pdf}")
        if usg_pdf:
            st.write(f"🖥️ Ultrasound Report Attached: {usg_pdf}")
        if ct_pdf:
            st.write(f"🧠 CT Report Attached: {ct_pdf}")

        st.info("📌 Next Phase: WhatsApp & SMS delivery")

    elif st.session_state.decision == "REJECTED":
        st.error("Decision recorded: REJECTED")
        st.warning("Case sent for manual review. No patient communication generated.")

# =============================
# Footer
# =============================
st.divider()
st.caption("Doctor-in-the-Loop | Evidence-based | Safe AI Clinical System")
