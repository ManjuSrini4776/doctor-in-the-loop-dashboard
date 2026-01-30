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

# ==================== CASE SELECTION ====================
st.sidebar.header("👤 Case Selection")

case_choice = st.sidebar.selectbox(
    "Select Case",
    ["Latest Ultrasound Case"]
)

# ==================== JSON SOURCE (CLOUD SAFE) ====================
AUTO_JSON_PATH = Path("data/ultrasound_latest.json")
json_file = AUTO_JSON_PATH

# ==================== NAVIGATION ====================
page = st.sidebar.radio(
    "🧭 Navigation",
    [
        "🏠 Home Overview",
        "📋 Clinical Evidence",
        "✏️ Doctor Actions",
        "📲 Patient Communication"
    ]
)

# ==================== LOAD JSON ====================
if not json_file.exists():
    st.error(f"Required JSON file not found: {json_file}")
    st.stop()

with open(json_file, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================
patient = data.get("patient_details", {})
imaging = data.get("imaging_evidence", {})
model_out = data.get("model_output", {})
system = data.get("system_metadata", {})

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
        st.write(f"**Clinical Context:** {patient.get('clinical_context', '-')}")

    with col2:
        st.metric(
            label="AI Prediction",
            value=model_out.get("prediction", "NA")
        )

    st.divider()

    st.subheader("🧠 AI Summary")
    st.info(
        f"Ultrasound plane classified as **{model_out.get('prediction', '-') }** "
        f"with **{round(model_out.get('confidence', 0)*100, 2)}% confidence**."
    )

    st.divider()

    st.subheader("⚙️ System Metadata")
    st.json(system)

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":
    st.subheader("📋 Clinical Evidence for Doctor Verification")

    st.subheader("🖥️ Ultrasound AI Evidence")
    st.write(f"**Modality:** {imaging.get('modality', '-')}")
    st.write(f"**Ultrasound Image ID:** {imaging.get('image_id', '-')}")
    st.write(f"**AI Prediction:** {model_out.get('prediction', '-')}")
    st.write(
        f"**Confidence:** {round(model_out.get('confidence', 0) * 100, 2)} %"
    )

    st.divider()

    # ---------- IMAGE PREVIEW & DOWNLOAD ----------
    image_path = imaging.get("image_path")

    if image_path and Path(image_path).exists():
        st.image(
            image_path,
            caption="Ultrasound Image Used for AI Inference",
            use_column_width=True
        )

        with open(image_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Ultrasound Image",
                data=f,
                file_name=Path(image_path).name,
                mime="image/png"
            )
    else:
        st.warning("Ultrasound image file not available.")

# =====================================================
# ✏️ DOCTOR ACTIONS
# =====================================================
elif page == "✏️ Doctor Actions":
    st.subheader("🧑‍⚕️ Doctor Decision")

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
            "prediction": model_out.get("prediction"),
            "confidence": model_out.get("confidence"),
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
            f"Your ultrasound report has been reviewed and approved.\n\n"
            f"Patient ID: {patient.get('patient_id')}\n"
            f"Finding: {model_out.get('prediction')}\n"
            f"Confidence: {round(model_out.get('confidence', 0)*100, 2)}%\n\n"
            f"Regards,\nHospital Care Team"
        )

        st.text_area(
            "Patient Message Preview (WhatsApp / SMS)",
            patient_message,
            height=220
        )
