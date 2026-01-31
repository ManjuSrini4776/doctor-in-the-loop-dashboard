import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="Doctor-in-the-Loop Clinical Review Dashboard",
    layout="wide"
)

# -------------------------------------------------------
# CSS
# -------------------------------------------------------
st.markdown("""
<style>

.block-container { padding-top: 1rem; }

.card {
    padding:16px;
    border-radius:14px;
    background:#ffffff;
    border:1px solid #e5e7eb;
}

.card-title{font-size:14px;color:#374151;}
.card-value{font-size:26px;font-weight:700;color:#111827;}

.card-blue{ background:#eef4ff; }
.card-green{ background:#ecfdf3; }
.card-yellow{ background:#fff7ed; }

.section-box{
    padding:18px;
    border-radius:14px;
    border:1px solid #e5e7eb;
    background:#0b1220;
    color:white;
}

.header-bar{
    padding:12px 16px;
    border-radius:12px;
    background:#f1f5f9;
    border:1px solid #e5e7eb;
    font-size:14px;
    color:#111827;
}

.status-ok{
    padding:14px;
    border-radius:10px;
    background:#0f3d2e;
    color:#34f5a3;
    font-weight:600;
}

.status-warn{
    padding:14px;
    border-radius:10px;
    background:#3b1d1d;
    color:#ffb4b4;
    font-weight:600;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Title
# -------------------------------------------------------
st.markdown(
    "<h1 style='color:white'>Doctor-in-the-Loop Clinical Review Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='color:#9ca3af'>Workflow-driven AI clinical triage and reporting system</div>",
    unsafe_allow_html=True
)

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------
st.sidebar.markdown("## Clinical workflow")

page = st.sidebar.radio(
    "",
    ["Overview","Clinical Evidence","Guideline Summary","Doctor Decision","Patient Communication"]
)

st.sidebar.divider()

st.sidebar.markdown("### Case selection")

case_list = ["CT_001 | CT Brain"]
selected_case = st.sidebar.selectbox("Select case", case_list)

pid, modality = selected_case.split(" | ")

# -------------------------------------------------------
# Load JSON
# -------------------------------------------------------
DATA_PATH = Path("data/ct_demo_with_rag.json")

with open(DATA_PATH,"r") as f:
    data = json.load(f)

patient  = data.get("patient_details",{})
ct_out   = data.get("ct_model_output",{})
fusion   = data.get("ai_severity_fusion",{})
imaging  = data.get("imaging_evidence",{})

validation_decision = data.get("validation_decision","-")
validation_reason   = data.get("validation_reason","-")
rag_imaging_sources = data.get("rag_imaging_sources",[])
rag_pathway_sources = data.get("rag_pathway_sources",[])
doctor_summary      = data.get("doctor_facing_summary","-")

# -------------------------------------------------------
# Session state  (IMPORTANT FIX)
# -------------------------------------------------------
if "case_status" not in st.session_state:
    st.session_state.case_status = "PENDING"

try:
    conf = round(float(ct_out.get("confidence",0))*100,2)
except:
    conf = "-"

# -------------------------------------------------------
# Header bar
# -------------------------------------------------------
st.markdown(
    f"""
    <div class="header-bar">
    Clinical review workspace |
    Case: {pid} |
    Modality: {modality} |
    Workflow: Doctor-in-the-loop validation
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# -------------------------------------------------------
# Case status (shown on ALL pages)
# -------------------------------------------------------
if st.session_state.case_status == "APPROVED":
    st.markdown('<div class="status-ok">Case status: Approved by doctor</div>',unsafe_allow_html=True)
elif st.session_state.case_status == "REJECTED":
    st.markdown('<div class="status-warn">Case status: Rejected by doctor</div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="status-warn">Case status: Pending doctor review</div>',unsafe_allow_html=True)

st.write("")

# ======================================================
# OVERVIEW
# ======================================================
if page == "Overview":

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="card card-blue">
            <div class="card-title">Patient ID</div>
            <div class="card-value">{pid}</div>
        </div>
        """,unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card card-green">
            <div class="card-title">CT prediction</div>
            <div class="card-value">{ct_out.get("prediction","-")}</div>
        </div>
        """,unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card card-yellow">
            <div class="card-title">Final severity</div>
            <div class="card-value">{fusion.get("derived_severity","-")}</div>
        </div>
        """,unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="card card-blue">
            <div class="card-title">Model confidence</div>
            <div class="card-value">{conf}%</div>
        </div>
        """,unsafe_allow_html=True)

    st.write("")

    left,right = st.columns(2)

    with left:
        st.markdown("<div class='section-box'>",unsafe_allow_html=True)
        st.markdown("### Imaging evidence")
        st.write("Modality:", modality)
        st.write("Image ID:", imaging.get("image_id","-"))

        img_path = imaging.get("image_path")
        if img_path and Path(img_path).exists():
        st.image(img_path, use_container_width=True)


        st.markdown("</div>",unsafe_allow_html=True)

    with right:
        st.markdown("<div class='section-box'>",unsafe_allow_html=True)
        st.markdown("### Clinical validation")
        st.write("Validation decision:",validation_decision)
        st.write("Reason:",validation_reason)
        st.write("Patient context:",patient.get("context","-"))
        st.markdown("</div>",unsafe_allow_html=True)

