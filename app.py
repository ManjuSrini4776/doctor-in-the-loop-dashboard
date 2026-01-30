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

# ==================== JSON SOURCE ====================
# For Streamlit Cloud, keep JSON inside repo (e.g., data/)
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
ct_output = data.get("ct_model_output", {})
fusion = data.get("ai_severity_fusion", {})
rag = data.get("rag_guideline_validation", {})
doctor_summary = data.get("doctor_facing_short_summary", "")

# ==================== SESSION STATE ====================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# =====================================================
# 🏠 HOME OVERVIEW
# =====================================================
if page == "🏠 Home Overview":
    st.subheader("🏠 Case Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Modality:** CT Brain")
        st.write("**AI Prediction:**", ct_output.get("prediction", "-"))
        st.write("**Confidence:**", ct_output.get("confidence", "-"))

    with col2:
        st.metric(
            label="Final AI Severity",
            value=fusion.get("derived_severity", "NA")
        )

    st.divider()

    st.subheader("🩺 Doctor-Facing AI Summary")
    st.info(doctor_summary)

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":
    st.subheader("📋 Clinical Evidence for Doctor Verification")

    st.subheader("🧠 CT AI Output")
    st.json({
        "Prediction": ct_output.get("prediction"),
        "Confidence": ct_output.get("confidence")
    })

    st.divider()

    st.subheader("⚖️ AI Severity Fusion")
    st.json(fusion)

    st.divider()

    st.subheader("📘 Guideline Validation (RAG)")
    st.json(rag)

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
            "modality": "CT Brain",
            "doctor_decision": "APPROVED",
            "ct_prediction": ct_output.get("prediction"),
            "confidence": ct_output.get("confidence"),
            "final_severity": fusion.get("derived_severity"),
            "guideline_validation": rag.get("validation_status"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        st.json(final_output)

        st.download_button(
            label="⬇️ Download Final Doctor Output (JSON)",
            data=json.dumps(final_output, indent=4),
            file_name="ct_doctor_final_output.json",
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
            f"Finding: {ct_output.get('prediction')}\n"
            f"Severity: {fusion.get('derived_severity')}\n\n"
            f"No urgent medical action is required.\n\n"
            f"Regards,\nHospital Care Team"
        )

        st.text_area(
            "Patient Message Preview (WhatsApp / SMS)",
            patient_message,
            height=220
        )
