import json
import streamlit as st

st.set_page_config(page_title="Doctor Dashboard", layout="centered")

st.title("🩺 Doctor Dashboard")

JSON_PATH = "/content/drive/MyDrive/Medical_AI_Project/doctor_review_output.json"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

st.subheader("Patient Context")
st.write(data["patient_context"])

st.subheader("Structured Clinical Summary")
for key, value in data["structured_summary"].items():
    st.write(f"**{key}:** {value}")

st.subheader("Doctor-Facing Short Summary")
st.info(data["short_summary"])

st.subheader("System Decisions")
st.write("Guideline Validation:", data["guideline_validation"])
st.write("Routing Decision:", data["routing_decision"])
