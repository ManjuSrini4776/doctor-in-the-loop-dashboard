import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

SEV_COLORS = {
    'Normal':'#10B981','Mild':'#F59E0B',
    'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
}
CT_CLINICAL = {
    'notumor':    ('No Intracranial Tumor', 'Normal brain scan. No suspicious lesion identified.'),
    'pituitary':  ('Pituitary Adenoma', 'Benign pituitary gland tumor. Endocrinology review recommended.'),
    'meningioma': ('Meningioma', 'Slow-growing tumor of the meninges. Neurosurgery referral advised.'),
    'glioma':     ('Glioma', 'Malignant brain tumor. Urgent oncology referral required.')
}
US_CLINICAL = {
    'Fetal abdomen': ('Fetal Abdomen', 'Normal fetal abdominal plane. Measurements within expected range.'),
    'Fetal brain':   ('Fetal Brain', 'Fetal neurosonography plane. Detailed anomaly scan recommended.'),
    'Fetal femur':   ('Fetal Femur', 'Normal femur length for gestational age. Growth on track.'),
    'Fetal thorax':  ('Fetal Thorax', 'Thoracic plane identified. Cardiac and lung assessment indicated.')
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
        emb  = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2',
                                     encode_kwargs={'batch_size':32})
        path = 'rag_output/baseline_vector_db'
        if os.path.exists(path):
            return FAISS.load_local(path, emb,
                                    allow_dangerous_deserialization=True)
    except Exception:
        pass
    return None


def generate_ai_report(patient: dict) -> str:
    """Generate clinical report. Uses OpenAI if available, else fallback."""
    ct_cls = patient.get('ct_predicted_class','')
    us_cls = patient.get('us_predicted_class','')
    fus    = patient.get('fusion_label','Unknown')
    name   = patient.get('name', 'Patient')

    # Build clinical query for RAG
    parts = []
    if patient.get('lab_score') is not None:
        parts.append(
            f"Lab: {patient.get('lab_severity_label','Unknown')} chronic disease. "
            f"CKD stage {patient.get('ckd_severity','N/A')}, "
            f"Diabetes {patient.get('diabetes_severity_final','N/A')}, "
            f"Thyroid {patient.get('thyroid_severity_final','N/A')}."
        )
    if patient.get('ct_score') is not None:
        ct_name, _ = CT_CLINICAL.get(ct_cls, (ct_cls, ''))
        parts.append(
            f"CT scan: {ct_name} "
            f"(confidence {patient.get('ct_confidence',0):.1%})."
        )
    if patient.get('us_score') is not None:
        us_name, _ = US_CLINICAL.get(us_cls, (us_cls, ''))
        parts.append(
            f"Ultrasound: {us_name} "
            f"(confidence {patient.get('us_confidence',0):.1%})."
        )
    parts.append(f"Overall assessment: {fus} severity.")
    if patient.get('symptoms'):
        parts.append(f"Presenting symptoms: {patient['symptoms']}.")
    query = ' '.join(parts)

    # Try RAG + OpenAI
    context = ''
    rag_db  = get_rag_db()
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            pass

    client = get_openai_client()
    if client:
        prompt = f"""You are a clinical decision support assistant in a hospital AI system.
Generate a professional clinical report for the doctor to review.

Patient Assessment:
{query}

{"Clinical Guidelines Reference:\n" + context if context else ""}

Write a structured clinical report. Be concise and professional.
Do NOT mention AI, scores, or technical system details.
Write as if this is a standard clinical summary report.

Format:
**Clinical Summary:** <2-3 sentences describing the overall clinical picture>

**Key Findings:**
- <finding 1>
- <finding 2>
- <finding 3 if applicable>

**Recommended Actions:** <specific clinical next steps>

**Urgency:** <Routine / Semi-urgent / Urgent>

**Follow-up:** <timeline and what to monitor>"""

        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role':'user','content':prompt}],
                temperature=0.2, max_tokens=450
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    # Clean fallback — no technical jargon
    urgency = ('Urgent' if fus=='Severe' else
               'Semi-urgent' if fus=='Moderate' else 'Routine')
    actions = {
        'Severe':   'Immediate specialist referral required. Consider admission.',
        'Moderate': 'Specialist review within 7 days. Adjust current treatment plan.',
        'Mild':     'Outpatient follow-up within 2-4 weeks. Monitor progression.',
        'Normal':   'No immediate intervention required. Routine follow-up in 3 months.'
    }.get(fus, 'Discuss findings with patient and arrange appropriate follow-up.')

    ct_name, ct_detail = CT_CLINICAL.get(ct_cls, ('',''))
    us_name, us_detail = US_CLINICAL.get(us_cls, ('',''))

    findings = []
    if patient.get('lab_score') is not None:
        findings.append(
            f"Laboratory results indicate {patient.get('lab_severity_label','unknown')} "
            f"chronic disease burden with CKD stage "
            f"{patient.get('ckd_severity','not recorded')}."
        )
    if ct_name:
        findings.append(f"CT imaging: {ct_detail}")
    if us_name:
        findings.append(f"Ultrasound: {us_detail}")

    findings_text = '\n'.join([f'• {f}' for f in findings]) if findings else '• See individual modality reports.'

    return f"""**Clinical Summary:** {name} presents with {fus.lower()} overall findings across multimodal assessment. {"Immediate clinical attention is warranted." if fus=="Severe" else "Clinical review and management plan required." if fus=="Moderate" else "Continued monitoring is advised."}

**Key Findings:**
{findings_text}

**Recommended Actions:** {actions}

**Urgency:** {urgency}

**Follow-up:** {"Within 24-48 hours" if fus=="Severe" else "Within 7-10 days" if fus=="Moderate" else "Within 2-4 weeks" if fus=="Mild" else "3 months routine review"}

---
*This report was generated with AI assistance and requires doctor review before release.*"""


