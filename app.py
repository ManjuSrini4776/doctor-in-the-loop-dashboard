import json
import os
import streamlit as st
from datetime import datetime

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Load JSON safely
# -----------------------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("❌ doctor_review_output.json not found. Please upload it.")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -----------------------------
# Extract sections safely
# -----------------------------
patient = data.get("patient_details", {})
doctor = data.get("assigned_doctor", {})
summary = data.get("structured_summary", {})
system = data.get("system_decisions", {})
short_summary = data.get("short_summary", "")

# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <h1 style='color:#7dd3fc;'>🩺 Doctor-in-the-Loop Clinical Dashboard</h1>
    <p style='color:gray;'>Evidence-based AI report validation with doctor oversight</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# -----------------------------
# Layout: Left (Patient) | Right (Doctor)
# -----------------------------
left, right = st.columns([1.2, 1])

# =============================
# LEFT COLUMN – PATIENT SIDE
# =============================
with left:
    st.subheader("👤 Patient Details")

    st.write(f"**Patient ID:** {patient.get('patient_id', 'PREG_1023')}")
    st.write(f"**Age:** {patient.get('age', 28)}")
    st.write(f"**Gender:** {patient.get('gender', 'Female')}")
    st.write(f"**Clinical Context:** {patient.get('clinical_context', 'Pregnancy')}")

    st.divider()

    st.subheader("📄 Structured Clinical Summary")

    # --- LAB REPORT ---
    st.markdown("**🧪 Lab Report**")
    st.write(f"- **Lab Parameter:** {summary.get('lab_parameter', 'Fasting Blood Sugar')}")
    st.write(f"- **Patient Value:** {summary.get('patient_value', '92 mg/dL')}")
    st.write(f"- **Guideline Reference:** {summary.get('guideline_reference', 'WHO Antenatal Care Guidelines')}")
    st.write(f"- **Guideline Range:** {summary.get('guideline_range', '70–95 mg/dL')}")
    st.write(f"- **AI Severity:** {summary.get('ai_severity', 'Normal')}")
    st.write(f"- **Risk Level:** {summary.get('risk_level', 'Low')}")
    st.write(f"- **Recommended Action:** {summary.get('recommended_action', 'Continue routine antenatal follow-up')}")

    st.divider()

    # --- ULTRASOUND REPORT (Pregnancy) ---
    if patient.get("clinical_context", "Pregnancy") == "Pregnancy":
        st.markdown("**🖥️ Ultrasound Summary**")
        st.write("- **Last Ultrasound:** Normal fetal anatomy scan")
        st.write("- **AI Note:** Ultrasound used for triage support only")
        st.write("- **Clinical Note:** No abnormal indicators detected")

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(
        short_summary
        if short_summary
        else "Patient values are within guideline range. No immediate intervention required."
    )

# =============================
# RIGHT COLUMN – DOCTOR SIDE
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

    # -----------------------------
    # Doctor Notes (Editable)
    # -----------------------------
    st.subheader("✏️ Doctor Notes / Follow-up Instructions")

    follow_up_notes = st.text_area(
        "Add follow-up instructions (next visit, ultrasound, tests, etc.)",
        placeholder="Example: Next ultrasound – Growth Scan at 28 weeks",
        height=120
    )

    st.divider()

    # -----------------------------
    # Doctor Decision
    # -----------------------------
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

    # -----------------------------
    # After Decision Logic
    # -----------------------------
    if st.session_state.decision == "APPROVED":
        st.success("Decision recorded: APPROVED")

        st.subheader("📨 Patient Communication (Auto-generated)")

        patient_message = f"""
Dear Patient,

Your recent lab report has been reviewed and approved by the doctor.

• Fasting Blood Sugar: 92 mg/dL (Normal)
• Risk Level: Low

Doctor Instructions:
{follow_up_notes if follow_up_notes else "Continue routine antenatal follow-up."}

Please visit the hospital if you experience any unusual symptoms.

— Hospital Care Team
"""

        st.text_area(
            "Patient Message Preview (SMS / WhatsApp)",
            patient_message,
            height=220
        )

        st.info("📌 In next phase, this message will be sent via WhatsApp & SMS.")

    elif st.session_state.decision == "REJECTED":
        st.error("Decision recorded: REJECTED")
        st.warning("Case sent for manual review. No patient message generated.")

# -----------------------------
# Footer
# -----------------------------
st.divider()
st.caption("Doctor-in-the-Loop | Evidence-based | Safe AI Clinical System")
