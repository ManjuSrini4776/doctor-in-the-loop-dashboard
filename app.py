import json
import streamlit as st
from pathlib import Path

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Doctor-in-the-Loop – Clinical Review Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop – Clinical Review Dashboard")

# ==================== CASE SELECTION ====================
st.sidebar.header("📂 Case Selection")

case_choice = st.sidebar.selectbox(
    "Select Case",
    ["Latest CT Brain Case", "Latest Ultrasound Case"]
)

# ==================== JSON SOURCE ====================
if case_choice == "Latest CT Brain Case":
    DATA_PATH = Path("data/ct_demo_with_rag.json")
else:
    DATA_PATH = Path("data/ultrasound_latest.json")

if not DATA_PATH.exists():
    st.error(f"Required JSON file not found: {DATA_PATH}")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

# =====================================================
# ==================== CT CASE ========================
# =====================================================
if case_choice == "Latest CT Brain Case":

    patient = data.get("patient_details", {})
    ct_out = data.get("ct_model_output", {})
    fusion = data.get("ai_severity_fusion", {})
    rag = data.get("rag_guideline_validation", {})
    imaging = data.get("imaging_evidence", {})

    left, right = st.columns([1, 3])

    # ---------------- LEFT PANEL ----------------
    with left:
        st.subheader("👤 Patient Details")

        st.write("**Patient ID:**", patient.get("patient_id", "-"))
        st.write("**Modality:**", patient.get("modality", "CT Brain"))

        if imaging:
            st.write("**Image ID:**", imaging.get("image_id", "-"))

        st.divider()

        st.subheader("🧠 AI Severity (Fusion)")

        st.metric(
            label="Final Severity",
            value=fusion.get("final_severity", "-")
        )

        st.write("**Patient Context:**", fusion.get("patient_context", "-"))

    # ---------------- RIGHT PANEL ----------------
    with right:
        st.subheader("🖥️ CT AI Evidence")

        st.write("**Prediction:**", ct_out.get("prediction", "-"))
        st.write(
            "**Confidence:**",
            round(float(ct_out.get("confidence", 0)), 3)
        )

        st.divider()

        st.subheader("📘 Guideline Validation (RAG)")

        st.write("**Guideline Source:**", rag.get("guideline_source", "-"))
        st.write("**Validation Status:**", rag.get("validation_status", "-"))

        st.subheader("Clinical Summary")

        clinical_summary = rag.get("clinical_summary", {})
        if isinstance(clinical_summary, dict):
            st.json(clinical_summary)
        else:
            st.write(clinical_summary)

        st.subheader("Recommendation")
        st.info(rag.get("recommendation", "-"))

# =====================================================
# ================= ULTRASOUND CASE ===================
# =====================================================
else:

    patient = data.get("patient_details", {})
    imaging = data.get("imaging_evidence", {})
    model_out = data.get("model_output", {})
    system = data.get("system_metadata", {})

    left, right = st.columns([1, 3])

    # ---------------- LEFT PANEL ----------------
    with left:
        st.subheader("👤 Patient Details")

        st.write("**Patient ID:**", patient.get("patient_id", "-"))
        st.write("**Clinical Context:**", patient.get("clinical_context", "-"))

        st.divider()

        st.subheader("🧠 AI Output")

        st.metric(
            label="Prediction",
            value=model_out.get("prediction", "-")
        )

    # ---------------- RIGHT PANEL ----------------
    with right:
        st.subheader("🖥️ Ultrasound AI Evidence")

        st.write("**Modality:**", imaging.get("modality", "-"))
        st.write("**Image ID:**", imaging.get("image_id", "-"))

        st.write("**Prediction:**", model_out.get("prediction", "-"))
        st.write(
            "**Confidence:**",
            f"{round(model_out.get('confidence', 0)*100, 2)} %"
        )

        st.divider()

        image_path = imaging.get("image_path")

        if image_path and Path(image_path).exists():
            st.image(
                image_path,
                caption="Ultrasound Image used for inference",
                use_column_width=True
            )
        else:
            st.warning("Ultrasound image file not available in this deployment.")

        st.divider()

        st.subheader("⚙️ System Metadata")
        st.json(system)
