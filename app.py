import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Doctor-approved AI medical reporting with secure patient access")

# ==================== AUTO ULTRASOUND CASE ====================
st.sidebar.header("👤 Case Selection")

case_choice = st.sidebar.selectbox(
    "Select Case",
    ["Latest Ultrasound Case"]
)

AUTO_JSON_PATH = (
    "/content/drive/MyDrive/Medical_AI_Project/"
    "auto_evidence/ultrasound_latest.json"
)

json_file = AUTO_JSON_PATH


page = st.sidebar.radio(
    "🧭 Navigation",
    [
        "🏠 Home Overview",
        "📋 Clinical Evidence",
        "✏️ Doctor Actions",
        "📲 Patient Communication"
    ]
)

json_file = PATIENT_FILES[patient_choice]

if not Path(json_file).exists():
    st.error(f"Required JSON file not found: {json_file}")
    st.stop()

# ==================== LOAD JSON ====================
with open(json_file, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================
patient = data.get("patient_details", {})
doctor = data.get("assigned_doctor", {})
lab = data.get("lab_summary", {})
ultrasound = data.get("ultrasound_summary", {})
system = data.get("system_decisions", {})
reports = data.get("hospital_reports", {})
followup = data.get("doctor_followup_instructions", {})

REPORTS_DIR = Path("reports")

# ==================== SESSION STATE ====================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# =====================================================
# 🏠 HOME OVERVIEW
# =====================================================
if page == "🏠 Home Overview":
    st.subheader("🏠 Patient Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Patient ID:** {patient.get('patient_id', '-')}")
        st.write(f"**Age:** {patient.get('age', '-')}")
        st.write(f"**Gender:** {patient.get('gender', '-')}")
        st.write(f"**Clinical Context:** {patient.get('clinical_context', '-')}")

    with col2:
        st.metric(
            label="Final AI Severity",
            value=lab.get("ai_severity", "NA")
        )

    st.divider()

    st.subheader("📝 Doctor-Facing Summary")
    st.info(data.get("doctor_facing_short_summary", "Summary not available"))

    st.divider()

    st.subheader("⚙️ Guideline Validation Status")
    st.write(system.get("guideline_validation", "-"))

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":
    st.subheader("📋 Clinical Evidence for Doctor Verification")

    # ==============================
# Ultrasound Evidence (AUTO)
# ==============================

imaging = data.get("imaging_evidence", {})
model_out = data.get("model_output", {})

st.subheader("🖥️ Ultrasound AI Evidence")

st.write(f"**Modality:** {imaging.get('modality', '-')}")
st.write(f"**Ultrasound Image ID:** {imaging.get('image_id', '-')}")

st.write(f"**AI Prediction:** {model_out.get('prediction', '-')}")
st.write(
    f"**Confidence:** {round(model_out.get('confidence', 0) * 100, 2)} %"
)


    # ---------- LAB SUMMARY ----------
    if lab:
        st.subheader("📄 Lab Summary")
        st.json(lab)

    # ---------- ULTRASOUND SUMMARY ----------
    if ultrasound:
        st.divider()
        st.subheader("🖥️ Ultrasound Summary")

        st.write(f"**Ultrasound Image ID:** {ultrasound.get('image_id', '-')}")
        st.write(f"**Plane:** {ultrasound.get('plane', '-')}")

        st.json({
            "last_ultrasound": ultrasound.get("last_ultrasound", "-"),
            "ai_note": ultrasound.get("ai_note", "-"),
            "clinical_note": ultrasound.get("clinical_note", "-")
        })

    # ---------- REPORT DOWNLOADS ----------
    st.divider()
    st.subheader("📎 Diagnostic Reports (Download & Verify)")

    if reports.get("lab_report_pdf"):
        lab_path = REPORTS_DIR / reports["lab_report_pdf"]
        if lab_path.exists():
            with open(lab_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Lab Report",
                    data=f,
                    file_name=lab_path.name,
                    mime="application/pdf"
                )
        else:
            st.warning("Lab report file not found.")
# ---------- ULTRASOUND IMAGE DOWNLOAD ----------
if ultrasound.get("image_file"):
    image_path = REPORTS_DIR / ultrasound["image_file"]

    if image_path.exists():
        with open(image_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Ultrasound Image (Used for AI Inference)",
                data=f,
                file_name=image_path.name,
                mime="image/png"
            )
    else:
        st.warning("Ultrasound image file not found.")

# =====================================================
# ✏️ DOCTOR ACTIONS
# =====================================================
elif page == "✏️ Doctor Actions":
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Name:** {doctor.get('doctor_name', '-')}")
    st.write(f"**Department:** {doctor.get('department', '-')}")
    st.write(f"**Routing Reason:** {doctor.get('routing_reason', '-')}")

    st.divider()
    st.subheader("✏️ Doctor Decision")

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

    if st.session_state.doctor_decision == "APPROVED":
        st.success("Doctor approved the AI report.")

        st.divider()
        st.subheader("📄 Doctor-Approved Final Output")

        final_output = {
            "patient_id": patient.get("patient_id"),
            "clinical_context": patient.get("clinical_context"),
            "doctor_decision": "APPROVED",
            "severity": lab.get("ai_severity", "NA"),
            "doctor_summary": data.get("doctor_facing_short_summary"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        st.json(final_output)

        st.download_button(
            label="⬇️ Download Final Doctor Output (JSON)",
            data=json.dumps(final_output, indent=4),
            file_name=f"{patient.get('patient_id')}_final_output.json",
            mime="application/json"
        )

# =====================================================
# 📲 PATIENT COMMUNICATION
# =====================================================
elif page == "📲 Patient Communication":
    st.subheader("📲 Patient Communication")

    if st.session_state.doctor_decision != "APPROVED":
        st.warning("Patient communication is locked until doctor approval.")
    else:
        patient_message = (
            f"Hello,\n\n"
            f"Your medical report has been reviewed and approved by your doctor.\n\n"
            f"Patient ID: {patient.get('patient_id')}\n"
            f"Clinical Context: {patient.get('clinical_context')}\n"
            f"Overall Assessment: {lab.get('ai_severity', 'NA')}\n\n"
            f"Please follow the medical advice provided.\n\n"
            f"Regards,\nHospital Care Team"
        )

        st.text_area(
            "Patient Message Preview (WhatsApp / SMS)",
            patient_message,
            height=220
        )
