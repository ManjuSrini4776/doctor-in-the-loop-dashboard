import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Doctor-in-the-Loop Dashboard", layout="wide")

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    fusion = pd.read_csv("data/fusion_data.csv")

    with open("data/rag_patient_context.json") as f:
        rag = json.load(f)

    rag_dict = {item["case_id"]: item for item in rag}

    return fusion, rag_dict

fusion_df, rag_data = load_data()

# -------------------------------
# SESSION
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
# GET IMAGE
# -------------------------------
def get_ct_image(label):
    mapping = {
        "Severe": "ct_glioma.png",
        "Moderate": "ct_meningioma.png",
        "Mild": "ct_pituitary.png",
        "Normal": "ct_notumor.png"
    }
    return f"images/{mapping.get(label, 'ct_notumor.png')}"

def get_us_image(label):
    mapping = {
        "Severe": "us_brain.png",
        "Moderate": "us_thorax.png",
        "Mild": "us_femur.png",
        "Normal": "us_abdomen.png"
    }
    return f"images/{mapping.get(label, 'us_abdomen.png')}"

# -------------------------------
# PATIENT DETAILS
# -------------------------------
def patient_details(case_id):
    st.title(f"🧾 Case: {case_id}")

    fusion = fusion_df[fusion_df['case_id'] == case_id].iloc[0]
    rag    = rag_data.get(case_id, {})

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
    # GRADCAM
    # -------------------------------
    st.subheader("🧠 Explainability (Grad-CAM)")

    col1, col2 = st.columns(2)

    ct_img = get_ct_image(fusion['ct_severity_label'])
    us_img = get_us_image(fusion['us_severity_label'])

    if os.path.exists(ct_img):
        col1.image(ct_img, caption="CT Grad-CAM")

    if os.path.exists(us_img):
        col2.image(us_img, caption="Ultrasound Grad-CAM")

    # -------------------------------
    # RAG SUMMARY
    # -------------------------------
    st.subheader("📚 AI Clinical Summary")

    scores = rag.get("scores", {})

    st.write(f"""
**Clinical Interpretation:**
Patient shows **{fusion['fusion_label']} severity** based on multimodal analysis.

- Lab: {scores.get('lab', {}).get('label', 'N/A')}
- CT: {scores.get('ct', {}).get('label', 'N/A')}
- Ultrasound: {scores.get('ultrasound', {}).get('label', 'N/A')}
""")

    # -------------------------------
    # RECOMMENDATIONS
    # -------------------------------
    st.subheader("💊 Recommendations")

    if fusion['fusion_label'] == "Severe":
        st.write("- Immediate clinical attention required")
        st.write("- Specialist consultation recommended")
    elif fusion['fusion_label'] == "Moderate":
        st.write("- Follow-up tests advised")
    else:
        st.write("- Routine monitoring")

    # -------------------------------
    # DOCTOR ACTION
    # -------------------------------
    st.subheader("👨‍⚕️ Doctor Decision")

    if st.button("✅ Approve"):
        st.success("Approved ✔")

    # -------------------------------
    # PATIENT MESSAGE
    # -------------------------------
    st.subheader("📩 Patient Message")

    st.text_area("Preview", f"""
Dear Patient,

Your reports indicate **{fusion['fusion_label']} condition**.

Please follow doctor advice.

Stay healthy.
""", height=150)

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
