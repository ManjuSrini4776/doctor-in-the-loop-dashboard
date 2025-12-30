import streamlit as st
import json
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

# ---------------- HEADER ----------------
st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Doctor-approved AI medical reporting with secure patient access")

# ---------------- LOAD DATA ----------------
DATA_FILES = {
    "PREG_001": "pregnancy_normal.json",
    "PREG_002": "pregnancy_abnormal.json"
}

# ---------------- URL PARAM SUPPORT ----------------
query_params = st.query_params
url_patient_id = query_params.get("patient_id")

# ---------------- SIDEBAR PATIENT SELECT ----------------
st.sidebar.header("👤 Select Patient")

selected_patient = st.sidebar.selectbox(
    "Patient ID",
    options=["-- Select --"] + list(DATA_FILES.keys()),
    index=1 if url_patient_id in DATA_FILES else 0
)

# Priority: URL > Dropdown
patient_id = url_patient_id if url_patient_id in DATA_FILES else (
    selected_patient if selected_patient != "-- Select --" else None
)

if not patient_id:
    st.warning("Please select a patient from the sidebar.")
    st.stop()

# ---------------- LOAD PATIENT JSON ----------------
with open(DATA_FILES[patient_id]) as f:
    data = json.load(f)

patient = data["patient_details"]
doctor = data["doctor_details"]
reports = data["reports"]

# ---------------- SESSION STATE ----------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# ---------------- PATIENT DETAILS ----------------
st.subheader("👤 Patient Details")
st.write(f"**Patient ID:** {patient['patient_id']}")
st.write(f"**Age:** {patient['age']}")
st.write(f"**Gender:** {patient['gender']}")
st.write(f"**Clinical Context:** {patient['clinical_context']}")

# ---------------- LAB SUMMARY ----------------
st.subheader("📄 Lab Summary")
lab = reports["lab_summary"]
st.write(f"**Parameter:** {lab['parameter']}")
st.write(f"**Value:** {lab['value']}")
st.write(f"**Guideline Range:** {lab['guideline_range']}")
st.write(f"**AI Severity:** {lab['ai_severity']}")

# ---------------- ULTRASOUND ----------------
st.subheader("🖥️ Ultrasound Summary")
us = reports["ultrasound_summary"]
st.write(us["ai_note"])
st.write(us["clinical_note"])

# ---------------- DOCTOR SUMMARY ----------------
st.subheader("📝 Doctor-Facing Short Summary")
st.info(reports["doctor_summary"])

# ---------------- DOCTOR ACTION ----------------
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

# ---------------- PATIENT COMMUNICATION ----------------
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision == "APPROVED":
    st.success("Doctor approved the report.")
    final_message = reports["patient_message"]

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor chose to edit the report. Communication on hold.")
    st.stop()

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Report rejected. Patient will be contacted separately.")
    st.stop()
else:
    st.info("Awaiting doctor decision.")
    st.stop()

st.write(final_message)

# ---------------- FINAL JSON OUTPUT ----------------
final_output = {
    "patient_id": patient_id,
    "clinical_context": patient["clinical_context"],
    "doctor_decision": st.session_state.doctor_decision,
    "severity": lab["ai_severity"],
    "doctor_summary": reports["doctor_summary"],
    "final_patient_message": final_message
}

st.subheader("📄 Doctor-Approved Final Output (JSON)")
st.json(final_output)

st.download_button(
    "⬇️ Download Final Doctor Output JSON",
    json.dumps(final_output, indent=2),
    file_name="doctor_review_output.json"
)

# ---------------- WHATSAPP (SAFE MODE) ----------------
st.subheader("📎 WhatsApp Attachments Preview")

media_urls = []
if reports.get("lab_report_pdf"):
    media_urls.append(
        f"https://raw.githubusercontent.com/ManjuSrini4776/doctor-in-the-loop-dashboard/main/{reports['lab_report_pdf']}"
    )
if reports.get("ultrasound_report_pdf"):
    media_urls.append(
        f"https://raw.githubusercontent.com/ManjuSrini4776/doctor-in-the-loop-dashboard/main/{reports['ultrasound_report_pdf']}"
    )

for url in media_urls:
    st.write(f"📄 {url}")

# ---------------- OPTIONAL WHATSAPP SEND ----------------
def send_whatsapp_message(text, media_urls=None):
    try:
        client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"]
        )
        message = client.messages.create(
            body=text,
            from_=os.environ["TWILIO_WHATSAPP_FROM"],
            to=os.environ["TWILIO_WHATSAPP_TO"],
            media_url=media_urls
        )
        return message.sid
    except TwilioRestException as e:
        return f"Twilio Error: {e}"

if st.button("📤 Send WhatsApp Message"):
    sid = send_whatsapp_message(final_message, media_urls)
    st.info(f"WhatsApp status: {sid}")
