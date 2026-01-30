import json
import streamlit as st
from pathlib import Path

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Doctor-in-the-Loop – CT Review Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop – CT Brain Review Dashboard")

# ==================== DATA PATH ====================
DATA_PATH = Path("data/ct_demo_with_rag.json")

if not DATA_PATH.exists():
    st.error("CT review JSON not found. Please upload data/ct_demo_with_rag.json")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

# ==================== SAFE EXTRACTION ====================

patient = data.get("patient_details", {})
ct_out = data.get("ct_model_output", {})
fusion = data.get("ai_severity_fusion", {})
rag = data.get("rag_guideline_validation", {})

# ==================== LAYOUT ====================

left, right = st.columns([1, 3])

# ---------------- LEFT PANEL ----------------
with left:
    st.subheader("👤 Patient Details")

    st.write("**Patient ID:**", patient.get("patient_id", "-"))
    st.write("**Modality:**", patient.get("modality", "CT Brain"))

    st.divider()

    st.subheader("🧠 AI Severity (Fusion)")
    st.metric(
        label="Final Severity",
        value=fusion.get("final_severity", "-")
    )

# ---------------- RIGHT PANEL ----------------
with right:
    st.subheader("🖥️ CT AI Evidence")

    st.write("**CT Image ID:**", data.get("imaging_evidence", {}).get("image_id", "-"))
    st.write("**Prediction:**", ct_out.get("prediction", "-"))
    st.write("**Confidence:**", round(float(ct_out.get("confidence", 0)), 3))

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
