import json
import streamlit as st

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

# -----------------------------
# Load JSON (SCENARIO FILE)
# -----------------------------
JSON_PATH = "pregnancy_normal.json"   # CHANGE THIS PER SCENARIO

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -----------------------------
# Extract Core Fields
# -----------------------------
patient = data["patient_details"]
doctor = data["doctor_details"]
ai_outputs = data["ai_outputs"]
assessment = data["final_assessment"]

clinical_context = patient["clinical_context"]

# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <h2 style='color:#1f4e79;'>🩺 Doctor-in-the-Loop Clinical Dashboard</h2>
    <p style='color:gray;'>Evidence-based AI report validation with doctor oversight</p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# Debug (REMOVE later if you want)
st.write("🔍 Clinical Context Detected:", clinical_context)

# -----------------------------
# Layout
# -----------------------------
left, right = st.columns([1.2, 1])

# =============================
# LEFT COLUMN — PATIENT + AI
# =============================
with left:
    st.subheader("👤 Patient Details")
    st.info(
        f"""
        **Patient ID:** {patient['patient_id']}  
        **Age:** {patient['age']}  
        **Gender:** {patient['gender']}  
        **Clinical Context:** {clinical_context}
        """
    )

    # -------- LAB (ALWAYS SHOWN) --------
    st.subheader("🧪 Lab Summary")
    lab = ai_outputs.get("lab_summary", {})
    st.write(f"**Parameter:** {lab.get('parameter', 'N/A')}")
    st.write(f"**Value:** {lab.get('value', 'N/A')}")
    st.write(f"**Severity:** {lab.get('severity', 'N/A')}")
    st.write(f"**Guideline Range:** {lab.get('guideline_range', 'N/A')}")

    # -------- ULTRASOUND (PREGNANCY ONLY) --------
    if clinical_context == "PREGNANCY":
        st.subheader("🖥️ Ultrasound Summary")
        usg = ai_outputs.get("ultrasound_summary", {})
        st.write(f"**Finding:** {usg.get('finding', 'N/A')}")
        st.write(f"**Clinical Note:** {usg.get('clinical_note', 'N/A')}")

    # -------- CT (GENERAL ONLY) --------
    if clinical_context == "GENERAL":
        st.subheader("🧠 CT Scan Summary")
        ct = ai_outputs.get("ct_summary", {})
        st.write(f"**Finding:** {ct.get('finding', 'N/A')}")
        st.write(f"**Severity:** {ct.get('severity', 'N/A')}")

# =============================
# RIGHT COLUMN — DOCTOR
# =============================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.success(
        f"""
        **Doctor Name:** {doctor['assigned_doctor']}  
        **Department:** {doctor['department']}  
        **Routing Reason:** {doctor['routing_reason']}
        """
    )

    st.subheader("⚙️ System Decisions")
    st.write(f"**Guideline Validation:** {assessment['guideline_validation']}")
    st.write(f"**Routing Decision:** {assessment['routing_decision']}")
    st.write(f"**Risk Level:** {assessment['risk_level']}")
    st.write(f"**Recommended Action:** {assessment['recommended_action']}")

    st.subheader("✏️ Doctor Follow-up Instructions")
    doctor_notes = st.text_area(
        "Add or edit follow-up details (e.g., next visit, ultrasound name, tests):",
        placeholder="Example: Next ultrasound – Anomaly Scan at 28 weeks"
    )

    st.subheader("✅ Doctor Decision")
    col1, col2 = st.columns(2)

    approved = False

    with col1:
        if st.button("Approve"):
            approved = True
            st.success("Decision Approved")

    with col2:
        if st.button("Reject"):
            st.error("Decision Rejected – Doctor Review Required")

# =============================
# PATIENT COMMUNICATION (ONLY AFTER APPROVE)
# =============================
if approved:
    st.markdown("---")
    st.subheader("📩 Patient Communication (After Doctor Approval)")

    st.info(
        f"""
        **Message to Patient:**  
        Your test results are normal.  
        Lab values are within guideline limits, and ultrasound findings are reassuring.  
        Please continue routine antenatal follow-up as advised.

        **Doctor Notes:**  
        {doctor_notes if doctor_notes else "No additional instructions provided."}
        """
    )

    st.write("📎 **Reports shared:**")
    st.write("- Lab report PDF")
    if clinical_context == "PREGNANCY":
        st.write("- Ultrasound report PDF")

