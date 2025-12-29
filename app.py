import json
import os
from datetime import datetime
import streamlit as st

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    page_icon="🩺",
    layout="wide"
)

# --------------------------------------------------
# Session State Initialization (CRITICAL FIX)
# --------------------------------------------------
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

# --------------------------------------------------
# Custom CSS (Professional Medical UI)
# --------------------------------------------------
st.markdown("""
<style>
body { background-color: #0e1117; }
.card {
    background-color: #161b22;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 16px;
    border: 1px solid #30363d;
}
.card h3 { color: #58a6ff; }
.label { color: #8b949e; font-size: 14px; }
.value { color: #e6edf3; font-size: 16px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Title
# --------------------------------------------------
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

patient = data.get("patient_details", {})
summary = data.get("structured_summary", {})

# --------------------------------------------------
# Layout
# --------------------------------------------------
left_col, right_col = st.columns(2)

# ================= LEFT COLUMN ====================
with left_col:
    st.markdown(f"""
    <div class="card">
        <h3>👤 Patient Details</h3>
        <div class="label">Patient ID</div><div class="value">{patient.get("patient_id")}</div><br>
        <div class="label">Age</div><div class="value">{patient.get("age")}</div><br>
        <div class="label">Gender</div><div class="value">{patient.get("gender")}</div><br>
        <div class="label">Clinical Context</div><div class="value">{patient.get("context")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>📄 Structured Clinical Summary</h3>
        <div class="value">Lab Parameter: {summary.get("Lab Parameter")}</div>
        <div class="value">Patient Value: {summary.get("Patient Value")}</div>
        <div class="value">Guideline Reference: {summary.get("Guideline Reference")}</div>
        <div class="value">Guideline Range: {summary.get("Guideline Range")}</div>
        <div class="value">AI Severity: {summary.get("AI Severity")}</div>
        <div class="value">Risk Level: {summary.get("Risk Level")}</div>
        <div class="value">Recommended Action: {summary.get("Recommended Action")}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>📝 Doctor-Facing Short Summary</h3>
        <div class="value">{data.get("short_summary")}</div>
    </div>
    """, unsafe_allow_html=True)

# ================= RIGHT COLUMN ====================
with right_col:
    st.markdown(f"""
    <div class="card">
        <h3>🧑‍⚕️ Assigned Doctor</h3>
        <div class="label">Doctor Name</div><div class="value">{assigned_doctor.get("doctor_name")}</div><br>
        <div class="label">Department</div><div class="value">{assigned_doctor.get("department")}</div><br>
        <div class="label">Routing Reason</div><div class="value">{routing_reason}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>⚙️ System Decisions</h3>
        <div class="value">Guideline Validation: {data.get("guideline_validation")}</div>
        <div class="value">Routing Decision: {data.get("routing_decision")}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- Doctor Notes ----------------
    st.markdown("### ✏️ Doctor Follow-up Instructions")

    next_ultrasound = st.text_input(
        "Next Ultrasound Name (exact test name)",
        placeholder="e.g., Anomaly Scan (Level II Ultrasound)"
    )

    next_ultrasound_week = st.text_input(
        "Scheduled Gestational Week",
        placeholder="e.g., 28 weeks"
    )

    additional_notes = st.text_area(
        "Additional Clinical Notes",
        placeholder="Any additional instructions for the patient",
        height=100
    )

    # ---------------- Doctor Decision ----------------
    st.markdown("### ✅ Doctor Decision")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("✅ Approve"):
            st.session_state.doctor_decision = "APPROVED"

    with c2:
        if st.button("❌ Reject"):
            st.session_state.doctor_decision = "REJECTED"

    # ---------------- Save Decision ----------------
    if st.session_state.doctor_decision:
        decision = st.session_state.doctor_decision

        decision_record = {
            "patient_id": patient.get("patient_id"),
            "doctor_name": assigned_doctor.get("doctor_name"),
            "department": assigned_doctor.get("department"),
            "decision": decision,
            "next_ultrasound": next_ultrasound,
            "scheduled_week": next_ultrasound_week,
            "additional_notes": additional_notes,
            "timestamp": datetime.now().isoformat()
        }

        with open("doctor_decision_log.json", "w") as f:
            json.dump(decision_record, f, indent=4)

        st.success(f"Decision recorded: {decision}")

    # ---------------- Patient Communication ----------------
    st.markdown("### 📢 Patient Communication")

    if st.session_state.doctor_decision == "APPROVED":
        st.success("Doctor-approved message for patient")

        st.write(
            "Your test results are within the normal range. "
            "Please continue routine antenatal follow-up as advised."
        )

        if next_ultrasound:
            st.info(
                f"📅 **Next Scheduled Ultrasound:** {next_ultrasound} "
                f"at {next_ultrasound_week}"
            )

        if additional_notes.strip():
            st.markdown("**Doctor’s Additional Instructions:**")
            st.info(additional_notes)
    else:
        st.warning("Patient communication will be enabled only after doctor approval.")

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("---")
st.caption("⚠️ AI outputs are assistive only. Final decisions remain with clinicians.")

