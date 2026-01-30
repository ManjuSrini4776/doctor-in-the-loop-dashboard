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
    ["Latest CT Brain Case"]
)

# ==================== JSON SOURCE (STREAMLIT CLOUD SAFE) ====================
JSON_PATH = Path("data/doctor_review_output.json")

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
if not JSON_PATH.exists():
    st.error(f"Doctor review JSON not found: {JSON_PATH}")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================
patient = data.get("patient_details", {})
ct_model = data.get("ct_model_output", {})
severity_fusion = data.get("ai_severity_fusion", {})
rag = data.get("rag_guideline_validation", {})
doctor_summary = data.get("doctor_facing_short_summary", "")

# ==================== SESSION STATE ====================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# =====================================================
# 🏠 HOME OVERVIEW
# =====================================================
if page == "🏠 Home Overview":
    st.subheader("👤 Patient Information")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Patient ID:** {patient.get('patient_id', '-')}")
        st.write(f"**Age:** {patient.get('age', '-')}")
        st.write(f"**Gender:** {patient.get('gender', '-')}")
        st.write(f"**Clinical Context:** {patient.get('clinical_context', '-')}")

    with col2:
        st.metric(
            label="Final AI Severity",
            value=severity_fusion.get("derived_severity", "NA")
        )

    st.divider()

    st.subheader("🧠 AI Summary")
    st.info(doctor_summary if doctor_summary else "No AI summary available.")

    st.divider()

    st.subheader("⚙️ System Metadata")
    st.json({
        "Model": "EfficientNet-B0 (CT Brain)",
        "Prediction": ct_model.get("prediction"),
        "Confidence": ct_model.get("confidence"),
        "Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":
    st.subheader("📋 Clinical Evidence for Doctor Verification")

    st.subheader("🖥️ CT Brain AI Evidence")
    st.write(f"**AI Prediction:** {ct_model.get('prediction', '-')}")
    st.write(f"**Confidence:** {round(ct_model.get('confidence', 0)*100, 2)} %")
    st.write(f"**Derived Severity:** {severity_fusion.get('derived_severity', '-')}")

    st.divider()

    st.subheader("📘 Guideline Validation (RAG)")
    st.json({
        "Guideline Source": rag.get("guideline_source"),
        "Validation Status": rag.get("validation_status"),
        "Clinical Summary": rag.get("clinical_summary"),
        "Recommendation": rag.get("recommendation"),
        "Generated At": rag.get("generated_at")
    })

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

        final_output = {
            "patient_id": patient.get("patient_id"),
            "clinical_context": patient.get("clinical_context"),
            "doctor_decision": "APPROVED",
            "final_severity": severity_fusion.get("derived_severity"),
            "ai_prediction": ct_model.get("prediction"),
            "confidence": ct_model.get("confidence"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        st.divider()
        st.subheader("📄 Doctor-Approved Final Output")
        st.json(final_output)

        st.download_button(
            label="⬇️ Download Final Doctor Output (JSON)",
            data=json.dumps(final_output, indent=4),
            file_name=f"{patient.get('patient_id', 'case')}_final_output.json",
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
            f"Your CT brain scan has been reviewed and approved by the doctor.\n\n"
            f"Patient ID: {patient.get('patient_id')}\n"
            f"Finding: {ct_model.get('prediction')}\n"
            f"Severity: {severity_fusion.get('derived_severity')}\n\n"
            f"Please follow hospital guidance.\n\n"
            f"Regards,\nHospital Care Team"
        )

        st.text_area(
            "Patient Message Preview (WhatsApp / SMS)",
            patient_message,
            height=220
        )
