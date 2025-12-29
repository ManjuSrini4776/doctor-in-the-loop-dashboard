import json
import os
from datetime import datetime
import streamlit as st

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Dashboard",
    page_icon="🩺",
    layout="centered"
)

st.markdown("## 🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# --------------------------------------------------
# Load JSON
# --------------------------------------------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("doctor_review_output.json not found in repository")
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
    routing_reason = "Ordering doctor available"
else:
    assigned_doctor = fallback_doctor
    routing_reason = "Ordering doctor unavailable → routed to same department"

# --------------------------------------------------
# PATIENT DETAILS (CARD)
# --------------------------------------------------
st.markdown("### 👤 Patient Details")
patient = data.get("patient_details", {})

with st.container():
    st.markdown(
        f"""
        **Patient ID:** {patient.get("patient_id")}  
        **Age:** {patient.get("age")}  
        **Gender:** {patient.get("gender")}  
        **Clinical Context:** {patient.get("context")}
        """
    )

# --------------------------------------------------
# ASSIGNED DOCTOR (CARD)
# --------------------------------------------------
st.markdown("### 🧑‍⚕️ Assigned Doctor")

with st.container():
    st.markdown(
        f"""
        **Doctor Name:** {assigned_doctor.get("doctor_name")}  
        **Department:** {assigned_doctor.get("department")}  
        **Routing Reason:** {routing_reason}
        """
    )

# --------------------------------------------------
# STRUCTURED CLINICAL SUMMARY
# --------------------------------------------------
st.markdown("### 📄 Structured Clinical Summary")

structured_summary = data.get("structured_summary", {})

for key, value in structured_summary.items():
    st.markdown(f"- **{key}:** {value}")

# --------------------------------------------------
# SHORT DOCTOR SUMMARY (HIGHLIGHT)
# --------------------------------------------------
st.markdown("### 📝 Doctor-Facing Short Summary")
st.info(data.get("short_summary"))

# --------------------------------------------------
# SYSTEM DECISIONS
# --------------------------------------------------
st.markdown("### ⚙️ System Decisions")

col1, col2 = st.columns(2)
with col1:
    st.success(f"Guideline Validation: {data.get('guideline_validation')}")
with col2:
    st.info(f"Routing Decision: {data.get('routing_decision')}")

# --------------------------------------------------
# DOCTOR EDITABLE NOTES
# --------------------------------------------------
st.markdown("### ✏️ Doctor Notes / Follow-up Instructions")

doctor_notes = st.text_area(
    "Add or edit follow-up details (next visit, ultrasound, tests, etc.)",
    value=data.get("doctor_notes", ""),
    height=130
)

# --------------------------------------------------
# DOCTOR DECISION
# --------------------------------------------------
st.markdown("### ✅ Doctor Decision")

approve_col, reject_col = st.columns(2)
decision = None

with approve_col:
    if st.button("✅ Approve Report"):
        decision = "APPROVED"

with reject_col:
    if st.button("❌ Reject Report"):
        decision = "REJECTED"

# --------------------------------------------------
# SAVE AUDIT LOG
# --------------------------------------------------
if decision:
    decision_record = {
        "patient_id": patient.get("patient_id"),
        "doctor_id": assigned_doctor.get("doctor_id"),
        "doctor_name": assigned_doctor.get("doctor_name"),
        "department": assigned_doctor.get("department"),
        "decision": decision,
        "doctor_notes": doctor_notes,
        "timestamp": datetime.now().isoformat()
    }

    with open("doctor_decision_log.json", "w") as f:
        json.dump(decision_record, f, indent=4)

    st.success(f"Doctor decision recorded: {decision}")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption(
    "⚠️ AI-generated outputs are assistive only. Final decisions remain with the clinician."
)

