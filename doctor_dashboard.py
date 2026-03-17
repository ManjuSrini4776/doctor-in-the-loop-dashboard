import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

SEV_COLORS = {
    'Normal':'#10B981','Mild':'#F59E0B',
    'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
}
SEV_BG = {
    'Normal':'rgba(16,185,129,0.12)','Mild':'rgba(245,158,11,0.12)',
    'Moderate':'rgba(249,115,22,0.12)','Severe':'rgba(239,68,68,0.12)',
    'Unknown':'rgba(148,163,184,0.12)'
}
CT_DIAGNOSIS = {
    'notumor':   ('No Brain Tumour Detected',
                  'Normal brain scan. No suspicious mass or lesion identified.'),
    'pituitary': ('Pituitary Adenoma',
                  'Benign pituitary gland tumour. Endocrinology review recommended.'),
    'meningioma':('Meningioma',
                  'Slow-growing tumour of the meninges. Neurosurgery referral advised.'),
    'glioma':    ('Glioma',
                  'Malignant brain tumour. Urgent oncology referral required.')
}
US_DIAGNOSIS = {
    'Fetal abdomen':('Fetal Abdomen — Normal',
                     'Abdominal measurements within expected range for gestational age.'),
    'Fetal brain':  ('Fetal Brain Plane',
                     'Neurosonography plane identified. Detailed anomaly scan recommended.'),
    'Fetal femur':  ('Fetal Femur — Normal Growth',
                     'Femur length within normal range. Fetal growth on track.'),
    'Fetal thorax': ('Fetal Thorax Plane',
                     'Thoracic plane identified. Cardiac and pulmonary assessment indicated.')
}
URGENCY = {
    'Severe':   ('URGENT',      '#EF4444', 'rgba(239,68,68,0.12)'),
    'Moderate': ('SEMI-URGENT', '#F97316', 'rgba(249,115,22,0.12)'),
    'Mild':     ('ROUTINE',     '#F59E0B', 'rgba(245,158,11,0.12)'),
    'Normal':   ('ROUTINE',     '#10B981', 'rgba(16,185,129,0.12)'),
    'Unknown':  ('REVIEW',      '#94A3B8', 'rgba(148,163,184,0.12)')
}


def get_openai_client():
    try:
        from openai import OpenAI
        key = st.secrets.get('OPENAI_API_KEY',
                             os.environ.get('OPENAI_API_KEY',''))
        if key:
            return OpenAI(api_key=key)
    except Exception:
        pass
    return None


def get_rag_db():
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        emb  = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size':32}
        )
        path = 'rag_output/baseline_vector_db'
        if os.path.exists(path):
            return FAISS.load_local(
                path, emb, allow_dangerous_deserialization=True
            )
    except Exception:
        pass
    return None


def build_clinical_query(p):
    parts = []
    mtype = p.get('modality_type','')

    if 'final_severity_label' in p or mtype == 'Lab Report':
        ckd = p.get('ckd_severity','')
        dia = p.get('diabetes_severity_final','')
        thy = p.get('thyroid_severity_final','')
        sev = p.get('final_severity_label', p.get('severity_label',''))
        if ckd and str(ckd) not in ['None','nan']:
            parts.append(f"Kidney function: CKD {ckd}.")
        if dia and str(dia) not in ['None','nan']:
            parts.append(f"Diabetes status: {dia}.")
        if thy and str(thy) not in ['None','nan']:
            parts.append(f"Thyroid function: {thy}.")
        if sev:
            parts.append(f"Overall lab assessment: {sev} severity.")

    if 'ct_predicted_class' in p:
        cls  = p.get('ct_predicted_class','')
        conf = p.get('ct_confidence',0)
        name, _ = CT_DIAGNOSIS.get(cls,(cls,''))
        parts.append(f"CT scan: {name} (AI confidence {float(conf):.1%}).")

    if 'predicted_class' in p or 'us_predicted_class' in p:
        cls  = p.get('predicted_class', p.get('us_predicted_class',''))
        conf = p.get('confidence', p.get('us_confidence',0))
        name, _ = US_DIAGNOSIS.get(cls,(cls,''))
        parts.append(f"Ultrasound: {name} (AI confidence {float(conf):.1%}).")

    if p.get('symptoms'):
        parts.append(f"Patient complaints: {p['symptoms']}.")

    fus = p.get('fusion_label', p.get('severity_label','Unknown'))
    parts.append(f"Overall clinical assessment: {fus} severity.")
    return ' '.join(parts)


