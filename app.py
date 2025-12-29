import json
import streamlit as st

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

# -------------------------------
# Load data
# -------------------------------
JSON_PATH = "doctor_review_output.json"

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# -------------------------------
# Session state initialization
# -------------------------------
if "decision" not in st.session_state:
    st.session_state.decision = None

if "doctor_notes" not in st.session_state:
    st.session_state.doctor_notes = ""

# -------------------------------
# Header
# -------------------------------
st.markdown(
    """
    <h1 style='color:#6EA8FE;'>🩺 Doctor-in-the-Loop Clinical Dashboard</h1>
    <p style='color:gray;'>Evidence-based AI report validation with doctor oversight</p>
    """,
    unsafe_allow_html=True
)

st.divider()

# -------------------------------
# Layout: Patient | Doctor
# -------------------------------
left, right = st.columns(2, gap="large")

# ===============================
# LEFT COLUMN — PATIENT & AI INFO
# ===============================
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {data['patient_details']['patient_id']}")
    st.write(f"**Age:** {data['patient_details']['age']}")
    st.write(f"**Gender:** {data['patient_details']['gender']}")
    st.write(f"**Clinical Context:** {data['patient_details']['context']}")

    st.divider()

    st.subheader("📄 Structured Clinical Summary")
    summary = data["structured_summary"]

    st.write(f"**Lab Parameter:** {summary['lab_parameter']}")
    st.write(f"**Patient Value:** {summary['patient_value']}")
    st.write(f"**Guideline Reference:** {summary['guideline_reference']}")
    st.write(f"**Guideline Range:** {summary['guideline_range']}")
    st.write(f"**AI Severity:** {summary['ai_severity']}")
    st.write(f"**Risk Level:** {summary['risk_level']}")
    st.write(f"**Recommended Action:** {summary['recommended_action']}")

    # Pregnancy-specific ultrasound info
    if data["patient_details"]["context"] == "Pregnancy":
        st.divider()
        st.subheader("🩻 Ultrasound Status")
        st.write(f"**Current Ultrasound:** {data['ultrasound']['current_status']}")
        st.write(f"**Next Scheduled Scan:** {data['ultrasound']['next_scan']}")

    st.divider()

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["short_summary"])

# ===============================
# RIGHT COLUMN — DOCTOR ACTIONS
# ===============================
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {data['doctor']['name']}")
    st.write(f"**Department:** {data['doctor']['department']}")
    st.write(f"**Routing Reason:** {data['doctor']['routing_reason']}")

    st.divider()

    st.subheader("✏️ Doctor Notes / Follow-up Instructions")
    st.session_state.doctor_notes = st.text_area(
        "Add follow-up instructions (next visit, ultrasound, tests, etc.)",
        value=st.session_state.doctor_notes,
        height=120,
        placeholder="Example: Next ultrasound – Anomaly Scan at 28 weeks"
    )

    st.divider()

    st.subheader("✅ Doctor Decision")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✔ Approve"):
            st.session_state.decision = "APPROVED"

    with col2:
        if st.button("❌ Reject"):
            st.session_state.decision = "REJECTED"

    if st.session_state.decision:
        if st.session_state.decision == "APPROVED":
            st.success("Decision recorded: APPROVED")
        else:
            st.error("Decision recorded: REJECTED")

# -------------------------------
# PATIENT COMMUNICATION (LOCKED → ENABLED)
# -------------------------------
st.divider()
st.subheader("📢 Patient Communication")

if st.session_state.decision != "APPROVED":
    st.warning("Patient communication will be enabled after doctor approval.")
else:
    patient_msg = f"""
    Your fasting blood sugar is {summary['patient_value']}, which is within the
    WHO guideline range ({summary['guideline_range']}).

    Risk level is LOW. No immediate hospital visit is required.

    Ultrasound status:
    - Current: {data['ultrasound']['current_status']}
    - Next scan: {data['ultrasound']['next_scan']}

    Doctor instructions:
    {st.session_state.doctor_notes if st.session_state.doctor_notes else "Follow routine antenatal care."}
    """

    st.success("✅ Patient communication approved and ready to send")
    st.text_area("Message to Patient (SMS / WhatsApp / PDF)", patient_msg, height=180)

# -------------------------------
# SYSTEM DECISIONS
# -------------------------------
st.divider()
st.subheader("⚙️ System Decisions")
st.write(f"**Guideline Validation:** {data['guideline_validation']}")
st.write(f"**Routing Decision:** {data['routing_decision']}")

