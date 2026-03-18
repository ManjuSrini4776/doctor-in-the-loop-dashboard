import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Doctor Dashboard", layout="wide")

# -------------------------------
# LOAD DATA (FROM ROOT)
# -------------------------------
@st.cache_data
def load_data():
    fusion = pd.read_csv("fusion_data.csv")
    lab = pd.read_csv("lab_data.csv")
    ct = pd.read_csv("ct_data.csv")
    us = pd.read_csv("us_data.csv")
    return fusion, lab, ct, us

fusion_df, lab_df, ct_df, us_df = load_data()

# -------------------------------
# SESSION STATE
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "selected_case" not in st.session_state:
    st.session_state.selected_case = None

# -------------------------------
# LOGIN
# -------------------------------
def login():
    st.title("👨‍⚕️ Doctor Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "doctor1" and pwd == "1234":
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

# -------------------------------
# PATIENT LIST
# -------------------------------
def patient_list():
    st.title("📋 Multimodal Patient Cases")

    for _, row in fusion_df.iterrows():
        col1, col2, col3 = st.columns([3,3,2])

        col1.write(f"**Case ID:** {row['case_id']}")
        col2.write(f"**Severity:** {row['fusion_label']}")

        if col3.button("View", key=row['case_id']):
            st.session_state.selected_case = row['case_id']

# -------------------------------
# SEVERITY DISPLAY
# -------------------------------
def show_severity(label):
    if label == "Severe":
        st.error(f"🔴 {label}")
    elif label == "Moderate":
        st.warning(f"🟠 {label}")
    elif label == "Mild":
        st.info(f"🟡 {label}")
    else:
        st.success(f"🟢 {label}")

# -------------------------------
# FAKE RAG (TEMP)
# -------------------------------
def generate_summary(case_id, fusion_row):
    return f"""
Patient {case_id} shows **{fusion_row['fusion_label']} severity** based on multimodal analysis.

- Lab Severity: {fusion_row['lab_severity_label']}
- CT Severity: {fusion_row['ct_severity_label']}
- Ultrasound Severity: {fusion_row['us_severity_label']}

Clinical interpretation:
The final severity is derived using max-rule fusion across modalities.

Recommendation:
Doctor review is required. Consider follow-up tests and clinical correlation.
"""

# -------------------------------
# PATIENT DETAILS
# -------------------------------
def patient_details(case_id):
    st.title(f"🧾 Case: {case_id}")

    fusion = fusion_df[fusion_df['case_id'] == case_id].iloc[0]

    # -------------------------------
    # SEVERITY
    # -------------------------------
    st.subheader("🤖 Multimodal Severity")
    show_severity(fusion['fusion_label'])

    col1, col2, col3 = st.columns(3)
    col1.write(f"Lab: {fusion['lab_severity_label']}")
    col2.write(f"CT: {fusion['ct_severity_label']}")
    col3.write(f"US: {fusion['us_severity_label']}")

    # -------------------------------
    # LAB DATA (TEMP FILTER)
    # -------------------------------
    st.subheader("🧪 Lab Data (Sample)")
    st.dataframe(lab_df.head(10))

    # -------------------------------
    # CT DATA
    # -------------------------------
    st.subheader("🧠 CT Analysis")
    ct_sample = ct_df.sample(1).iloc[0]
    st.write(f"Prediction: {ct_sample.get('label', 'N/A')}")

    # -------------------------------
    # US DATA
    # -------------------------------
    st.subheader("👶 Ultrasound Analysis")
    us_sample = us_df.sample(1).iloc[0]
    st.write(f"Plane: {us_sample.get('plane', 'N/A')}")

    # -------------------------------
    # RAG SUMMARY (TEMP)
    # -------------------------------
    st.subheader("📚 AI Clinical Summary")
    summary = generate_summary(case_id, fusion)
    st.write(summary)

    # -------------------------------
    # CITATIONS (STATIC FOR NOW)
    # -------------------------------
    st.subheader("📌 Citations")
    st.write("- WHO Clinical Guidelines (2023)")
    st.write("- ICMR Diagnostic Protocols")

    # -------------------------------
    # RECOMMENDATIONS
    # -------------------------------
    st.subheader("💊 Recommendations")
    st.write("- Further diagnostic evaluation")
    st.write("- Specialist consultation")
    st.write("- Follow-up monitoring")

    # -------------------------------
    # DOCTOR APPROVAL
    # -------------------------------
    st.subheader("👨‍⚕️ Doctor Action")

    if st.button("✅ Approve Report"):
        st.success("Report Approved (Doctor-in-the-loop ✔)")

    # -------------------------------
    # PATIENT MESSAGE
    # -------------------------------
    st.subheader("📩 Patient Message")

    message = f"""
Dear Patient,

Your reports indicate **{fusion['fusion_label']} condition**.

Please follow doctor's advice and attend follow-up if required.

Stay healthy.
"""

    st.text_area("Preview", message, height=150)

    if st.button("⬅ Back"):
        st.session_state.selected_case = None

# -------------------------------
# MAIN
# -------------------------------
if not st.session_state.logged_in:
    login()
else:
    if st.session_state.selected_case is None:
        patient_list()
    else:
        patient_details(st.session_state.selected_case)
