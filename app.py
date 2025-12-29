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
# Custom CSS (UI Styling)
# --------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.card {
    background-color: #161b22;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
    border: 1px solid #30363d;
}
.card h3 {
    color: #58a6ff;
}
.label {
    color: #8b949e;
    font-size: 14px;
}
.value {
    color: #e6edf3;
    font-size: 16px;
    font-weight: 500;
}
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
    st.error("doctor_review_output.json not found")
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
# Layout Columns
# --------------------------------------------------
left_col, right_col = st.columns(2)

# --------------------------------------------------
# LEFT: PATIENT & CLINICAL DETAILS
# --------------------------------------------------
with left_col:
    st.markdown("""
    <div class="card">
        <h3>👤 Patient Details</h3>
        <div class="label">Patient ID</div>
        <div class="value">{pid}</div><br>
        <div class="label">Age</div>
        <div class="value">{age}</div><br>
        <div class="label">Gender</div>
        <div class="value">{gender}</div><br>
        <div class="label">Clinical Context</div>
        <div class="value">{context}</div>
    </div>
    """.format(
        pid=patient.get("patient_id"),
        age=patient.get("age"),
        gender=patient.get("gender"),
        context=patient.get("context")
    ), unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📄 Structured Clinical Summary</h3>
        <div class="value">Lab Parameter: {param}</div>
        <div class="value">Patient Value: {val}</div>
        <div class="value">Guideline Reference: {guide}</div>
        <div class="value">Guideline Range: {range}</div>
        <div class="value">AI Severity: {sev}</div>
        <div class="value">Risk Level: {risk}</div>
        <div class="value">Recommended Action: {act}</div>
    </div>
    """.format(
        param=summary.get("Lab Parameter"),
        val=summary.get("Patient Value"),
        guide=summary.get("Guideline Reference"),
        range=summary.get("Guideline Range"),
        sev=summary.get("AI Severity"),
        risk=summary.get("Risk Level"),
        act=summary.get("Recommended Action")
    ), unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>📝 Doctor-Facing Short Summary</h3>
        <div class="value">{text}</div>
    </div>
    """.format(
        text=data.get("short_summary")
    ), unsafe_allow_html=True)

# --------------------------------------------------
# RIGHT: DOCTOR & DECISIONS
# --------------------------------------------------
with right_col:
    st.markdown("""
    <div class="card">
        <h3>🧑‍⚕️ Assigned Doctor</h3>
        <div class="label">Doctor Name</div>
        <div class="value">{doc}</div><br>
        <div class="label">Department</div>
        <div class="value">{dept}</div><br>
        <div class="label">Routing Reason</div>
        <div class="value">{reason}</div>
    </div>
    """.format(
        doc=assigned_doctor.get("doctor_name"),
        dept=assigned_doctor.get("department"),
        reason=routing_reason
    ), unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>⚙️ System Decisions</h3>
        <div class="value">Guideline Validation: {gv}</div>
        <div class="value">Routing Decision: {rd}</div>
    </div>
    """.format(
        gv=data.get("guideline_validation"),
        rd=data.get("routing_decision")
    ), unsafe_allow_html=True)

    st.markdown("### ✏️ Doctor Notes")
    doctor_notes = st.text_area(
        "Add follow-up instructions",
        value=data.get("doctor_notes", ""),
        height=120
    )

    st.markdown("### ✅ Doctor Decision")
    c1, c2 = st.columns(2)
    decision = None

    with c1:
        if st.button("✅ Approve"):
            decision = "APPROVED"

    with c2:
        if st.button("❌ Reject"):
            decision = "REJECTED"

    if decision:
        record = {
            "patient_id": patient.get("patient_id"),
            "doctor_name": assigned_doctor.get("doctor_name"),
            "department": assigned_doctor.get("department"),
            "decision": decision,
            "doctor_notes": doctor_notes,
            "timestamp": datetime.now().isoformat()
        }

        with open("doctor_decision_log.json", "w") as f:
            json.dump(record, f, indent=4)

        st.success(f"Decision recorded: {decision}")

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("---")
st.caption("⚠️ AI outputs are assistive only. Final decisions remain with clinicians.")
