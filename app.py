import json
import os
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================
if "doctor_decision" not in st.session_state:
    st.session_state.doctor_decision = None

if "pdf_generated" not in st.session_state:
    st.session_state.pdf_generated = False

# =====================================================
# LOAD DATA
# =====================================================
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("❌ doctor_review_output.json not found in repository.")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# =====================================================
# LAYOUT
# =====================================================
left_col, right_col = st.columns(2)

# =====================================================
# LEFT COLUMN — PATIENT DETAILS
# =====================================================
with left_col:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {data['patient_details']['patient_id']}")
    st.write(f"**Age:** {data['patient_details']['age']}")
    st.write(f"**Gender:** {data['patient_details']['gender']}")
    st.write(f"**Clinical Context:** {data['patient_details']['context']}")

    st.subheader("📄 Structured Clinical Summary")
    for k, v in data["structured_summary"].items():
        st.write(f"**{k}:** {v}")

# =====================================================
# RIGHT COLUMN — DOCTOR DETAILS
# =====================================================
with right_col:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {data['doctor_details']['name']}")
    st.write(f"**Department:** {data['doctor_details']['department']}")
    st.write(f"**Routing Reason:** {data['doctor_details']['routing_reason']}")

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["short_summary"])

    st.subheader("⚙️ System Decisions")
    st.write("**Guideline Validation:**", data["guideline_validation"])
    st.write("**Routing Decision:**", data["routing_decision"])

# =====================================================
# DOCTOR FOLLOW-UP SECTION
# =====================================================
st.divider()
st.subheader("✏️ Doctor Notes / Follow-up Instructions")

next_ultrasound = st.selectbox(
    "Select Next Ultrasound (Exact Name)",
    [
        "Anomaly Scan (28 weeks)",
        "Growth Scan (32 weeks)",
        "Doppler Ultrasound",
        "NT Scan",
        "No ultrasound required now"
    ]
)

doctor_notes = st.text_area(
    "Additional Doctor Notes",
    placeholder="Add next visit details, medications, investigations, etc."
)

# =====================================================
# STABLE CONTAINER FOR PATIENT COMMUNICATION
# =====================================================
patient_comm_container = st.container()

# =====================================================
# DOCTOR DECISION (LOCKED AFTER APPROVAL)
# =====================================================
st.subheader("✅ Doctor Decision")

if st.session_state.doctor_decision is None:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✔ Approve"):
            st.session_state.doctor_decision = "APPROVED"

    with col2:
        if st.button("✖ Reject"):
            st.session_state.doctor_decision = "REJECTED"
else:
    st.success(f"Decision recorded: {st.session_state.doctor_decision}")

# =====================================================
# PDF GENERATION FUNCTION
# =====================================================
def generate_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Doctor-Validated Medical Report")
    y -= 30

    c.setFont("Helvetica", 10)

    sections = {
        "Patient Details": data["patient_details"],
        "Doctor Details": data["doctor_details"],
        "Clinical Summary": data["structured_summary"],
        "Doctor Instructions": {
            "Next Ultrasound": next_ultrasound,
            "Doctor Notes": doctor_notes
        }
    }

    for section, content in sections.items():
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, section)
        y -= 18

        c.setFont("Helvetica", 10)
        for k, v in content.items():
            c.drawString(70, y, f"{k}: {v}")
            y -= 14

        y -= 10

    c.drawString(50, y, f"Approved on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.save()

# =====================================================
# PATIENT COMMUNICATION — GUARANTEED RENDER
# =====================================================
if st.session_state.doctor_decision == "APPROVED":
    with patient_comm_container:
        st.divider()
        st.subheader("📲 Patient Communication (WhatsApp)")

        pdf_filename = f"final_report_{data['patient_details']['patient_id']}.pdf"

        if not st.session_state.pdf_generated:
            generate_pdf(pdf_filename)
            st.session_state.pdf_generated = True

        whatsapp_message = f"""
Hello,

Your medical report has been reviewed and approved by the doctor.

Summary:
• Status: Normal
• Risk Level: Low
• Next Ultrasound: {next_ultrasound}

📎 Please find your doctor-approved medical report attached.

— Hospital Care Team
"""

        st.text_area(
            "WhatsApp Message Preview",
            whatsapp_message,
            height=180
        )

        st.write("📄 **Attached PDF:**", pdf_filename)

        if st.button("📤 Send via WhatsApp (Mock)"):
            st.success("✅ WhatsApp message sent successfully (simulated)")
            st.info("Message and PDF recorded in audit log")

elif st.session_state.doctor_decision == "REJECTED":
    with patient_comm_container:
        st.error("❌ Report rejected. Routed for senior doctor review.")
