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
imaging = data.get("imaging_evidence", {})

# New pipeline fields
validation_decision = data.get("validation_decision", "-")
validation_reason   = data.get("validation_reason", "-")
rag_imaging_sources = data.get("rag_imaging_sources", [])
rag_pathway_sources = data.get("rag_pathway_sources", [])
doctor_summary      = data.get("doctor_facing_summary", "-")

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

    try:
        conf = round(float(ct_out.get("confidence", 0)) * 100, 2)
    except:
        conf = "-"

    st.info(
        f"CT Brain image classified as **{ct_out.get('prediction','-')}** "
        f"with **{conf}% confidence**."
    )

    st.divider()

    st.subheader("🧠 AI Severity (Fusion)")
    st.write("**Final Severity:**", fusion.get("derived_severity", "-"))
    st.write("**Patient Context:**", patient.get("context", "-"))

    st.divider()

    st.subheader("📘 Guideline & Safety Validation (New CT-RAG Pipeline)")

    st.write("**Validation decision:**", validation_decision)
    st.write("**Reason:**", validation_reason)

    st.subheader("📚 Retrieved reference sources (audit)")

    st.markdown("**Imaging references**")
    if rag_imaging_sources:
        for s in rag_imaging_sources:
            st.write("-", s)
    else:
        st.write("- None")

    st.markdown("**Pathway references**")
    if rag_pathway_sources:
        for s in rag_pathway_sources:
            st.write("-", s)
    else:
        st.write("- None")

# =====================================================
# 📋 CLINICAL EVIDENCE
# =====================================================
elif page == "📋 Clinical Evidence":

    st.subheader("📋 Clinical Evidence for Doctor Verification")

    st.subheader("🖥️ CT AI Evidence")

    st.write("**Modality:** CT Brain")
    st.write("**CT Image ID:**", imaging.get("image_id", "-"))
    st.write("**Prediction:**", ct_out.get("prediction", "-"))

    try:
        conf = round(float(ct_out.get("confidence", 0)) * 100, 2)
    except:
        conf = "-"

    st.write("**Confidence:**", conf, "%")

    st.divider()

    st.subheader("📘 RAG – Doctor-facing grounded summary")

    st.write(doctor_summary)

    st.divider()

    st.subheader("📚 Evidence used for this summary")

    st.markdown("**Imaging references**")
    for s in rag_imaging_sources:
        st.write("-", s)

    st.markdown("**Pathway references**")
    for s in rag_pathway_sources:
        st.write("-", s)

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

            st.success("Doctor approved the RAG-grounded AI report.")

            final_output = {
                "patient_id": patient.get("patient_id"),
                "modality": "CT Brain",
                "image_id": imaging.get("image_id"),
                "ct_prediction": ct_out.get("prediction"),
                "confidence": ct_out.get("confidence"),
                "final_severity": fusion.get("derived_severity"),
                "patient_context": patient.get("context"),
                "validation_decision": validation_decision,
                "validation_reason": validation_reason,
                "rag_imaging_sources": rag_imaging_sources,
                "rag_pathway_sources": rag_pathway_sources,
                "doctor_facing_summary": doctor_summary,
                "doctor_decision": "APPROVED",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.subheader("📄 Doctor-approved final output")
            st.json(final_output)

            st.download_button(
                label="⬇️ Download doctor-approved JSON",
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

    else:

        patient_message = (
            f"Hello,\n\n"
            f"Your CT brain report has been reviewed and approved by your doctor.\n\n"
            f"Patient ID: {patient.get('patient_id', '-')}\n"
            f"Result: {ct_out.get('prediction','-')}\n"
            f"Severity: {fusion.get('derived_severity', '-')}\n\n"
            f"If you have symptoms, concerns, or would like further clarification, "
            f"please schedule a follow-up appointment with your doctor.\n\n"
            f"Regards,\n"
            f"Hospital Care Team"
        )

        st.text_area(
            "Patient Message Preview (SMS / WhatsApp)",
            patient_message,
            height=220
        )
