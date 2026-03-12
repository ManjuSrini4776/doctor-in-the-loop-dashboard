import streamlit as st
import pandas as pd
import json
from pipeline import run_clinical_pipeline

st.set_page_config(page_title="Doctor-in-the-Loop Clinical AI Dashboard", layout="wide")

st.title("Doctor-in-the-Loop Clinical AI Dashboard")

st.markdown("---")

# Load patient multimodal outputs
fusion_df = pd.read_csv("fusion_patient_context.csv")

# Patient selector
patient_ids = fusion_df["case_id"].tolist()

selected_patient = st.selectbox(
    "Select Patient Case",
    patient_ids
)

st.markdown("---")

# Get patient row
patient_data = fusion_df[fusion_df["case_id"] == selected_patient].iloc[0]

st.subheader("Patient Details")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("Case ID:", patient_data["case_id"])

with col2:
    st.write("Lab Score:", patient_data["lab_score"])

with col3:
    st.write("Final Severity Score:", patient_data["final_score"])

st.markdown("---")

# Run AI pipeline
if st.button("Run AI Clinical Analysis"):

    result = run_clinical_pipeline(selected_patient)

    st.subheader("Patient Clinical Context")

    st.info(result["context"])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CT Model Prediction")
        st.write(result["ct_prediction"])

    with col2:
        st.subheader("Ultrasound Model Prediction")
        st.write(result["ultrasound_prediction"])

    st.subheader("Multimodal Severity Assessment")

    st.write(result["severity"])

    st.markdown("---")

    st.subheader("AI Clinical Explanation (RAG)")

    edited_summary = st.text_area(
        "Doctor Review (editable)",
        result["explanation"],
        height=200
    )

    st.markdown("---")

    st.subheader("Doctor Decision")

    col1, col2, col3 = st.columns(3)

    if col1.button("Approve Diagnosis"):
        st.success("Diagnosis approved. Report sent to patient.")

    if col2.button("Reject Diagnosis"):
        st.error("Diagnosis rejected. Case returned for re-evaluation.")

    if col3.button("Save Edited Summary"):
        st.info("Edited summary saved.")
