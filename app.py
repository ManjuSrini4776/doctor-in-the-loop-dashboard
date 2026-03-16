# ============================================================
# app.py — Doctor-in-the-Loop Multimodal Medical AI Dashboard
# Streamlit Cloud Production Version
# ============================================================

import streamlit as st
import json
import pandas as pd
import numpy as np
import os
from datetime import datetime
from pipeline import run_rag_pipeline

st.set_page_config(
    page_title="MedAI Doctor Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.dash-header {
    background: linear-gradient(135deg, #0a1f3c 0%, #1a3f6f 60%, #1e5799 100%);
    padding: 1.2rem 1.8rem; border-radius: 12px; margin-bottom: 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
}
.dash-title { color: white; font-size: 1.35rem; font-weight: 600; margin: 0; }
.dash-sub   { color: rgba(255,255,255,0.6); font-size: 0.78rem; margin-top: 3px; }
.dash-tag   { background: rgba(255,255,255,0.12); color: #7dd3fc;
              font-size: 0.72rem; padding: 4px 10px; border-radius: 20px;
              border: 1px solid rgba(125,211,252,0.3); }

.metric-card {
    background: white; border: 1px solid #e8edf2; border-radius: 10px;
    padding: 1rem 1.2rem; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.metric-val   { font-size: 1.9rem; font-weight: 600; line-height: 1.1; }
.metric-label { font-size: 0.7rem; color: #6b7280; text-transform: uppercase;
                letter-spacing: 0.06em; margin-top: 3px; }
.metric-sub   { font-size: 0.7rem; color: #94a3b8; margin-top: 2px; }

.badge { display:inline-block; padding:3px 10px; border-radius:20px;
         font-size:0.7rem; font-weight:600; letter-spacing:0.03em; }
.badge-pending  { background:#FFF3E0; color:#854F0B; }
.badge-approved { background:#E8F5E9; color:#2E7D32; }
.badge-rejected { background:#FFEBEE; color:#C62828; }
.badge-edited   { background:#E3F2FD; color:#1565C0; }
.badge-severe   { background:#FFEBEE; color:#C62828; }
.badge-moderate { background:#FFF3E0; color:#854F0B; }
.badge-mild     { background:#E8F5E9; color:#2E7D32; }
.badge-normal   { background:#E3F2FD; color:#1565C0; }
.badge-unknown  { background:#F1F5F9; color:#64748b; }

.section-title {
    font-size:0.7rem; font-weight:600; color:#94a3b8;
    text-transform:uppercase; letter-spacing:0.08em;
    margin-bottom:0.5rem; margin-top:0.2rem;
}
.report-box {
    background:#f8fafc; border:1px solid #e2e8f0;
    border-left:4px solid #1a3f6f; border-radius:8px;
    padding:1rem 1.2rem; font-size:0.87rem; line-height:1.8;
    color:#1e293b; white-space:pre-wrap;
}
.evidence-chip {
    display:inline-block; background:#EBF5FB; color:#185FA5;
    border:1px solid #B5D4F4; border-radius:6px;
    padding:2px 9px; font-size:0.7rem; margin:2px;
    font-family:'DM Mono',monospace;
}
.info-box  { background:#EBF5FB; border:1px solid #B5D4F4; border-radius:8px;
             padding:0.8rem 1rem; font-size:0.82rem; color:#1565C0; margin-bottom:0.8rem; }
.warn-box  { background:#FFF8E1; border:1px solid #FFE082; border-radius:8px;
             padding:0.8rem 1rem; font-size:0.82rem; color:#854F0B; margin-bottom:0.8rem; }
.sev-bar-wrap { background:#e2e8f0; border-radius:4px; height:6px; margin-top:4px; }
.sev-bar      { height:6px; border-radius:4px; }
#MainMenu { visibility:hidden; } footer { visibility:hidden; } header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Paths
DATA_PATH   = "data/fusion_patient_context.csv"
RAG_PATH    = "data/rag_output.json"
REVIEW_PATH = "data/doctor_review_output.json"

SEVERITY_COLORS = {
    "Severe":"#C62828","Moderate":"#F28E2B",
    "Mild":"#2E7D32","Normal":"#1565C0","Unknown":"#64748b"
}

# ── Data helpers
@st.cache_data(ttl=300)
def load_patients():
    try:
        df = pd.read_csv(DATA_PATH)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
        df["case_id"] = df["case_id"].astype(str)
        def get_type(row):
            ct = str(row.get("ct_disease","")).lower()
            us = str(row.get("ultrasound_disease","")).lower()
            if "fetal" in us or "pregnancy" in us: return "Pregnancy"
            if any(t in ct for t in ["glioma","meningioma","pituitary","tumor"]): return "Tumor"
            if pd.notna(row.get("lab_score")): return "Chronic/Lab"
            return "General"
        df["patient_type"] = df.apply(get_type, axis=1)
        return df
    except Exception:
        return _demo()

def _demo():
    return pd.DataFrame([
        {"case_id":"23529134","lab_score":2.0,"ct_score":None,"ct_disease":None,
         "ultrasound_score":None,"ultrasound_disease":None,"fusion_score":2.0,
         "final_severity":"Moderate","patient_type":"Chronic/Lab"},
        {"case_id":"Tr-gl_0042","lab_score":2.0,"ct_score":3.0,"ct_disease":"glioma",
         "ultrasound_score":None,"ultrasound_disease":None,"fusion_score":3.0,
         "final_severity":"Severe","patient_type":"Tumor"},
        {"case_id":"216","lab_score":None,"ct_score":None,"ct_disease":None,
         "ultrasound_score":3.0,"ultrasound_disease":"Fetal brain","fusion_score":3.0,
         "final_severity":"Severe","patient_type":"Pregnancy"},
        {"case_id":"25259089","lab_score":2.0,"ct_score":None,"ct_disease":None,
         "ultrasound_score":None,"ultrasound_disease":None,"fusion_score":2.0,
         "final_severity":"Moderate","patient_type":"Chronic/Lab"},
        {"case_id":"Tr-me_0010","lab_score":None,"ct_score":2.0,"ct_disease":"meningioma",
         "ultrasound_score":None,"ultrasound_disease":None,"fusion_score":2.0,
         "final_severity":"Moderate","patient_type":"Tumor"},
        {"case_id":"305","lab_score":None,"ct_score":None,"ct_disease":None,
         "ultrasound_score":1.0,"ultrasound_disease":"Fetal abdomen","fusion_score":1.0,
         "final_severity":"Mild","patient_type":"Pregnancy"},
        {"case_id":"29467146","lab_score":3.0,"ct_score":None,"ct_disease":None,
         "ultrasound_score":None,"ultrasound_disease":None,"fusion_score":3.0,
         "final_severity":"Severe","patient_type":"Chronic/Lab"},
    ])

def load_rag_outputs():
    try:
        with open(RAG_PATH,"r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(i["case_id"]): i for i in data}
        return {str(k): v for k,v in data.items()}
    except Exception:
        return {}

def load_reviews():
    try:
        with open(REVIEW_PATH,"r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_review(cid, decision, report, notes, delivery, ptype, sev):
    os.makedirs("data", exist_ok=True)
    reviews = load_reviews()
    reviews[str(cid)] = {
        "case_id": str(cid), "decision": decision,
        "edited_report": report, "doctor_notes": notes,
        "delivery": delivery, "patient_type": ptype,
        "severity": sev,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(REVIEW_PATH,"w") as f:
        json.dump(reviews, f, indent=2)

def save_rag(cid, result):
    os.makedirs("data", exist_ok=True)
    outputs = load_rag_outputs()
    outputs[str(cid)] = result
    with open(RAG_PATH,"w") as f:
        json.dump(list(outputs.values()), f, indent=2)

def sev_color(s):  return SEVERITY_COLORS.get(str(s),"#64748b")
def sev_badge(s):  return f"badge-{str(s).lower()}" if s else "badge-unknown"
def score_pct(v):
    try: return min(int(float(v)/3*100),100)
    except: return 0

# ── Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:0.8rem 0 0.5rem;'>
        <div style='font-size:2.2rem;'>🏥</div>
        <div style='font-weight:600;font-size:1rem;color:#0a1f3c;'>MedAI Dashboard</div>
        <div style='font-size:0.7rem;color:#94a3b8;margin-top:2px;'>Doctor-in-the-Loop</div>
    </div>
    <hr style='border:none;border-top:1px solid #e2e8f0;margin:0.6rem 0;'>
    """, unsafe_allow_html=True)

    page = st.radio("nav", label_visibility="collapsed", options=[
        "🏠 Overview","👨‍⚕️ Review Queue",
        "✅ Approved Reports","📊 RAG Analytics","ℹ️ About",
    ])

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:0.6rem 0;'>",
                unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)
    f_type = st.multiselect("Patient Type",
        ["Pregnancy","Tumor","Chronic/Lab","General"],
        default=["Pregnancy","Tumor","Chronic/Lab","General"])
    f_sev  = st.multiselect("Severity",
        ["Severe","Moderate","Mild","Normal"], default=["Severe","Moderate"])
    f_stat = st.multiselect("Review Status",
        ["Pending","Approved","Rejected","Edited"], default=["Pending"])
    show_n = st.slider("Patients per page", 10, 100, 25)

# ── Load data
patients_df = load_patients()
rag_outputs = load_rag_outputs()
reviews     = load_reviews()

patients_df["status"] = patients_df["case_id"].astype(str).apply(
    lambda c: reviews.get(c,{}).get("decision","Pending")
)
fdf = patients_df.copy()
if f_type: fdf = fdf[fdf["patient_type"].isin(f_type)]
if f_sev:  fdf = fdf[fdf["final_severity"].apply(
    lambda s: any(f.lower() in str(s).lower() for f in f_sev))]
if f_stat: fdf = fdf[fdf["status"].isin(f_stat)]

# ══════════════ OVERVIEW ══════════════
if page == "🏠 Overview":
    st.markdown(f"""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>🏥 Doctor-in-the-Loop Medical AI Dashboard</div>
            <div class='dash-sub'>Multimodal AI · RAG-Validated Reports · Doctor Approval · {datetime.now().strftime("%d %b %Y")}</div>
        </div>
        <div style='display:flex;flex-direction:column;gap:6px;align-items:flex-end;'>
            <span class='dash-tag'>Page Index RAG · Faith 0.692</span>
            <span class='dash-tag'>Hierarchical RAG · Relev 0.701</span>
        </div>
    </div>""", unsafe_allow_html=True)

    total=len(patients_df); pending=len(patients_df[patients_df["status"]=="Pending"])
    approved=len(patients_df[patients_df["status"]=="Approved"])
    rejected=len(patients_df[patients_df["status"]=="Rejected"])
    severe=len(patients_df[patients_df["final_severity"].str.contains("Severe",na=False)])
    preg=len(patients_df[patients_df["patient_type"]=="Pregnancy"])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col,val,lbl,sub,color in [
        (c1,total,"Total Patients","All modalities","#0a1f3c"),
        (c2,pending,"Pending Review","Needs doctor","#854F0B"),
        (c3,approved,"Approved","Reports released","#2E7D32"),
        (c4,rejected,"Rejected","Needs regen","#C62828"),
        (c5,severe,"Severe Cases","Priority queue","#C62828"),
        (c6,preg,"Pregnancy","Chronic follow-up","#4A148C"),
    ]:
        col.markdown(f"""
        <div class='metric-card' style='border-top:3px solid {color};'>
            <div class='metric-val' style='color:{color};'>{val}</div>
            <div class='metric-label'>{lbl}</div>
            <div class='metric-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2.5,1.2])

    with cl:
        st.markdown("<div class='section-title'>Priority Queue — Severe & Moderate Cases</div>",
                    unsafe_allow_html=True)
        pq = patients_df[patients_df["final_severity"].isin(["Severe","Moderate"])]\
            .sort_values("fusion_score",ascending=False,na_position="last").head(15)
        show_cols = [c for c in ["case_id","patient_type","final_severity",
                                  "ct_disease","ultrasound_disease","fusion_score","status"]
                     if c in pq.columns]
        st.dataframe(pq[show_cols], use_container_width=True, hide_index=True,
            column_config={
                "case_id": st.column_config.TextColumn("Patient ID",width=120),
                "patient_type": st.column_config.TextColumn("Type",width=100),
                "final_severity": st.column_config.TextColumn("Severity",width=90),
                "ct_disease": st.column_config.TextColumn("CT Finding",width=110),
                "ultrasound_disease": st.column_config.TextColumn("US Finding",width=120),
                "fusion_score": st.column_config.NumberColumn("Score",format="%.1f",width=70),
                "status": st.column_config.TextColumn("Status",width=90),
            })

    with cr:
        st.markdown("<div class='section-title'>Severity Distribution</div>",
                    unsafe_allow_html=True)
        sev_c = patients_df["final_severity"].value_counts()
        for s in ["Severe","Moderate","Mild","Normal"]:
            cnt=sev_c.get(s,0); pct=int(cnt/max(total,1)*100); c=sev_color(s)
            st.markdown(f"""
            <div style='margin-bottom:9px;'>
                <div style='display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:3px;'>
                    <span style='font-weight:500;'>{s}</span>
                    <span style='color:#64748b;'>{cnt} ({pct}%)</span>
                </div>
                <div class='sev-bar-wrap'><div class='sev-bar' style='width:{pct}%;background:{c};'></div></div>
            </div>""", unsafe_allow_html=True)

        reviewed=approved+rejected; pd2=int(reviewed/max(total,1)*100)
        st.markdown(f"""
        <div style='margin-top:1rem;background:#f0fdf4;border:1px solid #86efac;
                    border-radius:8px;padding:0.8rem;'>
            <div style='font-size:0.72rem;font-weight:600;color:#166534;margin-bottom:5px;'>
                💡 Impact</div>
            <div style='font-size:0.75rem;color:#166534;line-height:1.6;'>
                <b>{approved}</b> reports approved<br>
                <b>{preg}</b> pregnancy follow-ups<br>
                Reducing unnecessary revisits
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════ REVIEW QUEUE ══════════════
elif page == "👨‍⚕️ Review Queue":
    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>👨‍⚕️ Doctor Review Queue</div>
            <div class='dash-sub'>Select patient → View AI analysis → Review → Approve / Edit / Reject → Deliver</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if fdf.empty:
        st.info("No patients match filters. Adjust sidebar.")
        st.stop()

    cq, cd = st.columns([1,2.8])

    with cq:
        st.markdown(f"<div class='section-title'>Queue ({len(fdf)})</div>",
                    unsafe_allow_html=True)
        if "selected_patient" not in st.session_state:
            st.session_state.selected_patient = str(
                fdf.sort_values("fusion_score",ascending=False,na_position="last").iloc[0]["case_id"])

        sdf = fdf.sort_values("fusion_score",ascending=False,na_position="last").head(show_n)
        type_icon = {"Pregnancy":"🤰","Tumor":"🧠","Chronic/Lab":"🧪","General":"👤"}

        for _, row in sdf.iterrows():
            cid=str(row["case_id"]); sev=str(row.get("final_severity","Unknown"))
            status=str(row.get("status","Pending")); ptype=str(row.get("patient_type","General"))
            active = cid==st.session_state.selected_patient
            icon = type_icon.get(ptype,"👤")

            if st.button(f"{'▶ ' if active else ''}{icon} #{cid}",
                         key=f"q_{cid}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.selected_patient=cid; st.rerun()

            sb=sev_badge(sev)
            pb={"Pending":"badge-pending","Approved":"badge-approved",
                "Rejected":"badge-rejected","Edited":"badge-edited"}.get(status,"badge-pending")
            st.markdown(f"""
            <div style='font-size:0.7rem;color:#64748b;margin:-8px 0 8px 2px;'>
                <span class='badge {sb}'>{sev}</span>
                <span class='badge {pb}'>{status}</span>
            </div>""", unsafe_allow_html=True)

    with cd:
        cid=st.session_state.selected_patient
        pat=patients_df[patients_df["case_id"].astype(str)==cid]
        if pat.empty: st.warning("Patient not found."); st.stop()
        p=pat.iloc[0]; sev=str(p.get("final_severity","Unknown"))
        ptype=str(p.get("patient_type","General")); score=p.get("fusion_score",None)
        icon=type_icon.get(ptype,"👤"); sc=sev_color(sev)

        st.markdown(f"""
        <div style='background:#f8fafc;border:1px solid #e2e8f0;
                    border-left:4px solid {sc};border-radius:10px;
                    padding:1rem 1.2rem;margin-bottom:1rem;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='font-size:1.1rem;font-weight:600;color:#0a1f3c;'>
                        {icon} Patient #{cid}</div>
                    <div style='font-size:0.75rem;color:#64748b;margin-top:3px;'>
                        {ptype} · Multimodal AI Assessment</div>
                </div>
                <span class='badge {sev_badge(sev)}' style='font-size:0.8rem;padding:5px 14px;'>{sev}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Context messages
        if ptype=="Pregnancy":
            st.markdown("<div class='info-box'>🤰 <b>Pregnancy Follow-up</b> — If findings are normal, approve for WhatsApp delivery to avoid unnecessary hospital revisit.</div>",
                        unsafe_allow_html=True)
        elif ptype=="Chronic/Lab":
            st.markdown("<div class='info-box'>🧪 <b>Chronic Disease Patient</b> — Regular monitoring case. Approve with next appointment to reduce revisits.</div>",
                        unsafe_allow_html=True)
        elif sev=="Severe":
            st.markdown("<div class='warn-box'>⚠️ <b>Severe Case</b> — Immediate attention required. Review carefully before approving.</div>",
                        unsafe_allow_html=True)

        # Score cards
        s1,s2,s3,s4 = st.columns(4)
        for col,lbl,val,color in [
            (s1,"Lab Score",p.get("lab_score"),"#1565C0"),
            (s2,"CT Score",p.get("ct_score"),"#C62828"),
            (s3,"Ultrasound",p.get("ultrasound_score"),"#2E7D32"),
            (s4,"Fusion Score",score,sc),
        ]:
            d = f"{float(val):.1f}" if val and str(val) not in ["nan","None",""] else "—"
            col.markdown(f"""
            <div class='metric-card' style='border-top:3px solid {color};padding:0.7rem;'>
                <div class='metric-val' style='color:{color};font-size:1.4rem;'>{d}</div>
                <div class='metric-label'>{lbl}</div>
            </div>""", unsafe_allow_html=True)

        # Findings chips
        findings=[]
        if str(p.get("ct_disease","")).lower() not in ["nan","none",""]:
            findings.append(f"🧠 CT: {p['ct_disease']}")
        if str(p.get("ultrasound_disease","")).lower() not in ["nan","none",""]:
            findings.append(f"🔊 US: {p['ultrasound_disease']}")
        if findings:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(" ".join([f"<span class='evidence-chip'>{f}</span>" for f in findings]),
                        unsafe_allow_html=True)

        # RAG Report
        st.markdown("<br><div class='section-title'>AI-Generated Clinical Report (RAG)</div>",
                    unsafe_allow_html=True)
        existing = reviews.get(cid,{}); rag_data=rag_outputs.get(cid,{})
        default_report=rag_data.get("report","")

        if not default_report:
            cg,ci=st.columns([1,2])
            with cg:
                gen=st.button("⚡ Generate RAG Report",type="primary",
                               key=f"gen_{cid}",use_container_width=True)
            with ci:
                st.markdown("<div style='font-size:0.78rem;color:#64748b;padding-top:0.5rem;'>"
                            "Page Index RAG + Domain Filter + GPT-4o-mini</div>",
                            unsafe_allow_html=True)
            if gen:
                with st.spinner("Retrieving guidelines & generating report..."):
                    try:
                        result=run_rag_pipeline(p.to_dict())
                        default_report=result.get("report","Generation failed.")
                        save_rag(cid,result); st.success("✅ Report generated!"); st.rerun()
                    except Exception as e:
                        st.error(f"Pipeline error: {e}")
        else:
            rag_type=rag_data.get("rag_type","Page Index RAG")
            faith=rag_data.get("faithfulness",0.692)
            sources=rag_data.get("sources",[])
            st.markdown(
                f"<span class='evidence-chip'>🤖 {rag_type}</span>"
                f"<span class='evidence-chip'>Faith: {faith:.3f}</span>"
                +"".join([f"<span class='evidence-chip'>📄 {s}</span>" for s in sources[:4]]),
                unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        edited=st.text_area("report_edit",
            value=existing.get("edited_report",default_report),
            height=220,key=f"rep_{cid}",
            placeholder="RAG report appears here. Edit before approving.",
            label_visibility="collapsed")

        st.markdown("<div class='section-title' style='margin-top:0.6rem;'>Doctor Notes</div>",
                    unsafe_allow_html=True)
        notes=st.text_area("notes_edit",
            value=existing.get("doctor_notes",""),height=80,key=f"nts_{cid}",
            placeholder="Add observations, corrections, next appointment, patient instructions...",
            label_visibility="collapsed")

        st.markdown("<div class='section-title' style='margin-top:0.6rem;'>Deliver Approved Report Via</div>",
                    unsafe_allow_html=True)
        prev=existing.get("delivery",[])
        d1,d2,d3,d4=st.columns(4)
        dpdf=d1.checkbox("📄 PDF",    value="PDF" in prev,       key=f"pdf_{cid}")
        dwa =d2.checkbox("💬 WhatsApp",value="WhatsApp" in prev, key=f"wa_{cid}")
        dem =d3.checkbox("📧 Email",  value="Email" in prev,     key=f"em_{cid}")
        drec=d4.checkbox("💾 Record", value="Record" in prev,    key=f"rc_{cid}")
        delivery=(["PDF"]*dpdf+["WhatsApp"]*dwa+["Email"]*dem+["Record"]*drec)

        st.markdown("<br>", unsafe_allow_html=True)
        b1,b2,b3,b4=st.columns(4)

        with b1:
            if st.button("✅ Approve & Send",key=f"app_{cid}",
                         use_container_width=True,type="primary"):
                if not edited: st.error("Generate report first!")
                else:
                    save_review(cid,"Approved",edited,notes,delivery,ptype,sev)
                    st.success(f"✅ Report approved & queued for delivery!")
                    st.balloons(); st.rerun()
        with b2:
            if st.button("💾 Save Edits",key=f"sv_{cid}",use_container_width=True):
                save_review(cid,"Edited",edited,notes,delivery,ptype,sev)
                st.info("💾 Saved."); st.rerun()
        with b3:
            if st.button("🔄 Regenerate",key=f"rg_{cid}",use_container_width=True):
                outputs=load_rag_outputs()
                if cid in outputs:
                    del outputs[cid]
                    with open(RAG_PATH,"w") as f: json.dump(list(outputs.values()),f,indent=2)
                st.warning("Cleared — click Generate"); st.rerun()
        with b4:
            if st.button("❌ Reject",key=f"rej_{cid}",use_container_width=True):
                save_review(cid,"Rejected",edited,notes,delivery,ptype,sev)
                st.warning(f"❌ Rejected."); st.rerun()

        cur_status=reviews.get(cid,{}).get("decision","Pending")
        if cur_status=="Approved" and edited:
            st.markdown("<br>", unsafe_allow_html=True)
            rpt=(f"{'='*60}\nDOCTOR-APPROVED CLINICAL REPORT\n{'='*60}\n"
                 f"Patient ID  : {cid}\nType        : {ptype}\nSeverity    : {sev}\n"
                 f"Date        : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n\n"
                 f"{edited}\n\nDoctor Notes:\n{notes}\n\nDelivery: {', '.join(delivery)}\n"
                 f"{'='*60}\nReviewed and approved by a licensed physician.\n")
            st.download_button("⬇️ Download Approved Report",data=rpt,
                file_name=f"report_{cid}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",use_container_width=True)

# ══════════════ APPROVED REPORTS ══════════════
elif page == "✅ Approved Reports":
    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>✅ Doctor-Reviewed Reports Log</div>
            <div class='dash-sub'>All approved, edited and rejected reports · Export</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if not reviews:
        st.info("No reviews yet. Go to Review Queue.")
        st.stop()

    appr=[v for v in reviews.values() if v.get("decision")=="Approved"]
    edit=[v for v in reviews.values() if v.get("decision")=="Edited"]
    rejt=[v for v in reviews.values() if v.get("decision")=="Rejected"]

    t1,t2,t3,t4=st.tabs([f"✅ Approved ({len(appr)})",
                          f"✏️ Edited ({len(edit)})",
                          f"❌ Rejected ({len(rejt)})",
                          f"📋 All ({len(reviews)})"])

    def show_table(rlist, expandable=True):
        if not rlist: st.info("No records."); return
        df=pd.DataFrame(rlist)
        cols=[c for c in ["case_id","patient_type","severity","decision",
                           "timestamp","delivery","doctor_notes"] if c in df.columns]
        st.dataframe(df[cols],use_container_width=True,hide_index=True)
        cl,_=st.columns([1,3])
        with cl:
            st.download_button("⬇️ Export CSV",data=df.to_csv(index=False),
                file_name=f"reviews_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")
        if expandable:
            for rev in rlist[:10]:
                with st.expander(f"Patient #{rev['case_id']} · {rev.get('patient_type','')} · {rev.get('timestamp','')}"):
                    st.markdown(f"<div class='report-box'>{rev.get('edited_report','—')}</div>",
                                unsafe_allow_html=True)
                    if rev.get("doctor_notes"):
                        st.markdown(f"**Doctor Notes:** {rev['doctor_notes']}")
                    st.download_button("⬇️ Download",data=rev.get("edited_report",""),
                        file_name=f"report_{rev['case_id']}.txt",mime="text/plain",
                        key=f"dl_{rev['case_id']}")

    with t1: show_table(appr)
    with t2: show_table(edit)
    with t3: show_table(rejt, expandable=False)
    with t4: show_table(list(reviews.values()), expandable=False)

# ══════════════ RAG ANALYTICS ══════════════
elif page == "📊 RAG Analytics":
    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>📊 RAG Performance Analytics</div>
            <div class='dash-sub'>Baseline vs Hierarchical vs Page Index · V1 vs V2</div>
        </div>
    </div>""", unsafe_allow_html=True)

    try: import plotly.graph_objects as go
    except: st.error("pip install plotly"); st.stop()

    rl=["Baseline","Hierarchical","Page Index"]
    fv1=[0.5606,0.4687,0.4461]; fv2=[0.4568,0.4180,0.6919]
    rv1=[0.4718,0.3922,0.5664]; rv2=[0.4634,0.7012,0.6050]
    lat=[2.764,2.559,3.619]

    c1,c2,c3,c4=st.columns(4)
    for col,val,lbl,sub,color in [
        (c1,"0.692","Best Faithfulness","Page Index V2 +0.246","#2E7D32"),
        (c2,"0.701","Best Relevancy","Hierarchical V2 +0.309","#2E7D32"),
        (c3,"2.56s","Fastest RAG","Hierarchical V2","#1565C0"),
        (c4,"~0.62","Avg Score V2","from ~0.51 V1","#854F0B"),
    ]:
        col.markdown(f"""
        <div class='metric-card' style='border-top:3px solid {color};'>
            <div class='metric-val' style='color:{color};'>{val}</div>
            <div class='metric-label'>{lbl}</div>
            <div class='metric-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    C1,C2="#A8C4DC","#1F5F8B"

    def gbar(v1,v2,title):
        fig=go.Figure()
        fig.add_trace(go.Bar(name="V1 Original",x=rl,y=v1,marker_color=C1,
            text=[f"{x:.3f}" for x in v1],textposition="outside"))
        fig.add_trace(go.Bar(name="V2 Improved",x=rl,y=v2,marker_color=C2,
            text=[f"{x:.3f}" for x in v2],textposition="outside"))
        fig.update_layout(title=title,barmode="group",
            yaxis=dict(range=[0,1],title="Score"),
            plot_bgcolor="white",paper_bgcolor="white",
            legend=dict(orientation="h",y=-0.25),
            height=340,margin=dict(t=40,b=70,l=40,r=20),
            font=dict(family="DM Sans, sans-serif"))
        fig.update_xaxes(showgrid=False); fig.update_yaxes(gridcolor="#f1f5f9")
        return fig

    cl,cr=st.columns(2)
    with cl: st.plotly_chart(gbar(fv1,fv2,"Faithfulness ↑"),use_container_width=True)
    with cr: st.plotly_chart(gbar(rv1,rv2,"Answer Relevancy ↑"),use_container_width=True)

    cl2,cr2=st.columns(2)
    with cl2:
        ml=max(lat); cats=["Faithfulness","Answer Relevancy","Speed","Faithfulness"]
        rc={"Baseline":"#4E79A7","Hierarchical":"#F28E2B","Page Index":"#59A14F"}
        fig3=go.Figure()
        for name,f,r,la in [("Baseline",fv2[0],rv2[0],lat[0]),
                              ("Hierarchical",fv2[1],rv2[1],lat[1]),
                              ("Page Index",fv2[2],rv2[2],lat[2])]:
            spd=round(1-la/ml,3)
            fig3.add_trace(go.Scatterpolar(r=[f,r,spd,f],theta=cats,fill="toself",
                name=name,line_color=rc[name],fillcolor=rc[name],opacity=0.25))
        fig3.update_layout(title="V2 Quality Profile",
            polar=dict(radialaxis=dict(visible=True,range=[0,1])),
            plot_bgcolor="white",paper_bgcolor="white",
            legend=dict(orientation="h",y=-0.2),
            height=360,margin=dict(t=50,b=70,l=40,r=40),
            font=dict(family="DM Sans, sans-serif"))
        st.plotly_chart(fig3,use_container_width=True)

    with cr2:
        df2=[round(b-a,4) for a,b in zip(fv1,fv2)]
        dr2=[round(b-a,4) for a,b in zip(rv1,rv2)]
        fig4=go.Figure()
        fig4.add_trace(go.Bar(name="Faithfulness Δ",x=rl,y=df2,
            marker_color=["#2E7D32" if d>=0 else "#C62828" for d in df2],
            text=[f"{'+' if d>=0 else ''}{d:.3f}" for d in df2],textposition="outside"))
        fig4.add_trace(go.Bar(name="Relevancy Δ",x=rl,y=dr2,
            marker_color=["#52b788" if d>=0 else "#e63946" for d in dr2],
            text=[f"{'+' if d>=0 else ''}{d:.3f}" for d in dr2],
            textposition="outside",opacity=0.8))
        fig4.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
        fig4.update_layout(title="V1 → V2 Score Delta",barmode="group",
            yaxis=dict(title="Δ Score"),plot_bgcolor="white",paper_bgcolor="white",
            legend=dict(orientation="h",y=-0.25),
            height=360,margin=dict(t=50,b=70,l=40,r=20),
            font=dict(family="DM Sans, sans-serif"))
        fig4.update_xaxes(showgrid=False); fig4.update_yaxes(gridcolor="#f1f5f9")
        st.plotly_chart(fig4,use_container_width=True)

# ══════════════ ABOUT ══════════════
elif page == "ℹ️ About":
    st.markdown("""
    <div class='dash-header'>
        <div>
            <div class='dash-title'>ℹ️ About This System</div>
            <div class='dash-sub'>Doctor-in-the-Loop Multimodal Medical AI Reporting System</div>
        </div>
    </div>""", unsafe_allow_html=True)

    cl,cr=st.columns(2)
    with cl:
        st.markdown("### 🎯 Project Goal")
        st.markdown("""
An AI-assisted clinical decision support system that interprets **multimodal medical data**
(lab reports, CT scans, ultrasound images) and generates structured reports —
reviewed and approved by a doctor before patient delivery.

**Key problem solved:** Reducing unnecessary hospital revisits for:
- 🤰 Pregnancy follow-up patients (normal ultrasound results)
- 🧪 Chronic disease patients (regular lab monitoring)
        """)
        st.markdown("### 🔬 AI Modules")
        st.markdown("""
| Module | Dataset | Output |
|---|---|---|
| CT Scan Model | Kaggle Brain Tumor | Tumor type + severity |
| Ultrasound Model | PlaneDB | Fetal plane + severity |
| Lab Module | MIMIC-4 | Lab severity score |
| Fusion Layer | All 3 combined | Final clinical severity |
| RAG Module | WHO/Clinical guidelines | Grounded report |
        """)

    with cr:
        st.markdown("### 📊 RAG Results")
        st.markdown("""
| RAG Type | Faithfulness | Relevancy |
|---|---|---|
| Baseline V1 | 0.5606 | 0.4718 |
| Hierarchical V1 | 0.4687 | 0.3922 |
| Page Index V1 | 0.4461 | 0.5664 |
| **Page Index V2** | **0.692 ✅** | 0.605 |
| **Hierarchical V2** | 0.418 | **0.701 ✅** |
        """)
        st.markdown("### 🔄 Workflow")
        st.markdown("""
```
Patient Data (Lab + CT + Ultrasound)
            ↓
  Multimodal AI Analysis
            ↓
  Fusion Severity Score
            ↓
  RAG Report Generation
  (Page Index + Domain Filter)
            ↓
  Doctor Review Dashboard
  (Approve / Edit / Reject)
            ↓
  Deliver to Patient
  (WhatsApp / SMS / PDF / Email)
```
        """)

    st.markdown("### 👥 Impact")
    c1,c2,c3=st.columns(3)
    for col,icon,title,desc in [
        (c1,"⏱️","Faster Diagnosis","AI pre-analyzes — doctor reviews summary not raw data"),
        (c2,"🏠","Fewer Revisits","Normal reports delivered digitally — no hospital visit needed"),
        (c3,"✅","Clinical Safety","Doctor approves every report — AI assists, doctor decides"),
    ]:
        col.markdown(f"""
        <div class='metric-card' style='text-align:left;'>
            <div style='font-size:1.5rem;margin-bottom:6px;'>{icon}</div>
            <div style='font-weight:600;font-size:0.9rem;color:#0a1f3c;margin-bottom:4px;'>{title}</div>
            <div style='font-size:0.78rem;color:#64748b;line-height:1.5;'>{desc}</div>
        </div>""", unsafe_allow_html=True)
