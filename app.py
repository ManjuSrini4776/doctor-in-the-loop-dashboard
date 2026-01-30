import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Doctor-in-the-Loop – Clinical Review Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop – Clinical Review Dashboard")
st.caption("Doctor-approved AI medical reporting with secure patient access")

# ==================== SIDEBAR ====================
st.sidebar.header("📂 Case Selection")

case_choice = st.sidebar.selectbox(
    "Select Case",
    ["Latest CT Brain Case"]
)

st.sidebar.divider()

page = st.sidebar.radio(
    "🧭 Navigation",
    [
        "🏠 Home Overview",
        "📋 Clinical Evidence",
        "✏️ Doctor Actions",
        "📲 Patient Communication"
    ]
)

# ==================== JSON SOURCE ====================
DATA_PATH = Path("data/ct_demo_with_rag.json")

if not DATA_PATH.exists():
    st.error("Required CT review JSON not found: data/ct_demo_with_rag.json")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================
patient = data.get("patient_details", {})
ct_out = data.get("ct_model_output", {})
fusion = data.get("ai_severity_fusion", {})
rag = data.get("rag_guideline_validation", {})
imaging = data.get("imaging_evidence", {})

# ==================== SESSION ====================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# =====================================================
# 🏠 HOME OVERVIEW
# =====================================================
if page == "🏠 Home Overview":

    st.subheader("👤 Patient Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Patient ID:**", patient.get("patient_id", "-"))
        st.write("**Modality:**", patient.get("modality", "CT Brain"))

    with col2:
        st.metric(
            label="CT AI Prediction",
            value=ct_out.get("prediction", "-")
        )

    st.divider()

    st.subheader("🧠 AI Summary")

    st.info(
        f"CT Brain image classified as **{ct_out.get('prediction','-')}** "
        f"with **{round(float(ct_out.get('confidence',0))*100,2)}% confidence**."
    )

    st.divider()

    st.subheader("🧠 AI Severity (Fusion)")
    st.write("**Final Severity:**", fusion.get("final_severity", "-"))
    st.write("**Patient Context:**", fusion.get("patient_context", "-"))

    st.divider()

    st.subheader("📘 Guideline Validation (RAG)")
    st.write("**Guideline Source:**", rag.get("guideline_source", "-"))
    st.write("**Validation Status:**", rag.get("validation_status", "-"))

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":

    st.subheader("📋 Clinical Evidence for Doctor Verification")

    st.subheader("🖥️ CT AI Evidence")

    st.write("**Modality:** CT Brain")
    st.write("**CT Image ID:**", imaging.get("image_id", "-"))
    st.write("**Prediction:**", ct_out.get("prediction", "-"))
    st.write(
        f"**Confidence:** {round(float(ct_out.get('confidence',0))*100,2)} %"
    )

    st.divider()

    # ---------- CT IMAGE PREVIEW ----------
    image_path = imaging.get("image_path")

    if image_path and Path(image_path).exists():
        st.subheader("🖼️ CT Image Used for AI Inference")

        st.image(
            image_path,
            caption="CT image used by the AI model",
            use_column_width=True
        )

        with open(image_path, "rb") as f:
            st.download_button(
                label="⬇️ Download CT Image",
                data=f,
                file_name=Path(image_path).name,
                mime="image/jpeg"
            )
    else:
        st.warning("CT image file path not found in JSON or file not available.")

    st.divider()

    st.subheader("📘 RAG – Clinical Summary")

    clinical_summary = rag.get("clinical_summary", {})

    if isinstance(clinical_summary, dict):
        st.json(clinical_summary)
    else:
        st.write(clinical_summary)

    st.subheader("📌 Recommendation")
    st.info(rag.get("recommendation", "-"))

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

    if st.session_state.doctor_decision is not None:

        st.divider()
        st.write("### Doctor Decision:", st.session_state.doctor_decision)

        if st.session_state.doctor_decision == "APPROVED":

            st.success("Doctor approved the AI report.")

            final_output = {
                "patient_id": patient.get("patient_id"),
                "modality": "CT Brain",
                "image_id": imaging.get("image_id"),
                "ct_prediction": ct_out.get("prediction"),
                "confidence": ct_out.get("confidence"),
                "final_severity": fusion.get("final_severity"),
                "patient_context": fusion.get("patient_context"),
                "rag_validation": rag,
                "doctor_decision": "APPROVED",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.subheader("📄 Doctor-Approved Final Output")
            st.json(final_output)

            st.download_button(
                label="⬇️ Download Doctor Approved JSON",
                data=json.dumps(final_output, indent=4),
                file_name=f"{patient.get('patient_id','CT')}_doctor_output.json",
                mime="application/json"
            )

# =====================================================
# 📲 PATIENT COMMUNICATION
# =====================================================
elif page == "📲 Patient Communication":

    st.subheader("📲 Patient Communication")

    if st.session_state.doctor_decision != "APPROVED":
        st.warning("Patient communication is locked until doctor approval.")
        patient_message = (
    f"Hello,\n\n"
    f"Your CT brain report has been reviewed and approved by your doctor.\n\n"
    f"Patient ID: {patient.get('patient_id', '-')}\n"
    f"Result: No abnormal findings were detected.\n"
    f"Severity: {fusion.get('final_severity', '-')}\n\n"
    f"This means your report appears normal and there is no urgent need to "
    f"visit the hospital at this time.\n\n"
    f"If you have any symptoms, concerns, or would like further clarification, "
    f"you may schedule a follow-up appointment with your doctor.\n\n"
    f"Please continue to follow any clinical advice already provided by your healthcare team.\n\n"
    f"Regards,\n"
    f"Hospital Care Team"
)

        st.text_area(
            "Patient Message Preview (SMS / WhatsApp)",
            patient_message,
            height=220
        )
