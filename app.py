import json
import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# -------------------- LOAD JSON --------------------
JSON_PATH = "pregnancy_abnormal.json"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -------------------- EXTRACT SECTIONS --------------------
patient = data["patient_details"]
doctor = data["assigned_doctor"]
lab = data["lab_summary"]
ultrasound = data["ultrasound_summary"]
system = data["system_decisions"]
reports = data["hospital_reports"]

patient_context = patient["clinical_context"]

# -------------------- SESSION STATE --------------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = "PENDING"

# -------------------- LAYOUT --------------------
left, right = st.columns(2)

# ==================== LEFT COLUMN ====================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient['patient_id']}")
    st.write(f"**Age:** {patient['age']}")
    st.write(f"**Gender:** {patient['gender']}")
    st.write(f"**Clinical Context:** {patient_context}")

    st.divider()

    # -------- LAB SUMMARY --------
    if patient_context in ["PREGNANCY", "CHRONIC", "GENERAL"]:
        st.subheader("📄 Lab Summary")
        st.write(f"**Lab Parameter:** {lab['lab_parameter']}")
        st.write(f"**Patient Value:** {lab['patient_value']}")
        st.write(f"**Guideline Reference:** {lab['guideline_reference']}")
        st.write(f"**Guideline Range:** {lab['guideline_range']}")
        st.write(f"**AI Severity:** {lab['ai_severity']}")
        st.write(f"**Risk Level:** {lab['risk_level']}")
        st.write(f"**Recommended Action:** {lab['recommended_action']}")

    st.divider()

    # -------- ULTRASOUND SUMMARY (PREGNANCY ONLY) --------
    if patient_context == "PREGNANCY":
        st.subheader("🖥️ Ultrasound Summary")
        st.write(f"• **Last Ultrasound:** {ultrasound['last_ultrasound']}")
        st.write(f"• **AI Note:** {ultrasound['ai_note']}")
        st.write(f"• **Clinical Note:** {ultrasound['clinical_note']}")

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["doctor_facing_short_summary"])

# ==================== RIGHT COLUMN ====================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {doctor['doctor_name']}")
    st.write(f"**Department:** {doctor['department']}")
    st.write(f"**Routing Reason:** {doctor['routing_reason']}")

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {system['guideline_validation']}")
    st.write(f"**Routing Decision:** {system['routing_decision']}")

    st.divider()

    st.subheader("✏️ Doctor Follow-up Instructions")
    st.write(f"**Next Visit:** {data['doctor_followup_instructions']['next_visit']}")
    st.write(f"**Next Ultrasound:** {data['doctor_followup_instructions']['next_ultrasound']}")

    st.divider()

    st.subheader("📎 Reports to be Shared with Patient")
    if reports["lab_report_pdf"]:
        st.write(f"📄 Lab Report: {reports['lab_report_pdf']}")
    if reports["ultrasound_report_pdf"]:
        st.write(f"📄 Ultrasound Report: {reports['ultrasound_report_pdf']}")

    st.info("Reports will be shared with the patient only after doctor approval.")

# ==================== DOCTOR ACTION ====================
st.divider()
st.subheader("✏️ Doctor Action")

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

# ==================== PATIENT COMMUNICATION ====================
st.divider()
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision == "APPROVED":
    st.success("Doctor approved the report.")
    st.info(
        "Your pregnancy scan and lab reports are normal. "
        "The baby is developing well. Please continue regular antenatal check-ups."
    )
    st.caption("This message will be sent via WhatsApp / SMS in the next phase.")

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor chose to edit the report. Patient communication is on hold.")

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Report rejected. Patient communication is blocked.")

else:
    st.info("Awaiting doctor decision. Patient communication is locked.")

