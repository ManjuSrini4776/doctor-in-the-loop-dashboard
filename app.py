import json
import os
import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide",
)

# ---------------- LOAD JSON ----------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("Doctor review JSON file not found.")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# Safe getters
patient = data.get("patient_details", {})
doctor = data.get("assigned_doctor", {})
summary = data.get("structured_summary", {})
system = data.get("system_decisions", {})
short_summary = data.get("short_summary", "")

# ---------------- HEADER ----------------
st.markdown(
    """
    <h1 style='text-align:center;'>🩺 Doctor-in-the-Loop Clinical Dashboard</h1>
    <p style='text-align:center; color:gray;'>
    Evidence-based AI report validation with doctor oversight
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([1, 1])

# ==========================================================
# LEFT COLUMN – PATIENT + CLINICAL SUMMARY
# ==========================================================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient.get('patient_id', 'PREG_1023')}")
    st.write(f"**Age:** {patient.get('age', 28)}")
    st.write(f"**Gender:** {patient.get('gender', 'Female')}")
    st.write(f"**Clinical Context:** {patient.get('context', 'Pregnancy')}")

    st.divider()

    st.subheader("📄 Structured Clinical Summary")

    st.write(f"**Lab Parameter:** {summary.get('lab_parameter', 'Fasting Blood Sugar')}")
    st.write(f"**Patient Value:** {summary.get('patient_value', '92 mg/dL')}")
    st.write(f"**Guideline Reference:** {summary.get('guideline_reference', 'WHO Antenatal Care Guidelines')}")
    st.write(f"**Guideline Range:** {summary.get('guideline_range', '70–95 mg/dL')}")
    st.write(f"**AI Severity:** {summary.get('ai_severity', 'Normal')}")
    st.write(f"**Risk Level:** {summary.get('risk_level', 'Low')}")
    st.write(
        f"**Recommended Action:** {summary.get('recommended_action', 'Continue routine antenatal follow-up')}"
    )

    # Pregnancy special note
    if patient.get("context", "Pregnancy") == "Pregnancy":
        st.info(
            "🧪 Pregnancy case: Both **lab results** and **ultrasound findings** "
            "are considered during clinical triage."
        )

# ==========================================================
# RIGHT COLUMN – DOCTOR + DECISION
# ==========================================================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {doctor.get('name', 'Dr. Kavya')}")
    st.write(f"**Department:** {doctor.get('department', 'Obstetrics & Gynecology')}")
    st.write(
        f"**Routing Reason:** {doctor.get('routing_reason', 'Ordering doctor unavailable → routed to same department')}"
    )

    st.divider()

    st.subheader("✏️ Doctor Notes / Follow-up Instructions")
    doctor_notes = st.text_area(
        "Add follow-up details (next visit, ultrasound name, tests, etc.)",
        placeholder="Example: Next ultrasound – Anomaly Scan (Level-II) at 28 weeks",
    )

    st.divider()

    st.subheader("📋 Doctor-Facing Short Summary")
    st.info(short_summary)

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {system.get('guideline_validation', 'PASS')}")
    st.write(f"**Routing Decision:** {system.get('routing_decision', 'ALLOW_SUMMARY_GENERATION')}")

    st.divider()

    # ---------------- DOCTOR DECISION ----------------
    st.subheader("✅ Doctor Decision")

    if "final_decision" not in st.session_state:
        st.session_state.final_decision = None

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("✅ Approve"):
            st.session_state.final_decision = "APPROVED"

    with col_b:
        if st.button("❌ Reject"):
            st.session_state.final_decision = "REJECTED"

    # ---------------- AFTER DECISION ----------------
    if st.session_state.final_decision == "APPROVED":
        st.success("Decision recorded: APPROVED")

        st.subheader("📨 Patient Communication (Auto-Generated)")

        patient_message = f"""
Hello,

Your recent medical report has been reviewed by the doctor.

• Test: {summary.get('lab_parameter', 'Fasting Blood Sugar')}
• Result: {summary.get('patient_value', '92 mg/dL')}
• Status: Normal (Low risk)

Doctor’s Instructions:
{doctor_notes if doctor_notes else 'Continue routine antenatal follow-up.'}

Thank you.
"""

        st.text_area(
            "Message to Patient (SMS / WhatsApp)",
            patient_message,
            height=180,
        )

        st.info(
            "📌 In next module (NB-7), this message will be sent via **WhatsApp (PDF + text)** "
            "and **SMS gateway**."
        )

    elif st.session_state.final_decision == "REJECTED":
        st.error("Decision recorded: REJECTED")
        st.warning("Case will be escalated for manual doctor review.")
