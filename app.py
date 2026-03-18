import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Doctor Dashboard", layout="wide")

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    lab["final_severity_label"] = lab["final_severity_label"].replace({
        "Stable": "Normal"
    })
    ct  = pd.read_csv("data/ct_data.csv")
    us  = pd.read_csv("data/us_data.csv")

    with open("data/rag_final_outputs.json") as f:
        rag = json.load(f)

    return lab, ct, us, rag

lab_df, ct_df, us_df, rag_data = load_data()

# -------------------------------
# DOCTORS
# -------------------------------
DOCTORS = {
    "Dr. Smith (Internal Medicine)": {
        "password": "1234",
        "dept": "Internal Medicine"
    },
    "Dr. John (Neurology)": {
        "password": "1234",
        "dept": "Neurology"
    },
    "Dr. Priya (Obstetrics)": {
        "password": "1234",
        "dept": "Obstetrics"
    }
}

# -------------------------------
# SESSION
# -------------------------------
if "doctor" not in st.session_state:
    st.session_state.doctor = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None

# -------------------------------
# LOGIN FLOW
# -------------------------------
def login():
    st.title("👩‍⚕️ Select Doctor")

    doctor_name = st.selectbox("Choose Doctor", list(DOCTORS.keys()))

    if st.button("Next"):
        st.session_state.doctor = doctor_name

    if st.session_state.doctor:
        st.subheader(f"Login for {st.session_state.doctor}")
        pwd = st.text_input("Enter Password", type="password")

        if st.button("Login"):
            if pwd == DOCTORS[st.session_state.doctor]["password"]:
                st.session_state.logged_in = True
            else:
                st.error("Wrong password")

# -------------------------------
# GET DATA BY DEPARTMENT
# -------------------------------
def get_data_by_dept(dept):
    if dept == "Internal Medicine":
        return lab_df, "hadm_id", "final_severity_label"

    elif dept == "Neurology":
        return ct_df, "image_id", "ct_severity_label"

    elif dept == "Obstetrics":
        return us_df, "patient_id", "us_severity_label"

# -------------------------------
# SEVERITY UI
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
# PATIENT QUEUE
# -------------------------------
def patient_queue():
    doctor = DOCTORS[st.session_state.doctor]
    dept = doctor["dept"]

    df, id_col, sev_col = get_data_by_dept(dept)

    st.title(f"📋 Patient Queue — {dept}")

    filter_option = st.selectbox(
        "Filter by Severity",
        ["All", "Normal", "Mild", "Moderate", "Severe"]
    )

    if filter_option != "All":
        df = df[df[sev_col] == filter_option]

    for _, row in df.head(50).iterrows():
        col1, col2, col3 = st.columns([3,3,2])

        col1.write(f"ID: {row[id_col]}")
        col2.write(f"Severity: {row[sev_col]}")

        if col3.button("View", key=str(row[id_col])):
            st.session_state.selected_patient = (dept, row[id_col])

# -------------------------------
# GRADCAM
# -------------------------------
def show_images(dept, severity):
    if dept == "Neurology":
        mapping = {
            "Severe": "ct_glioma.png",
            "Moderate": "ct_meningioma.png",
            "Mild": "ct_pituitary.png",
            "Normal": "ct_notumor.png"
        }
    else:
        mapping = {
            "Severe": "us_brain.png",
            "Moderate": "us_thorax.png",
            "Mild": "us_femur.png",
            "Normal": "us_abdomen.png"
        }

    img_path = f"images/{mapping.get(severity)}"

    if os.path.exists(img_path):
        st.image(img_path, caption="Grad-CAM")

# -------------------------------
# PATIENT DETAILS
# -------------------------------
def patient_details():
    dept, pid = st.session_state.selected_patient

    df, id_col, sev_col = get_data_by_dept(dept)
    row = df[df[id_col] == pid].iloc[0]

    st.title(f"🧾 Patient: {pid}")

    # Severity
    st.subheader("🤖 AI Severity")
    show_severity(row[sev_col])

    # Clinical context
    st.subheader("📊 Patient Context")

    if dept == "Internal Medicine":
        st.write("Diabetes Severity:", row.get("diabetes_severity_final", "N/A"))
        st.write("CKD Severity:", row.get("ckd_severity", "N/A"))

        st.info("Normal HbA1c: < 5.7 | Diabetes: > 6.5")

    # GradCAM
    if dept in ["Neurology", "Obstetrics"]:
        st.subheader("🧠 Explainability")
        show_images(dept, row[sev_col])

    # RAG Summary
    st.subheader("📚 AI Clinical Summary")

    report = rag_data.get(str(pid), "No report available")
    st.write(report)

    # Doctor approval
    st.subheader("👨‍⚕️ Doctor Decision")

    if st.button("Approve"):
        st.success("Approved ✔")

    if st.button("Reject"):
        st.error("Rejected ❌")

    # Patient message
    st.subheader("📩 Patient Message Preview")

    msg = f"""
Dear Patient,

Your reports indicate {row[sev_col]} condition.

Please follow doctor's advice.

Stay healthy.
"""

    st.text_area("Message", msg, height=150)

    if st.button("⬅ Back"):
        st.session_state.selected_patient = None

# -------------------------------
# MAIN
# -------------------------------
if not st.session_state.logged_in:
    login()
else:
    if st.session_state.selected_patient is None:
        patient_queue()
    else:
        patient_details()
