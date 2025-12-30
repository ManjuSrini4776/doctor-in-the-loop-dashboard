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
# Switch between pregnancy_normal.json / pregnancy_abnormal.json
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

# -------------------- SAVE FUNCTION --------------------
def save_final_doctor_output(final_data, filename):
    with open(filename, "w") as f:
        json.dump(final_data, f, indent=2)

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
    st.subheader("📄 Lab Summary")
    st.write(f"**Lab Parameter:** {lab['lab_parameter']}")
    st.write(f"**Patient Value:** {lab['patient_value']}")
    st.write(f"**Guideline Reference:** {lab['guideline_reference']}")
    st.write(f"**Guideline Range:** {lab['guideline_range']}")
    st.write(f"**AI Severity:** {lab['ai_severity']}")
    st.write(f"**Risk Level:** {lab['risk_level']}")
    st.write(f"**Recommended Action:** {lab['recommended_action']}")

    st.divider()

    # -------- ULTRASOUND (PREGNANCY ONLY) --------
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

    st.subheader("📎 Reports to be Shared with Patient")
    if reports.get("lab_report_pdf"):
        st.write(f"📄 Lab Report: {reports['lab_report_pdf']}")
    if reports.get("ultrasound_report_pdf"):
        st.write(f"📄 Ultrasound Report: {reports['ultrasound_report_pdf']}")

    st.info("Reports will be shared only after doctor approval.")

# ==================== DOCTOR ACTION ====================
st.divider()
st.subheader("✏️ Doctor Action")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Approve"):
        st.session_state.doctor_decision = "APPROVED"

        final_output = {
            "patient_id": patient["patient_id"],
            "clinical_context": patient_context,
            "doctor_decision": "APPROVED",
            "severity": lab["ai_severity"],
            "doctor_summary": data["doctor_facing_short_summary"],
            "final_patient_message": (
                "Your pregnancy scan and lab reports are normal. "
                "The baby is developing well. Please continue regular antenatal check-ups."
                if lab["ai_severity"] == "NORMAL"
                else
                "Your pregnancy report shows some findings that need closer follow-up. "
                "The doctor has reviewed the report and will guide you on the next steps. "
                "Please attend the recommended follow-up visit."
            )
        }

        filename = f"final_doctor_output_{patient['patient_id']}.json"
        save_final_doctor_output(final_output, filename)

        st.session_state.final_output = final_output
        st.session_state.final_filename = filename

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

    final_json = st.session_state.final_output

    # ---------- PATIENT MESSAGE ----------
    st.warning(final_json["final_patient_message"])

    # ---------- FINAL JSON ----------
    st.subheader("📄 Doctor-Approved Final Output (JSON)")
    st.json(final_json)

    st.download_button(
        label="⬇️ Download Final Doctor Output JSON",
        data=json.dumps(final_json, indent=2),
        file_name=st.session_state.final_filename,
        mime="application/json"
    )

    # ==================== WHATSAPP MESSAGE PREVIEW ====================
    st.subheader("📱 WhatsApp Message Preview")

    whatsapp_message = f"""
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
"""

    st.text_area(
        "Message to be sent via WhatsApp",
        whatsapp_message.strip(),
        height=240
    )

    # ==================== WHATSAPP ATTACHMENTS ====================
    st.subheader("📎 WhatsApp Attachments Preview")

    attachments = []
    if reports.get("lab_report_pdf"):
        attachments.append(reports["lab_report_pdf"])
    if reports.get("ultrasound_report_pdf"):
        attachments.append(reports["ultrasound_report_pdf"])

    for file in attachments:
        st.write(f"📄 {file}")

    st.info("WhatsApp message and attachments will be sent only after final integration.")

elif st.session_state.doctor_decision == "EDIT":
    st.warning("Doctor has chosen to edit the report. Patient communication is on hold.")

elif st.session_state.doctor_decision == "REJECTED":
    st.error("Report rejected. Patient communication is blocked.")

else:
    st.info("Awaiting doctor decision. Patient communication is locked.")
