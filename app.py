import json
import streamlit as st
from twilio.rest import Client

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Doctor-approved AI reporting & patient communication")

# --------------------------------------------------
# LOAD SCENARIO JSON
# --------------------------------------------------
JSON_PATH = "pregnancy_abnormal.json"  # switch to pregnancy_normal.json if needed

with open(JSON_PATH, "r") as f:
    data = json.load(f)

patient = data["patient_details"]
doctor = data["assigned_doctor"]
lab = data["lab_summary"]
ultrasound = data["ultrasound_summary"]
system = data["system_decisions"]
reports = data["hospital_reports"]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = "PENDING"

if "final_output" not in st.session_state:
    st.session_state.final_output = None

# --------------------------------------------------
# TWILIO SENDER
# --------------------------------------------------
def send_whatsapp(message_body, media_urls):
    client = Client(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"]
    )

    message = client.messages.create(
        from_=st.secrets["TWILIO_WHATSAPP_FROM"],
        to=st.secrets["TWILIO_WHATSAPP_TO"],
        body=message_body,
        media_url=media_urls
    )
    return message.sid

# --------------------------------------------------
# LAYOUT
# --------------------------------------------------
left, right = st.columns(2)

# ---------------- LEFT ----------------
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {patient['patient_id']}")
    st.write(f"**Age:** {patient['age']}")
    st.write(f"**Gender:** {patient['gender']}")
    st.write(f"**Clinical Context:** {patient['clinical_context']}")

    st.divider()

    st.subheader("📄 Lab Summary")
    for k, v in lab.items():
        st.write(f"**{k.replace('_',' ').title()}:** {v}")

    if patient["clinical_context"] == "PREGNANCY":
        st.divider()
        st.subheader("🖥️ Ultrasound Summary")
        for k, v in ultrasound.items():
            st.write(f"**{k.replace('_',' ').title()}:** {v}")

    st.divider()
    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["doctor_facing_short_summary"])

# ---------------- RIGHT ----------------
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Name:** {doctor['doctor_name']}")
    st.write(f"**Department:** {doctor['department']}")
    st.write(f"**Routing Reason:** {doctor['routing_reason']}")

    st.divider()

    st.subheader("⚙️ System Decisions")
    for k, v in system.items():
        st.write(f"**{k.replace('_',' ').title()}:** {v}")

    st.divider()
    st.subheader("📎 Reports")
    for _, v in reports.items():
        if v:
            st.write(f"📄 {v}")

# --------------------------------------------------
# DOCTOR ACTION
# --------------------------------------------------
st.divider()
st.subheader("✏️ Doctor Action")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("✅ Approve"):
        st.session_state.doctor_decision = "APPROVED"

        final_patient_message = (
            "Your pregnancy scan and lab reports are normal. "
            "The baby is developing well. Please continue regular antenatal check-ups."
            if lab["ai_severity"] == "NORMAL"
            else
            "Your pregnancy report shows some findings that need closer follow-up. "
            "The doctor has reviewed the report and will guide you on the next steps. "
            "Please attend the recommended follow-up visit."
        )

        st.session_state.final_output = {
            "patient_id": patient["patient_id"],
            "clinical_context": patient["clinical_context"],
            "doctor_decision": "APPROVED",
            "severity": lab["ai_severity"],
            "doctor_summary": data["doctor_facing_short_summary"],
            "final_patient_message": final_patient_message
        }

with c2:
    if st.button("✏️ Edit"):
        st.session_state.doctor_decision = "EDIT"

with c3:
    if st.button("❌ Reject"):
        st.session_state.doctor_decision = "REJECTED"

# --------------------------------------------------
# PATIENT COMMUNICATION
# --------------------------------------------------
st.divider()
st.subheader("📲 Patient Communication")

if st.session_state.doctor_decision == "APPROVED":

    final_json = st.session_state.final_output
    st.success("Doctor approved the report.")

    # ---- FINAL JSON ----
    st.subheader("📄 Doctor-Approved Final Output (JSON)")
    st.json(final_json)

    st.download_button(
        "⬇️ Download Final Doctor Output JSON",
        json.dumps(final_json, indent=2),
        file_name=f"final_doctor_output_{patient['patient_id']}.json",
        mime="application/json"
    )

    # ---- WHATSAPP MESSAGE ----
    st.subheader("📱 WhatsApp Message Preview")

    whatsapp_text = f"""
Hello,

This is an update regarding your recent hospital visit.

Patient ID: {final_json['patient_id']}
Clinical Context: Pregnancy

Doctor’s Message:
{final_json['final_patient_message']}

Attached Reports:
• Lab Report
• Ultrasound Report

Please attend the recommended follow-up visit.

Regards,
Hospital Care Team
""".strip()

    st.text_area("Message to be sent", whatsapp_text, height=240)

    # ---- ATTACHMENTS ----
    st.subheader("📎 WhatsApp Attachments Preview")

    media_urls = []

    if reports.get("lab_report_pdf"):
    media_urls.append(
        "https://raw.githubusercontent.com/ManjuSrini4776/doctor-in-the-loop-dashboard/main/lab_report_preg_002.pdf"
    )

if reports.get("ultrasound_report_pdf"):
    media_urls.append(
        "https://raw.githubusercontent.com/ManjuSrini4776/doctor-in-the-loop-dashboard/main/ultrasound_report_preg_002.pdf"
    )


    for url in media_urls:
        st.write(f"📄 {url}")

    # ---- SEND ----
    if st.button("📤 Send WhatsApp Message"):
        sid = send_whatsapp(whatsapp_text, media_urls)
        st.success(f"WhatsApp sent successfully. SID: {sid}")

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor chose to edit the report. Patient communication is on hold.")

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Report rejected. Patient communication blocked.")

else:
    st.info("Awaiting doctor decision.")
