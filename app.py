import json
import streamlit as st
from twilio.rest import Client

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# -------------------- TWILIO CONFIG --------------------
# ⚠️ Use Streamlit secrets in production
TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"  # Sandbox number
PATIENT_WHATSAPP_TO = "whatsapp:+91XXXXXXXXXX"  # Your verified number

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(text):
    message = client.messages.create(
        body=text,
        from_=TWILIO_WHATSAPP_FROM,
        to=PATIENT_WHATSAPP_TO
    )
    return message.sid

# -------------------- LOAD JSON --------------------
JSON_PATH = "pregnancy_abnormal.json"  # or pregnancy_normal.json

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -------------------- EXTRACT DATA --------------------
patient = data["patient_details"]
doctor = data["assigned_doctor"]
lab = data["lab_summary"]
ultrasound = data["ultrasound_summary"]
system = data["system_decisions"]

# -------------------- SESSION STATE --------------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# -------------------- LAYOUT --------------------
left, right = st.columns(2)

# ==================== LEFT ====================
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
    st.write(f"**Severity:** {lab['ai_severity']}")
    st.write(f"**Action:** {lab['recommended_action']}")

    st.divider()

    st.subheader("🖥️ Ultrasound Summary")
    st.write(ultrasound["clinical_note"])

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["doctor_facing_short_summary"])

# ==================== RIGHT ====================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Name:** {doctor['doctor_name']}")
    st.write(f"**Department:** {doctor['department']}")

    st.divider()

    st.subheader("⚙️ System Decisions")
    st.write(system["guideline_validation"])
    st.write(system["routing_decision"])

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

# -------------------- PATIENT COMMUNICATION --------------------
st.divider()
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision == "APPROVED":

    secure_link = f"https://doctor-in-the-loop-dashboard.streamlit.app/?patient_id={patient['patient_id']}"

    whatsapp_text = f"""
Hello,

Your medical report has been reviewed by the doctor.

Patient ID: {patient['patient_id']}
Clinical Context: {patient['clinical_context']}

Please view your report securely at the link below:
{secure_link}

Regards,
Hospital Care Team
"""

    st.success("Doctor approved the report.")
    st.text_area("WhatsApp Message to be sent", whatsapp_text, height=200)

    if st.button("📤 Send WhatsApp Message"):
        sid = send_whatsapp_message(whatsapp_text)
        st.success(f"WhatsApp sent successfully. SID: {sid}")

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor chose to edit the report. Patient communication is on hold.")

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Doctor rejected the report. No patient message will be sent.")

else:
    st.info("Awaiting doctor decision.")
