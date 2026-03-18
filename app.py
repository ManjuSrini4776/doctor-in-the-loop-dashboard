import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Doctor Dashboard", layout="wide")

DATA_PATH = "data"
IMAGE_PATH = "images"

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    fusion = pd.read_csv(f"{DATA_PATH}/fusion_data.csv")
    lab = pd.read_csv(f"{DATA_PATH}/lab_data.csv")
    ct = pd.read_csv(f"{DATA_PATH}/ct_data.csv")
    us = pd.read_csv(f"{DATA_PATH}/us_data.csv")

    with open(f"{DATA_PATH}/rag_patient_context.json") as f:
        rag = json.load(f)

    return fusion, lab, ct, us, rag

fusion_df, lab_df, ct_df, us_df, rag_data = load_data()

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
            st.error("Invalid login")

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
# SEVERITY COLOR
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
# GRADCAM MAPPING
# -------------------------------
def get_ct_image(label):
    mapping = {
        "glioma": "ct_glioma.png",
        "meningioma": "ct_meningioma.png",
        "pituitary": "ct_pituitary.png",
        "notumor": "ct_notumor.png"
    }
    return mapping.get(label.lower(), None)

def get_us_image(label):
    mapping = {
        "abdomen": "us_abdomen.png",
        "brain": "us_brain.png",
        "femur": "us_femur.png",
        "thorax": "us_thorax.png"
    }
    return mapping.get(label.lower(), None)

# -------------------------------
# PATIENT DETAILS
# -------------------------------
def patient_details(case_id):
    st.title(f"🧾 Case: {case_id}")

    fusion = fusion_df[fusion_df['case_id'] == case_id].iloc[0]

    st.subheader("🤖 Multimodal Severity")
    show_severity(fusion['fusion_label'])

    col1, col2, col3 = st.columns(3)
    col1.write(f"Lab: {fusion['lab_severity_label']}")
    col2.write(f"CT: {fusion['ct_severity_label']}")
    col3.write(f"US: {fusion['us_severity_label']}")

    # ---------------- LAB ----------------
    st.subheader("🧪 Lab Data")
    st.dataframe(lab_df.head(10))  # later filter mapping

    # ---------------- CT ----------------
    st.subheader("🧠 CT Scan")
    ct_sample = ct_df.sample(1).iloc[0]
    st.write(f"Prediction: {ct_sample['label']}")

    img = get_ct_image(ct_sample['label'])
    if img and os.path.exists(f"{IMAGE_PATH}/{img}"):
        st.image(f"{IMAGE_PATH}/{img}", caption="CT Grad-CAM")

    # ---------------- US ----------------
    st.subheader("👶 Ultrasound")
    us_sample = us_df.sample(1).iloc[0]
    st.write(f"Plane: {us_sample['plane']}")

    img = get_us_image(us_sample['plane'])
    if img and os.path.exists(f"{IMAGE_PATH}/{img}"):
        st.image(f"{IMAGE_PATH}/{img}", caption="US Grad-CAM")

    # ---------------- RAG ----------------
    st.subheader("📚 AI Clinical Summary")

    context = rag_data.get(case_id, {})
    st.write(context.get("summary", "No summary available"))

    st.subheader("📌 Citations")
    for c in context.get("citations", []):
        st.write(f"- {c}")

    st.subheader("💊 Recommendations")
    for r in context.get("recommendations", []):
        st.write(f"- {r}")

    # ---------------- APPROVAL ----------------
    st.subheader("👨‍⚕️ Doctor Action")

    if st.button("✅ Approve"):
        st.success("Approved & Ready to send to patient")

    # ---------------- MESSAGE ----------------
    st.subheader("📩 Patient Message")
    st.text_area("Preview", context.get("patient_message", ""), height=150)

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