def render():
    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;border-radius:12px;
                padding:18px 24px;margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;color:#F0F4FF;">
            🩺 Doctor Dashboard</div>
        <div style="font-size:12px;color:#64748B;margin-top:3px;
                    font-family:'IBM Plex Mono',monospace;">
            Review patient reports · Approve · Edit · Reject
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Doctor selector
    doctors   = st.session_state.doctors
    doc_opts  = {f"Dr. {v['name'].split('Dr. ')[-1]} — {v['specialty']}": k
                 for k,v in doctors.items()}
    sel_lbl   = st.selectbox('Select Doctor', list(doc_opts.keys()),
                              key='doc_selector', label_visibility='collapsed')
    active_id = doc_opts[sel_lbl]
    active    = doctors[active_id]

    st.markdown(f"""
    <div style="background:#0A1628;border:1px solid #1E3A5F;border-radius:8px;
                padding:10px 18px;margin-bottom:16px;
                display:flex;align-items:center;gap:14px;">
        <div style="width:36px;height:36px;background:#1E3A5F;border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    font-size:18px;">🩺</div>
        <div>
            <div style="font-size:14px;font-weight:600;color:#F0F4FF;">
                {active['name']}</div>
            <div style="font-size:11px;color:#64748B;">
                {active['dept']} · {active['specialty']}</div>
        </div>
        <div style="margin-left:auto;">
            <span style="background:rgba(16,185,129,.15);
                         border:1px solid rgba(16,185,129,.3);
                         color:#10B981;font-size:11px;padding:3px 12px;
                         border-radius:20px;font-family:'IBM Plex Mono',monospace;">
                ● ONLINE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    my_patients = {pid:p for pid,p in st.session_state.patients.items()
                   if p.get('doctor_id')==active_id}

    if not my_patients:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;background:#0D1621;
                    border:1px solid #1E293B;border-radius:12px;">
            <div style="font-size:36px;margin-bottom:12px;">📭</div>
            <div style="font-size:15px;color:#F0F4FF;margin-bottom:6px;">
                No pending reports</div>
            <div style="font-size:13px;color:#64748B;">
                Patient reports will appear here once submitted.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Queue stats
    total   = len(my_patients)
    pending = sum(1 for p in my_patients.values() if p.get('status')=='PENDING')
    approved= sum(1 for p in my_patients.values() if p.get('status')=='APPROVED')
    urgent  = sum(1 for p in my_patients.values() if p.get('fusion_label')=='Severe')

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
        ('Total Cases', total, '#3B82F6'),
        ('Awaiting Review', pending, '#F59E0B'),
        ('Approved', approved, '#10B981'),
        ('Urgent', urgent, '#EF4444')
    ]):
        with col:
            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-left:3px solid {clr};border-radius:8px;
                        padding:12px 16px;text-align:center;margin-bottom:8px;">
                <div style="font-size:10px;color:#64748B;
                            text-transform:uppercase;letter-spacing:.05em;">
                    {lbl}</div>
                <div style="font-size:26px;font-weight:700;color:#F0F4FF;
                            margin-top:2px;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    left, right = st.columns([1, 2], gap='large')

    with left:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#64748B;letter-spacing:.08em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:10px;">Pending Cases</div>
        """, unsafe_allow_html=True)

        sorted_pats = sorted(my_patients.items(), key=lambda x:(
            0 if x[1].get('fusion_label')=='Severe' else
            1 if x[1].get('fusion_label')=='Moderate' else
            2 if x[1].get('status')=='PENDING' else 3
        ))

        for pid, p in sorted_pats:
            status = p.get('status','PENDING')
            fus    = p.get('fusion_label','Unknown')
            clr    = SEV_COLORS.get(fus,'#94A3B8')
            icon   = {'APPROVED':'✅','REJECTED':'❌','PENDING':'🕐'}.get(status,'🕐')
            is_sel = st.session_state.current_patient == pid

            if st.button(
                f"{icon}  {pid}\n{p.get('name', 'Patient')}",
                key=f'doc_pt_{pid}',
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                # Pre-generate report when patient selected
                report_key = f'report_{pid}'
                if report_key not in st.session_state.reports:
                    with st.spinner('Preparing report...'):
                        st.session_state.reports[report_key] = generate_ai_report(p)
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if not pid or pid not in my_patients:
            st.markdown("""
            <div style="text-align:center;padding:80px 20px;
                        background:#0D1621;border:1px solid #1E293B;
                        border-radius:12px;">
                <div style="font-size:36px;margin-bottom:12px;">👈</div>
                <div style="font-size:14px;color:#64748B;">
                    Select a patient case from the list
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

        p       = my_patients[pid]
        fus     = p.get('fusion_label','Unknown')
        fus_clr = SEV_COLORS.get(fus,'#94A3B8')
        ct_cls  = p.get('ct_predicted_class','')
        us_cls  = p.get('us_predicted_class','')

        # Patient header — clinical info only
        urgency_tag = {
            'Severe':   ('URGENT', '#EF4444'),
            'Moderate': ('SEMI-URGENT', '#F97316'),
            'Mild':     ('ROUTINE', '#F59E0B'),
            'Normal':   ('ROUTINE', '#10B981')
        }.get(fus, ('REVIEW', '#94A3B8'))

        st.markdown(f"""
        <div style="background:#0D1621;border:1px solid #1E293B;
                    border-radius:10px;padding:14px 20px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:6px;">
                <div>
                    <span style="font-size:15px;font-weight:600;color:#F0F4FF;">
                        {p.get('name','Patient')}</span>
                    <span style="font-size:12px;color:#64748B;margin-left:10px;">
                        Case Ref: {pid}</span>
                </div>
                <span style="background:rgba(0,0,0,.3);
                             border:1px solid {urgency_tag[1]};
                             color:{urgency_tag[1]};font-size:11px;
                             padding:3px 12px;border-radius:20px;
                             font-family:'IBM Plex Mono',monospace;
                             font-weight:600;">{urgency_tag[0]}</span>
            </div>
            {(f'<div style="font-size:12px;color:#94A3B8;margin-top:4px;">Presenting complaint: {p.get("symptoms","")}</div>') if p.get("symptoms") else ""}
            <div style="font-size:11px;color:#475569;margin-top:6px;">
                Referred: {p.get('registered_at','')[:16]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── CLINICAL FINDINGS ────────────────────────────────
        st.markdown("""
        <div style="font-size:12px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;
                    margin-bottom:10px;">Clinical Findings</div>
        """, unsafe_allow_html=True)

        # Lab findings — shown as clinical text, not scores
        if p.get('lab_score') is not None:
            ckd = p.get('ckd_severity','N/A')
            dia = p.get('diabetes_severity_final','N/A')
            thy = p.get('thyroid_severity_final','N/A')
            sev = p.get('lab_severity_label','N/A')
            lab_clr = SEV_COLORS.get(sev,'#94A3B8')
            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {lab_clr};border-radius:8px;
                        padding:14px 16px;margin-bottom:8px;">
                <div style="font-size:11px;color:#64748B;margin-bottom:6px;
                            text-transform:uppercase;letter-spacing:.06em;">
                    Laboratory Results</div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
                    <div>
                        <div style="font-size:10px;color:#475569;">Renal Function</div>
                        <div style="font-size:13px;color:#F0F4FF;font-weight:500;">
                            CKD {ckd}</div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:#475569;">Glycaemic Status</div>
                        <div style="font-size:13px;color:#F0F4FF;font-weight:500;">
                            {dia}</div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:#475569;">Thyroid Function</div>
                        <div style="font-size:13px;color:#F0F4FF;font-weight:500;">
                            {thy}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # CT findings with GradCAM
        if p.get('ct_score') is not None:
            ct_name, ct_detail = CT_CLINICAL.get(ct_cls, (ct_cls,''))
            ct_conf = p.get('ct_confidence', 0)
            ct_sev  = p.get('ct_severity_label','N/A')
            ct_clr  = SEV_COLORS.get(ct_sev,'#94A3B8')

            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {ct_clr};border-radius:8px;
                        padding:14px 16px;margin-bottom:8px;">
                <div style="font-size:11px;color:#64748B;margin-bottom:6px;
                            text-transform:uppercase;letter-spacing:.06em;">
                    CT Brain Imaging</div>
                <div style="font-size:14px;color:#F0F4FF;font-weight:600;
                            margin-bottom:4px;">{ct_name}</div>
                <div style="font-size:12px;color:#94A3B8;">{ct_detail}</div>
                <div style="font-size:11px;color:{ct_clr};margin-top:6px;">
                    AI Confidence: {float(ct_conf):.1%}</div>
            </div>
            """, unsafe_allow_html=True)

            # GradCAM images
            ct_gradcam = p.get('gradcam_path','')
            if ct_gradcam and os.path.exists(str(ct_gradcam)):
                from PIL import Image as PILImage
                img = PILImage.open(ct_gradcam)
                gc1, gc2 = st.columns(2)
                with gc1:
                    st.image(img, caption='Original CT Scan',
                             use_column_width=True)
                with gc2:
                    st.image(img, caption='AI Attention Map (Grad-CAM)',
                             use_column_width=True)
                st.caption('Highlighted regions indicate areas of diagnostic significance.')

        # Ultrasound findings with GradCAM
        if p.get('us_score') is not None:
            us_name, us_detail = US_CLINICAL.get(us_cls, (us_cls,''))
            us_conf = p.get('us_confidence',0)
            us_sev  = p.get('us_severity_label','N/A')
            us_clr  = SEV_COLORS.get(us_sev,'#94A3B8')

            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {us_clr};border-radius:8px;
                        padding:14px 16px;margin-bottom:8px;">
                <div style="font-size:11px;color:#64748B;margin-bottom:6px;
                            text-transform:uppercase;letter-spacing:.06em;">
                    Obstetric Ultrasound</div>
                <div style="font-size:14px;color:#F0F4FF;font-weight:600;
                            margin-bottom:4px;">{us_name}</div>
                <div style="font-size:12px;color:#94A3B8;">{us_detail}</div>
                <div style="font-size:11px;color:{us_clr};margin-top:6px;">
                    AI Confidence: {float(us_conf):.1%}</div>
            </div>
            """, unsafe_allow_html=True)

            us_gradcam = p.get('us_gradcam_path','')
            if us_gradcam and os.path.exists(str(us_gradcam)):
                from PIL import Image as PILImage
                img = PILImage.open(us_gradcam)
                ug1, ug2 = st.columns(2)
                with ug1:
                    st.image(img, caption='Ultrasound Image',
                             use_column_width=True)
                with ug2:
                    st.image(img, caption='AI Attention Map (Grad-CAM)',
                             use_column_width=True)

        # ── AI CLINICAL REPORT ───────────────────────────────
        st.markdown("""
        <div style="font-size:12px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;
                    margin:16px 0 10px;">AI Clinical Report</div>
        """, unsafe_allow_html=True)

        report_key = f'report_{pid}'
        if report_key not in st.session_state.reports:
            st.session_state.reports[report_key] = generate_ai_report(p)

        report = st.session_state.reports[report_key]

        st.markdown(f"""
        <div style="background:#080C14;border:1px solid #1E3A5F;
                    border-left:3px solid #8B5CF6;border-radius:8px;
                    padding:16px 18px;font-size:13px;line-height:1.9;
                    color:#C8D0E0;white-space:pre-wrap;margin-bottom:6px;">
{report}
        </div>
        """, unsafe_allow_html=True)

        if st.button('↺ Regenerate Report', key=f'regen_{pid}',
                     use_container_width=False):
            del st.session_state.reports[report_key]
            st.session_state.reports[report_key] = generate_ai_report(p)
            st.rerun()

        # ── DOCTOR REVIEW ────────────────────────────────────
        st.markdown("""
        <div style="font-size:12px;font-weight:600;color:#94A3B8;
                    text-transform:uppercase;letter-spacing:.08em;
                    margin:16px 0 10px;">Your Review</div>
        """, unsafe_allow_html=True)

        edited = st.text_area(
            'Edit report if required',
            value=report, height=140,
            key=f'edit_{pid}',
            label_visibility='collapsed'
        )
        notes = st.text_input(
            'Clinical notes',
            placeholder='Additional observations, amendments, or instructions...',
            key=f'notes_{pid}',
            label_visibility='collapsed'
        )

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
                st.success('✅ Report approved and released to patient.')
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
                st.info('✏️ Approved with your amendments.')
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
                st.error('Report rejected — manual review required.')

        # Status after decision
        cur_status = st.session_state.patients[pid].get('status','PENDING')
        if cur_status == 'APPROVED':
            reviewer = st.session_state.patients[pid].get('reviewed_by','')
            rev_time = st.session_state.patients[pid].get('reviewed_at','')[:16]
            st.markdown(f"""
            <div style="background:#0D2818;border:1px solid #10B981;
                        border-radius:8px;padding:12px 16px;margin-top:10px;">
                <div style="font-size:13px;color:#10B981;font-weight:600;">
                    ✅ Approved by {reviewer} · {rev_time}</div>
                <div style="font-size:12px;color:#64748B;margin-top:4px;">
                    Report released to patient. They have been notified.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button('View Patient Notification →', key=f'view_{pid}'):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
        elif cur_status == 'REJECTED':
            st.markdown("""
            <div style="background:#1A0808;border:1px solid #EF4444;
                        border-radius:8px;padding:12px 16px;margin-top:10px;">
                <div style="font-size:13px;color:#EF4444;font-weight:600;">
                    ❌ Report Rejected</div>
                <div style="font-size:12px;color:#64748B;margin-top:4px;">
                    Patient has been notified to contact the clinic.</div>
            </div>
            """, unsafe_allow_html=True)
