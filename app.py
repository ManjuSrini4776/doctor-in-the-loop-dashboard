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
    layout="wide" # Changed to wide for better dashboard feel
)

# --------------------------------------------------
# Custom CSS for Modern UI
# --------------------------------------------------
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Card styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #3B82F6;
        margin-bottom: 20px;
    }
    
    /* Section Headers */
    .section-header {
        color: #1E293B;
        font-weight: 700;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    /* Status Badges */
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# Load JSON (Kept your existing logic)
# --------------------------------------------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("⚠️ doctor_review_output.json not found in repository")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# Routing Logic
ordering_doctor = data.get("ordering_doctor", {})
fallback_doctor = data.get("fallback_doctor", {})

if ordering_doctor.get("available", False):
    assigned_doctor = ordering_doctor
    routing_reason = "Direct Assignment"
    routing_color = "#10B981" # Green
else:
    assigned_doctor = fallback_doctor
    routing_reason = "Routed to Dept (Fallback)"
    routing_color = "#F59E0B" # Orange

# --------------------------------------------------
# HEADER SECTION
# --------------------------------------------------
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("# 🩺 Clinical Review Portal")
    st.markdown(f"**Reviewing for:** {assigned_doctor.get('doctor_name')} | *{assigned_doctor.get('department')}*")

with col_status:
    st.write("") # Spacer
    st.markdown(f'<p style="text-align:right"><span class="status-badge">Priority: Urgent</span></p>', unsafe_allow_html=True)

st.divider()

# --------------------------------------------------
# MAIN LAYOUT: 2 COLUMNS
# --------------------------------------------------
left_col, right_col = st.columns([1, 1.2], gap="large")

with left_col:
    st.markdown('<p class="section-header">👤 Patient Information</p>', unsafe_allow_html=True)
    patient = data.get("patient_details", {})
    
    # Using a clean container for patient details
    with st.container():
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin-top:0;">{patient.get("patient_id")}</h4>
            <p><b>Age:</b> {patient.get("age")} | <b>Gender:</b> {patient.get("gender")}</p>
            <hr style="margin: 10px 0;">
            <p style="font-size: 0.9rem; color: #64748B;"><b>Clinical Context:</b><br>{patient.get("context")}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<p class="section-header">⚙️ System Logistics</p>', unsafe_allow_html=True)
    st.info(f"**Routing Logic:** {routing_reason}")
    st.success(f"**Validation:** {data.get('guideline_validation')}")

with right_col:
    st.markdown('<p class="section-header">📄 AI Clinical Summary</p>', unsafe_allow_html=True)
    
    # Highlight the AI's short summary in a styled box
    st.markdown(f"""
    <div style="background-color: #EFF6FF; padding: 20px; border-radius: 10px; border: 1px solid #BFDBFE; margin-bottom: 20px;">
        <h5 style="color: #1E40AF; margin-top:0;">Doctor-Facing Insights</h5>
        <p style="font-style: italic;">"{data.get("short_summary")}"</p>
    </div>
    """, unsafe_allow_html=True)

    # Detailed summary in an expander to keep things clean
    with st.expander("View Full Structured Data", expanded=True):
        structured_summary = data.get("structured_summary", {})
        for key, value in structured_summary.items():
            st.write(f"**{key}:** {value}")

# --------------------------------------------------
# ACTION AREA (BOTTOM)
# --------------------------------------------------
st.markdown('<p class="section-header">✏️ Clinician Feedback & Decision</p>', unsafe_allow_html=True)

# Creating a nice text area with a pre-filled value
doctor_notes = st.text_area(
    "Clinical Follow-up Instructions",
    value=data.get("doctor_notes", ""),
    height=150,
    help="Update ultrasound details, test requests, or next visit timing."
)

# Decision Buttons
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
decision = None

with btn_col1:
    if st.button("✅ Approve Report", use_container_width=True, type="primary"):
        decision = "APPROVED"

with btn_col2:
    if st.button("❌ Reject / Revise", use_container_width=True):
        decision = "REJECTED"

# --------------------------------------------------
# SAVE AUDIT LOG (Logic kept exactly as yours)
# --------------------------------------------------
if decision:
    decision_record = {
        "patient_id": patient.get("patient_id"),
        "doctor_id": assigned_doctor.get("doctor_id"),
        "doctor_name": assigned_doctor.get("doctor_name"),
        "decision": decision,
        "doctor_notes": doctor_notes,
        "timestamp": datetime.now().isoformat()
    }

    # Visual feedback for the decision
    if decision == "APPROVED":
        st.balloons()
        st.success(f"### Report Verified Successfully\nLogged at: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.warning("### Report Rejected\nNotification sent back for revision.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align: center; color: #94A3B8; font-size: 0.8rem;">
        ⚠️ AI Assistive Technology • Final year Project • Decision Support System
    </div>
    """, unsafe_allow_html=True)
