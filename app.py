import json
import os
import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(page_title="Doctor Dashboard", layout="centered")
st.title("🩺 Doctor Dashboard")

# --------------------------------------------------
# Load JSON data
# --------------------------------------------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error(f"Required file not found: {JSON_PATH}")
    st.write("Files available in app directory:", os.listdir("."))
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# --------------------------------------------------
# Doctor Routing Logic (Doctor-in-the-Loop)
# --------------------------------------------------
ordering_doctor = data.get("ordering_doctor", {})
fallback_doctor = data.get("fallback_doctor", {})

if ordering_doctor.get("available", False):
    assigned_doctor = ordering_doctor
    routing_reason = "Assigned to ordering doctor (available)"
else:
    assigned_doctor = fallback_doctor
    routing_reason = "Ordering doctor unavailable – routed to same-department doctor"

# --------------------------------------------------
# Patient Details
# --------------------------------------------------
st.subheader("Patient Details")
patient = data.get("patient_details", {})

st.write("**Patient ID:**", patient.get("patient_id"))
st.write("**Age:**", patient.get("age"))
st.write("**Gender:**", patient.get("gender"))
st.write("**Clinical Context:**", patient.get("context"))

# --------------------------------------------------
# Assigned Doctor Details
# --------------------------------------------------
st.subheader("Assigned Doctor")
st.write("**Doctor Name:**", assigned_doctor.get("doctor_name"))
st.write("**Department:**", assigned_doctor.get("department"))
st.write("**Routing Reason:**", routing_reason)

# --------------------------------------------------
# Structured Clinical Summary
# --------------------------------------------------
st.subheader("Structured Clinical Summary")
structured_summary = data.get("structured_summary", {})

for key, value in structured_summary.items():
    st.write(f"**{key}:** {value}")

# --------------------------------------------------
# Doctor-Facing Short Summary
# --------------------------------------------------
st.subheader("Doctor-Facing Short Summary")
st.info(data.get("short_summary"))

# --------------------------------------------------
# System Decisions
# --------------------------------------------------
st.subheader("System Decisions")
st.write("**Guideline Validation:**", data.get("guideline_validation"))
st.write("**Routing Decision:**", data.get("routing_decision"))

