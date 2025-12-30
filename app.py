import json
import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# -------------------- READ PATIENT ID FROM URL --------------------
query_params = st.query_params
patient_id = query_params.get("patient_id")

if not patient_id:
    st.warning("No patient ID provided in the URL.")
    st.stop()

# -------------------- MAP PATIENT ID TO JSON --------------------
if patient_id == "PREG_001":
    JSON_PATH = "pregnancy_normal.json"
elif patient_id == "PREG_002":
    JSON_PATH = "pregnancy_abnormal.json"
else:
    st.error("Invalid or unknown patient ID.")
    st.stop()

# -------------------- LOAD JSON --------------------
with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -------------------- EXTRACT DATA --------------------
patient = data["patient_details"]
doctor = data["assigned_doctor"]
lab = data["lab_summary"]
ultrasound = data["ultrasound_summary"]
system = data["system_decisions"]
doctor_summary = data["doctor_facing_short_summary"]
followup = data["doctor_followup_instructions"]
reports = data["hospital_reports"]

# -------------------- SESSION STATE --------------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# -------------------- LAYOUT --------------------
left, right = st.columns(2)

# ==================== LEFT COLUMN ====================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient['patient_id']}")
    st.write(f"**Age:** {patient['age']}")
    st.write(f"**Gender:** {patient['gender']}")
    st.write(f"**Clinical Context:** {patient['clinical_context']}")

    st.divider()

    st.subheader("📄 Lab Summary")
    st.write(f"**Parameter:** {lab['lab_parameter']}")
    st.write(f"**Value:** {lab['patient_value']}")
    st.write(f"**Guideline Range:** {lab['guideline_range']}")
    st.write(f"**AI Severity:** {lab['ai_severity']}")
    st.write(f"**Risk Level:** {lab['risk_level']}")
    st.write(f"**Recommended Action:** {lab['recommended_action']}")

    st.divider()

    st.subheader("🖥️ Ultrasound Summary")
    st.write(f"**Last Scan:** {ultrasound['last_ultrasound']}")
    st.write(f"**AI Note:** {ultrasound['ai_note']}")
    st.write(f"**Clinical Note:** {ultrasound['clinical_note']}")

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(doctor_summary)

# ==================== RIGHT COLUMN ====================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Name:** {doctor['doctor_name']}")
    st.write(f"**Department:** {doctor['department']}")
    st.write(f"**Routing Reason:** {doctor['routing_reason']}")

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {system['guideline_validation']}")
    st.write(f"**Routing Decision:** {system['routing_decision']}")

    st.divider()

    st.subheader("✏️ Doctor Follow-up Instructions")
    st.write(f"**Next Visit:** {followup['next_visit']}")
    st.write(f"**Next Ultrasound:** {followup['next_ultrasound']}")

    st.divider()

    st.subheader("📎 Reports Available in Hospital System")
    if reports.get("lab_report_pdf"):
        st.write(f"📄 Lab Report: {reports['lab_report_pdf']}")
    if reports.get("ultrasound_report_pdf"):
        st.write(f"📄 Ultrasound Report: {reports['ultrasound_report_pdf']}")

# -------------------- DOCTOR ACTION --------------------
st.divider()
st.subheader("✏️ Doctor Action")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✅ Approve"):
        st.session_state.doctor_decision = "APPROVED"

with c2:
    if st.button("✏️ Edit"):
        st.session_state.doctor_decision = "EDIT"

with c3:
    if st.button("❌ Reject"):
        st.session_state.doctor_decision = "REJECTED"

# -------------------- PATIENT COMMUNICATION (PREVIEW ONLY) --------------------
st.divider()
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision == "APPROVED":
    secure_link = f"https://doctor-in-the-loop-dashboard.streamlit.app/?patient_id={patient_id}"

    st.success("Doctor approved the report.")

    st.text_area(
        "WhatsApp Message Preview",
        f"""
Hello,

Your medical report has been reviewed by the doctor.

Patient ID: {patient['patient_id']}
Clinical Context: {patient['clinical_context']}

Please view your report securely at the link below:
{secure_link}

Regards,
Hospital Care Team
""",
        height=200
    )

    st.info("WhatsApp notification will be sent in production using approved templates.")

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor chose to edit the report. Patient communication is on hold.")

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Doctor rejected the report. No patient communication will be sent.")

else:
    st.info("Awaiting doctor decision.")
