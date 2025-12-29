import json
import os
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Dashboard",
    layout="wide"
)

st.title("🩺 Doctor-in-the-Loop Clinical Dashboard")
st.caption("Evidence-based AI report validation with doctor oversight")

# ----------------------------
# LOAD DATA
# ----------------------------
JSON_PATH = "doctor_review_output.json"

if not os.path.exists(JSON_PATH):
    st.error("❌ Doctor review JSON file not found.")
    st.stop()

with open(JSON_PATH, "r") as f:
    data = json.load(f)

# ----------------------------
# LAYOUT
# ----------------------------
left, right = st.columns(2)

# ----------------------------
# LEFT COLUMN — PATIENT DETAILS
# ----------------------------
with left:
    st.subheader("👤 Patient Details")
    st.write(f"**Patient ID:** {data['patient_details']['patient_id']}")
    st.write(f"**Age:** {data['patient_details']['age']}")
    st.write(f"**Gender:** {data['patient_details']['gender']}")
    st.write(f"**Clinical Context:** {data['patient_details']['context']}")

    st.subheader("📄 Structured Clinical Summary")
    for k, v in data["structured_summary"].items():
        st.write(f"**{k}:** {v}")

# ----------------------------
# RIGHT COLUMN — DOCTOR & DECISION
# ----------------------------
with right:
    st.subheader("🧑‍⚕️ Assigned Doctor")
    st.write(f"**Doctor Name:** {data['doctor_details']['name']}")
    st.write(f"**Department:** {data['doctor_details']['department']}")
    st.write(f"**Routing Reason:** {data['doctor_details']['routing_reason']}")

    st.subheader("📝 Doctor-Facing Short Summary")
    st.info(data["short_summary"])

    st.subheader("⚙️ System Decisions")
    st.write("**Guideline Validation:**", data["guideline_validation"])
    st.write("**Routing Decision:**", data["routing_decision"])

# ----------------------------
# DOCTOR NOTES / FOLLOW-UP
# ----------------------------
st.divider()
st.subheader("✏️ Doctor Follow-up Instructions")

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
    placeholder="Add any follow-up instructions, medications, or advice..."
)

# ----------------------------
# DOCTOR DECISION
# ----------------------------
st.subheader("✅ Doctor Decision")

approve = st.button("✔ Approve")
reject = st.button("✖ Reject")

if approve:
    decision_status = "APPROVED"
elif reject:
    decision_status = "REJECTED"
else:
    decision_status = None

# ----------------------------
# PDF GENERATION FUNCTION
# ----------------------------
def generate_pdf(report_data, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Doctor-Validated Medical Report")
    y -= 30

    c.setFont("Helvetica", 10)
    for section, content in report_data.items():
        c.drawString(50, y, f"{section}:")
        y -= 15
        for k, v in content.items():
            c.drawString(70, y, f"{k}: {v}")
            y -= 15
        y -= 10

    c.drawString(50, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.save()

# ----------------------------
# AFTER APPROVAL — PATIENT COMMUNICATION
# ----------------------------
if decision_status == "APPROVED":
    st.success("Decision recorded: APPROVED")

    # Prepare report content
    pdf_data = {
        "Patient Details": data["patient_details"],
        "Doctor Details": data["doctor_details"],
        "Clinical Summary": data["structured_summary"],
        "Doctor Instructions": {
            "Next Ultrasound": next_ultrasound,
            "Doctor Notes": doctor_notes
        }
    }

    pdf_filename = f"final_report_{data['patient_details']['patient_id']}.pdf"
    generate_pdf(pdf_data, pdf_filename)

    # ----------------------------
    # PATIENT COMMUNICATION
    # ----------------------------
    st.divider()
    st.subheader("📲 Patient Communication (WhatsApp)")

    whatsapp_message = f"""
Hello,

Your medical report has been reviewed and approved by the doctor.

Summary:
• Status: Normal
• Risk Level: Low
• Next Ultrasound: {next_ultrasound}

📎 Please find your doctor-approved report attached.

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
        st.info("Message + PDF logged for audit trail")

elif decision_status == "REJECTED":
    st.error("Decision recorded: REJECTED")
    st.info("Case routed for further manual review")



