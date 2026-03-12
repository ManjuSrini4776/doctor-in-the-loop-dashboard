import streamlit as st
from pipeline import run_clinical_pipeline

st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical AI Dashboard",
    layout="wide"
)

st.title("Doctor-in-the-Loop Clinical AI Dashboard")

st.markdown("---")

# Patient selector
st.subheader("Select Patient")

patient_id = st.selectbox(
    "Patient ID",
    ["P001", "P002", "P003"]
)

st.markdown("---")

# Run pipeline button
if st.button("Run AI Clinical Analysis"):

    result = run_clinical_pipeline(patient_id)

    # Patient context
    st.subheader("Patient Clinical Context")
    st.info(result["context"])

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Model Prediction")
        st.write(result["prediction"])

    with col2:
        st.subheader("Severity Assessment")
        st.write(result["severity"])

    st.markdown("---")

    # AI explanation
    st.subheader("AI Generated Clinical Explanation")

    edited_summary = st.text_area(
        "Doctor Review (editable)",
        result["explanation"],
        height=200
    )

    st.markdown("---")

    # Doctor review buttons
    st.subheader("Doctor Decision")

    col1, col2, col3 = st.columns(3)

    if col1.button("Approve Diagnosis"):
        st.success("Diagnosis approved. Report sent to patient.")

    if col2.button("Reject Diagnosis"):
        st.error("Diagnosis rejected. Case returned for re-evaluation.")

    if col3.button("Save Edited Summary"):
        st.info("Edited summary saved.")
