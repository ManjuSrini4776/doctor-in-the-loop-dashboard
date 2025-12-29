import json
import os
from datetime import datetime
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
    st.write("Files available:", os.listdir("."))
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# --------------------------------------------------
# Doctor Routing Logic
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
# Assigned Doctor
# --------------------------------------------------
st.subheader("Assigned Doctor")
st.write("**Doctor Name:**", assigned_doctor.get("doctor_name"))
st.write("**Department:**", assigned_doctor.get("department"))
st.write("**Routing Reason:**", routing_reason)

# --------------------------------------------------
# Structured Clinical Summary
# --------------------------------------------------
st.subheader("Structured Clinical Summary")
for key, value in data.get("structured_summary", {}).items():
    st.write(f"**{key}:** {value}")

# --------------------------------------------------
# Short Doctor Summary
# --------------------------------------------------
st.subheader("Doctor-Facing Short Summary")
st.info(data.get("short_summary"))

# --------------------------------------------------
# System Decisions
# --------------------------------------------------
st.subheader("System Decisions")
st.write("**Guideline Validation:**", data.get("guideline_validation"))
st.write("**Routing Decision:**", data.get("routing_decision"))

# --------------------------------------------------
# Doctor Decision (Approve / Reject)
# --------------------------------------------------
st.subheader("Doctor Decision")

col1, col2 = st.columns(2)
decision = None

with col1:
    if st.button("✅ Approve"):
        decision = "APPROVED"

with col2:
    if st.button("❌ Reject"):
        decision = "REJECTED"

# --------------------------------------------------
# Save decision (Audit Trail)
# --------------------------------------------------
if decision:
    decision_record = {
        "patient_id": patient.get("patient_id"),
        "doctor_id": assigned_doctor.get("doctor_id"),
        "doctor_name": assigned_doctor.get("doctor_name"),
        "department": assigned_doctor.get("department"),
        "decision": decision,
        "timestamp": datetime.now().isoformat()
    }

    with open("doctor_decision_log.json", "w") as f:
        json.dump(decision_record, f, indent=4)

    st.success(f"Doctor decision recorded: {decision}")