def generate_report(p):
    query   = build_clinical_query(p)
    fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
    name    = p.get('name','Patient')
    mtype   = p.get('modality_type','')

    urg_tag, urg_clr, _ = URGENCY.get(fus,URGENCY['Unknown'])
    action = {
        'Severe':   'Immediate specialist referral. Consider urgent admission.',
        'Moderate': 'Specialist review within 7 days. Adjust management plan.',
        'Mild':     'Outpatient follow-up within 2 to 4 weeks.',
        'Normal':   'No immediate intervention required. Routine follow-up in 3 months.'
    }.get(fus,'Discuss findings with patient and arrange appropriate follow-up.')

    # Build findings text
    findings = []
    if 'final_severity_label' in p or mtype=='Lab Report':
        ckd = p.get('ckd_severity','')
        dia = p.get('diabetes_severity_final','')
        thy = p.get('thyroid_severity_final','')
        if ckd and str(ckd) not in ['None','nan']:
            findings.append(f"Kidney function shows {ckd}.")
        if dia and str(dia) not in ['None','nan']:
            findings.append(f"Diabetes assessment: {dia}.")
        if thy and str(thy) not in ['None','nan']:
            findings.append(f"Thyroid function: {thy}.")

    if 'ct_predicted_class' in p:
        cls = p.get('ct_predicted_class','')
        name_d, detail = CT_DIAGNOSIS.get(cls,(cls,''))
        findings.append(f"CT Brain: {name_d}. {detail}")

    if 'predicted_class' in p or 'us_predicted_class' in p:
        cls = p.get('predicted_class',p.get('us_predicted_class',''))
        name_d, detail = US_DIAGNOSIS.get(cls,(cls,''))
        findings.append(f"Ultrasound: {name_d}. {detail}")

    # Try OpenAI with RAG
    client = get_openai_client()
    if client:
        context = ''
        rag_db = get_rag_db()
        if rag_db:
            try:
                docs    = rag_db.similarity_search(query, k=4)
                context = '\n\n'.join([d.page_content for d in docs])
            except Exception:
                pass

        prompt = f"""You are a clinical decision support assistant.
Generate a professional clinical summary report.
Do NOT mention AI, machine learning, scores, or system names.
Write as a standard clinical summary a doctor would produce.

Patient assessment:
{query}

{"Supporting guidelines:\n" + context if context else ""}

Format the report exactly as:
**Clinical Summary**
[2-3 sentences describing overall clinical picture]

**Key Findings**
• [finding 1]
• [finding 2]
• [finding 3 if applicable]

**Recommended Actions**
[specific next steps]

**Urgency:** {urg_tag}
**Follow-up:** [specific timeline]

End with a single line:
*This report requires doctor review and sign-off before release.*"""

        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role':'user','content':prompt}],
                temperature=0.15, max_tokens=500
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    # Clean fallback
    findings_text = '\n'.join([f'• {f}' for f in findings]) \
                    if findings else '• See modality-specific results above.'

    return f"""**Clinical Summary**
{name} presents with {fus.lower()} overall findings. {"Prompt clinical attention is warranted." if fus=="Severe" else "Clinical review and appropriate management planning is required." if fus in ["Moderate","Mild"] else "Results are within acceptable limits."}

**Key Findings**
{findings_text}

**Recommended Actions**
{action}

**Urgency:** {urg_tag}
**Follow-up:** {"Within 24 to 48 hours" if fus=="Severe" else "Within 7 to 10 days" if fus=="Moderate" else "Within 2 to 4 weeks" if fus=="Mild" else "3-month routine review"}

*This report requires doctor review and sign-off before release.*"""