# ======================================================
# CLINICAL EVIDENCE
# ======================================================
elif page == "Clinical Evidence":

    st.markdown("<div class='section-box'>",unsafe_allow_html=True)
    st.markdown("### CT AI evidence")
    st.write("Prediction:",ct_out.get("prediction","-"))
    st.write("Confidence:",conf,"%")
    st.write("Image ID:",imaging.get("image_id","-"))
    st.markdown("</div>",unsafe_allow_html=True)

# ======================================================
# GUIDELINE SUMMARY
# ======================================================
elif page == "Guideline Summary":

    st.markdown("<div class='section-box'>",unsafe_allow_html=True)
    st.markdown("### Doctor-facing RAG summary")
    st.write(doctor_summary)
    st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("<div class='section-box'>",unsafe_allow_html=True)
    st.markdown("### Retrieved guideline sources")
    st.write("Imaging KB:")
    for s in rag_imaging_sources:
        st.write("-",s)
    st.write("Pathway KB:")
    for s in rag_pathway_sources:
        st.write("-",s)
    st.markdown("</div>",unsafe_allow_html=True)

# ======================================================
# DOCTOR DECISION
# ======================================================
elif page == "Doctor Decision":

    st.markdown("<div class='section-box'>",unsafe_allow_html=True)

    st.markdown("### Doctor review & decision")

    edited = st.text_area(
        "Clinical summary (editable)",
        doctor_summary,
        height=200
    )

    col1,col2 = st.columns(2)

    with col1:
        if st.button("Approve case"):
            st.session_state.case_status = "APPROVED"

            final_output = {
                "patient_id":pid,
                "modality":modality,
                "image_id":imaging.get("image_id"),
                "ct_prediction":ct_out.get("prediction"),
                "confidence":ct_out.get("confidence"),
                "final_severity":fusion.get("derived_severity"),
                "patient_context":patient.get("context"),
                "validation_decision":validation_decision,
                "validation_reason":validation_reason,
                "rag_imaging_sources":rag_imaging_sources,
                "rag_pathway_sources":rag_pathway_sources,
                "doctor_facing_summary":edited,
                "doctor_decision":"APPROVED",
                "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.success("Case approved")

            st.json(final_output)

            st.download_button(
                "Download approved JSON",
                json.dumps(final_output,indent=4),
                file_name=f"{pid}_doctor_output.json",
                mime="application/json"
            )

    with col2:
        if st.button("Reject case"):
            st.session_state.case_status="REJECTED"
            st.error("Case rejected")

    st.markdown("</div>",unsafe_allow_html=True)

# ======================================================
# PATIENT COMMUNICATION  (UPDATED MESSAGE)
# ======================================================
elif page == "Patient Communication":

    st.markdown("<div class='section-box'>",unsafe_allow_html=True)

    st.markdown("### Patient communication")

    if st.session_state.case_status!="APPROVED":
        st.warning("Patient communication is locked until doctor approval.")
    else:

        patient_message = f"""Hello,

Your CT brain report has been reviewed and approved by your doctor.

Patient ID : {pid}
Result     : {ct_out.get("prediction")}
Severity   : {fusion.get("derived_severity")}

The findings are normal and there is no indication of a brain tumour in this scan.
At this time, there is no need for an immediate hospital visit.

If you notice any new symptoms or would like further clarification, please contact your doctor or schedule a follow-up consultation.

Regards,
Hospital Care Team
"""

        st.text_area("Patient message preview",patient_message,height=260)

    st.markdown("</div>",unsafe_allow_html=True)