def render():
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:26px;font-weight:700;color:#F1F5F9;
                    letter-spacing:-0.5px;margin-bottom:6px;">
            Doctor Dashboard
        </div>
        <div style="font-size:15px;color:#94A3B8;">
            Review patient reports, approve findings, and release results
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Doctor selector
    doctors  = st.session_state.doctors
    doc_opts = {f"{v['name']}": k for k,v in doctors.items()}
    sel_name = st.selectbox(
        'You are logged in as',
        list(doc_opts.keys()),
        key='doc_selector'
    )
    active_id = doc_opts[sel_name]
    active    = doctors[active_id]

    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1E2D40;
                border-radius:10px;padding:14px 20px;margin-bottom:20px;
                display:flex;align-items:center;gap:16px;">
        <div style="background:#1E3A5F;width:44px;height:44px;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    font-size:20px;flex-shrink:0;">🩺</div>
        <div>
            <div style="font-size:16px;font-weight:600;color:#F1F5F9;">
                {active['name']}</div>
            <div style="font-size:13px;color:#64748B;margin-top:2px;">
                {active['dept']} · {active['specialty']}</div>
        </div>
        <div style="margin-left:auto;background:rgba(16,185,129,0.12);
                    border:1px solid rgba(16,185,129,0.25);
                    color:#10B981;font-size:12px;font-weight:600;
                    padding:5px 14px;border-radius:20px;
                    font-family:'JetBrains Mono',monospace;">● ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)

    my_patients = {pid:p for pid,p in st.session_state.patients.items()
                   if p.get('doctor_id') == active_id}

    if not my_patients:
        st.markdown("""
        <div style="background:#111827;border:2px dashed #1E2D40;
                    border-radius:12px;padding:64px;text-align:center;">
            <div style="font-size:40px;margin-bottom:16px;">📭</div>
            <div style="font-size:18px;font-weight:600;color:#F1F5F9;
                        margin-bottom:8px;">No reports assigned</div>
            <div style="font-size:14px;color:#64748B;">
                Patient cases will appear here once submitted from the
                Patient Registration page.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Stats
    total   = len(my_patients)
    pending = sum(1 for p in my_patients.values() if p.get('status')=='PENDING')
    approved= sum(1 for p in my_patients.values() if p.get('status')=='APPROVED')
    urgent  = sum(1 for p in my_patients.values()
                  if p.get('fusion_label',p.get('severity_label',''))=='Severe'
                  and p.get('status')=='PENDING')

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
        ('Total Cases',     total,    '#3B82F6'),
        ('Awaiting Review', pending,  '#F59E0B'),
        ('Approved',        approved, '#10B981'),
        ('Urgent',          urgent,   '#EF4444')
    ]):
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-top:3px solid {clr};border-radius:10px;
                        padding:16px;text-align:center;margin-bottom:16px;">
                <div style="font-size:28px;font-weight:700;color:{clr};">
                    {val}</div>
                <div style="font-size:13px;color:#64748B;margin-top:4px;">
                    {lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    left, right = st.columns([1,2.2], gap='large')

    with left:
        st.markdown("""
        <div style="font-size:14px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:12px;">Cases Queue</div>
        """, unsafe_allow_html=True)

        sorted_pats = sorted(my_patients.items(), key=lambda x:(
            0 if x[1].get('fusion_label',x[1].get('severity_label',''))=='Severe' else
            1 if x[1].get('fusion_label',x[1].get('severity_label',''))=='Moderate' else
            2 if x[1].get('status')=='PENDING' else 3
        ))

        for pid,p in sorted_pats:
            status  = p.get('status','PENDING')
            fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
            clr     = SEV_COLORS.get(fus,'#94A3B8')
            is_sel  = st.session_state.current_patient == pid
            icon    = {'APPROVED':'✓','REJECTED':'✗','PENDING':'○'}.get(status,'○')
            mtype   = p.get('modality_type','')

            if st.button(
                f"{icon}  {pid}\n{p.get('name','')}  ·  {fus}",
                key=f'dpat_{pid}',
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                # Pre-generate report
                rkey = f'report_{pid}'
                if rkey not in st.session_state.reports:
                    with st.spinner('Preparing report...'):
                        st.session_state.reports[rkey] = generate_report(p)
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if not pid or pid not in my_patients:
            st.markdown("""
            <div style="background:#111827;border:2px dashed #1E2D40;
                        border-radius:12px;padding:80px;text-align:center;">
                <div style="font-size:32px;margin-bottom:12px;">👈</div>
                <div style="font-size:15px;color:#64748B;">
                    Select a case from the queue to review
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

        p       = my_patients[pid]
        fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
        fus_clr = SEV_COLORS.get(fus,'#94A3B8')
        fus_bg  = SEV_BG.get(fus,'rgba(148,163,184,0.12)')
        urg_tag, urg_clr, urg_bg = URGENCY.get(fus, URGENCY['Unknown'])
        mtype   = p.get('modality_type','')

        # Patient header
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1E2D40;
                    border-radius:12px;padding:18px 22px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;
                        align-items:flex-start;">
                <div>
                    <div style="font-size:12px;color:#64748B;
                                font-family:'JetBrains Mono',monospace;
                                margin-bottom:4px;">CASE REFERENCE</div>
                    <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                                font-family:'JetBrains Mono',monospace;">
                        {pid}</div>
                    <div style="font-size:14px;color:#94A3B8;margin-top:4px;">
                        {p.get('name','Patient')}
                    </div>
                    {f'<div style="font-size:13px;color:#64748B;margin-top:6px;">Complaint: {p.get("symptoms","")}</div>' if p.get("symptoms") else ''}
                    <div style="font-size:12px;color:#475569;margin-top:6px;">
                        Referred: {p.get('registered_at','')[:16]} ·
                        {mtype}
                    </div>
                </div>
                <div style="background:{urg_bg};border:1px solid {urg_clr}44;
                            border-radius:10px;padding:12px 18px;
                            text-align:center;min-width:130px;">
                    <div style="font-size:11px;color:{urg_clr};font-weight:700;
                                letter-spacing:0.1em;margin-bottom:6px;">
                        {urg_tag}</div>
                    <div style="font-size:18px;font-weight:700;color:{fus_clr};">
                        {fus}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Clinical Findings ────────────────────────────────
        st.markdown("""
        <div style="font-size:15px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin-bottom:14px;">Clinical Findings</div>
        """, unsafe_allow_html=True)

        # Lab findings
        if 'final_severity_label' in p or mtype=='Lab Report':
            ckd = p.get('ckd_severity','')
            dia = p.get('diabetes_severity_final','')
            thy = p.get('thyroid_severity_final','')

            c1,c2,c3 = st.columns(3)
            for col,(lbl,val) in zip([c1,c2,c3],[
                ('Kidney Function', ckd),
                ('Blood Sugar', dia),
                ('Thyroid', thy)
            ]):
                with col:
                    v = val if val and str(val) not in ['None','nan','NaN'] \
                        else 'Not available'
                    st.markdown(f"""
                    <div style="background:#0B1120;border:1px solid #1E2D40;
                                border-radius:10px;padding:14px 16px;
                                margin-bottom:12px;">
                        <div style="font-size:11px;color:#64748B;
                                    text-transform:uppercase;letter-spacing:0.06em;
                                    margin-bottom:6px;">{lbl}</div>
                        <div style="font-size:15px;font-weight:600;
                                    color:#F1F5F9;">{v}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # CT findings + GradCAM
        if 'ct_predicted_class' in p:
            ct_cls  = p.get('ct_predicted_class','')
            ct_conf = p.get('ct_confidence',0)
            ct_sev  = p.get('ct_severity_label','Unknown')
            ct_clr  = SEV_COLORS.get(ct_sev,'#94A3B8')
            diag, detail = CT_DIAGNOSIS.get(ct_cls,(ct_cls,''))

            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-left:4px solid {ct_clr};border-radius:10px;
                        padding:16px 18px;margin-bottom:12px;">
                <div style="font-size:11px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:8px;">CT Brain Scan</div>
                <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                            margin-bottom:4px;">{diag}</div>
                <div style="font-size:13px;color:#94A3B8;margin-bottom:6px;">
                    {detail}</div>
                <div style="font-size:13px;color:{ct_clr};">
                    {ct_sev} &nbsp;·&nbsp; AI Confidence: {float(ct_conf):.1%}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # GradCAM
            gradcam_path = p.get('gradcam_path','')
            if gradcam_path and os.path.exists(str(gradcam_path)):
                from PIL import Image as PILImage
                gc1, gc2 = st.columns(2)
                with gc1:
                    st.image(PILImage.open(gradcam_path),
                             caption='CT Scan — Original',
                             use_column_width=True)
                with gc2:
                    st.image(PILImage.open(gradcam_path),
                             caption='AI Attention Map',
                             use_column_width=True)
                st.markdown("""
                <div style="font-size:12px;color:#475569;margin-bottom:12px;">
                    Highlighted areas show where the AI model focused
                    to reach its conclusion.</div>
                """, unsafe_allow_html=True)

        # US findings + GradCAM
        if 'predicted_class' in p or 'us_predicted_class' in p:
            us_cls  = p.get('predicted_class',p.get('us_predicted_class',''))
            us_conf = p.get('confidence',p.get('us_confidence',0))
            us_sev  = p.get('us_severity_label','Unknown')
            us_clr  = SEV_COLORS.get(us_sev,'#94A3B8')
            diag, detail = US_DIAGNOSIS.get(us_cls,(us_cls,''))

            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-left:4px solid {us_clr};border-radius:10px;
                        padding:16px 18px;margin-bottom:12px;">
                <div style="font-size:11px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:8px;">Obstetric Ultrasound</div>
                <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                            margin-bottom:4px;">{diag}</div>
                <div style="font-size:13px;color:#94A3B8;margin-bottom:6px;">
                    {detail}</div>
                <div style="font-size:13px;color:{us_clr};">
                    {us_sev} &nbsp;·&nbsp; AI Confidence: {float(us_conf):.1%}
                </div>
            </div>
            """, unsafe_allow_html=True)

            us_gradcam = p.get('gradcam_path','')
            if us_gradcam and os.path.exists(str(us_gradcam)):
                from PIL import Image as PILImage
                ug1, ug2 = st.columns(2)
                with ug1:
                    st.image(PILImage.open(us_gradcam),
                             caption='Ultrasound — Original',
                             use_column_width=True)
                with ug2:
                    st.image(PILImage.open(us_gradcam),
                             caption='AI Attention Map',
                             use_column_width=True)

        # Fusion scores
        if 'fusion_score' in p and p.get('modalities_available',0) >= 2:
            st.markdown("""
            <div style="font-size:15px;font-weight:600;color:#94A3B8;
                        text-transform:uppercase;letter-spacing:0.08em;
                        margin:16px 0 12px;">Combined Assessment</div>
            """, unsafe_allow_html=True)
            c1,c2,c3 = st.columns(3)
            for col,(lbl,key) in zip([c1,c2,c3],[
                ('Lab Result','lab_score'),
                ('CT Result','ct_score'),
                ('Ultrasound Result','us_score')
            ]):
                with col:
                    val = p.get(key)
                    v   = str(int(val)) if val is not None and pd.notna(val) else '—'
                    sev_map = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
                    sev = sev_map.get(int(val),'—') \
                          if val is not None and pd.notna(val) else '—'
                    clr = SEV_COLORS.get(sev,'#64748B')
                    st.markdown(f"""
                    <div style="background:#0B1120;border:1px solid #1E2D40;
                                border-radius:10px;padding:14px;
                                text-align:center;margin-bottom:12px;">
                        <div style="font-size:11px;color:#64748B;
                                    text-transform:uppercase;letter-spacing:0.06em;
                                    margin-bottom:6px;">{lbl}</div>
                        <div style="font-size:26px;font-weight:700;color:#F1F5F9;">
                            {v}</div>
                        <div style="font-size:13px;color:{clr};margin-top:4px;">
                            {sev}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Clinical Report ───────────────────────────────────
        st.markdown("""
        <div style="font-size:15px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin:20px 0 12px;">Clinical Report</div>
        """, unsafe_allow_html=True)

        rkey = f'report_{pid}'
        if rkey not in st.session_state.reports:
            with st.spinner('Generating clinical report...'):
                st.session_state.reports[rkey] = generate_report(p)

        report = st.session_state.reports[rkey]

        st.markdown(f"""
        <div style="background:#0B1120;border:1px solid #1E3A5F;
                    border-left:4px solid #8B5CF6;border-radius:10px;
                    padding:20px 22px;font-size:14px;line-height:1.8;
                    color:#E2E8F0;white-space:pre-wrap;margin-bottom:8px;">
{report}
        </div>
        """, unsafe_allow_html=True)

        rc1,_ = st.columns([1,4])
        with rc1:
            if st.button('↺  Regenerate', key=f'regen_{pid}'):
                del st.session_state.reports[rkey]
                st.rerun()

        # ── Doctor Review ────────────────────────────────────
        st.markdown("""
        <div style="font-size:15px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:0.08em;
                    margin:20px 0 12px;">Your Review</div>
        """, unsafe_allow_html=True)

        edited = st.text_area(
            'Edit the report if needed',
            value=report, height=160,
            key=f'edit_{pid}',
            label_visibility='collapsed'
        )
        notes = st.text_input(
            'Clinical notes',
            placeholder='Add observations, amendments, or instructions...',
            key=f'notes_{pid}',
            label_visibility='collapsed'
        )

        st.markdown('<br>', unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)
        with b1:
            if st.button('✅  Approve & Release',
                         key=f'app_{pid}',
                         use_container_width=True,
                         type='primary'):
                st.session_state.patients[pid].update({
                    'status':       'APPROVED',
                    'final_report': edited,
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name']
                })
                st.success('✅  Report approved and released to patient.')
                st.balloons()
        with b2:
            if st.button('✏️  Approve with Edits',
                         key=f'edit_app_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':       'APPROVED',
                    'final_report': edited,
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name']
                })
                st.info('Report approved with your amendments.')
        with b3:
            if st.button('❌  Reject',
                         key=f'rej_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':       'REJECTED',
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name']
                })
                st.error('Report rejected. Patient notified to contact clinic.')

        cur = st.session_state.patients[pid].get('status','PENDING')
        if cur == 'APPROVED':
            rev  = st.session_state.patients[pid].get('reviewed_by','')
            time = st.session_state.patients[pid].get('reviewed_at','')[:16]
            st.markdown(f"""
            <div style="background:rgba(16,185,129,0.1);
                        border:1px solid rgba(16,185,129,0.25);
                        border-radius:10px;padding:14px 18px;margin-top:12px;">
                <div style="font-size:14px;font-weight:600;color:#10B981;">
                    ✅  Approved by {rev} · {time}</div>
                <div style="font-size:13px;color:#64748B;margin-top:4px;">
                    Report has been released to the patient.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button('View Patient Notification →',
                         key=f'view_{pid}'):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
