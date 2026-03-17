import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

SCORE_TO_LABEL = {0:'Normal', 1:'Mild', 2:'Moderate', 3:'Severe'}
SEV_COLORS = {
    'Normal':'#10B981','Mild':'#F59E0B',
    'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
}
CT_DESC = {
    'notumor':'No tumor detected','pituitary':'Pituitary adenoma',
    'meningioma':'Meningioma','glioma':'Glioma (high-grade)'
}
US_DESC = {
    'Fetal abdomen':'Normal abdominal plane',
    'Fetal brain':'Brain anomaly — urgent',
    'Fetal femur':'Normal femur growth',
    'Fetal thorax':'Thoracic assessment'
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
            return FAISS.load_local(path,emb,
                                    allow_dangerous_deserialization=True)
    except Exception:
        pass
    return None


def generate_ai_report(patient:dict, rag_db=None, client=None) -> str:
    parts = []
    if patient.get('lab_score') is not None:
        parts.append(
            f"Lab findings indicate "
            f"{patient.get('lab_severity_label','Unknown')} chronic disease. "
            f"CKD: {patient.get('ckd_severity','N/A')}, "
            f"Diabetes: {patient.get('diabetes_severity_final','N/A')}, "
            f"Thyroid: {patient.get('thyroid_severity_final','N/A')}."
        )
    if patient.get('ct_score') is not None:
        cls = patient.get('ct_predicted_class','')
        parts.append(
            f"CT scan: {CT_DESC.get(cls,cls)} "
            f"({patient.get('ct_severity_label','Unknown')} severity, "
            f"confidence {patient.get('ct_confidence',0):.1%})."
        )
    if patient.get('us_score') is not None:
        cls = patient.get('us_predicted_class','')
        parts.append(
            f"Ultrasound: {US_DESC.get(cls,cls)} "
            f"({patient.get('us_severity_label','Unknown')} risk, "
            f"confidence {patient.get('us_confidence',0):.1%})."
        )
    fus   = patient.get('fusion_label','Unknown')
    parts.append(f"Overall multimodal fusion severity: {fus}.")
    if patient.get('symptoms'):
        parts.append(f"Patient symptoms: {patient.get('symptoms')}.")
    query = ' '.join(parts)

    context = ''
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            pass

    # Fallback report (no OpenAI)
    if not client:
        urgency = ('High' if fus=='Severe' else
                   'Medium' if fus=='Moderate' else 'Low')
        action  = ('Urgent specialist referral required immediately.'
                   if fus=='Severe' else
                   'Schedule follow-up within 7-10 days.'
                   if fus=='Moderate' else
                   'Routine monitoring; next check-up in 3 months.')
        return (
            f"Clinical Interpretation: Patient presents with {fus} overall "
            f"severity based on multimodal assessment across lab, CT, and "
            f"ultrasound findings. "
            + (f"CT indicates {CT_DESC.get(patient.get('ct_predicted_class',''),'findings')}. "
               if patient.get('ct_score') is not None else '')
            + (f"Ultrasound shows {US_DESC.get(patient.get('us_predicted_class',''),'findings')}. "
               if patient.get('us_score') is not None else '')
            + f"\n\nRecommended Actions: {action}"
            + f"\n\nUrgency: {urgency}"
            + "\n\n⚠️ AI-generated draft — requires doctor review and validation."
        )

    prompt = f"""You are a clinical decision support assistant in a 
Doctor-in-the-Loop AI system.

Patient: {patient.get('name','')} | Symptoms: {patient.get('symptoms','Not specified')}

Multimodal Assessment:
{query}

{"Relevant Clinical Guidelines:\n" + context if context else ""}

Write a concise clinical report:

Clinical Interpretation: <2 sentences — what do the findings mean clinically>
Recommended Actions: <specific actionable next steps for the doctor>
Urgency: <Low / Medium / High>
Follow-up: <suggested timeline>

End with:
⚠️ AI-generated draft — requires doctor review and validation."""

    try:
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role':'user','content':prompt}],
            temperature=0.2,max_tokens=400
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Report generation error: {e}\n\n⚠️ Check API key in Streamlit secrets."


def render():
    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;border-radius:12px;
                padding:18px 24px;margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;color:#F0F4FF;">
            🩺 Doctor Dashboard</div>
        <div style="font-size:12px;color:#64748B;margin-top:3px;
                    font-family:'IBM Plex Mono',monospace;">
            Review AI-generated reports · RAG clinical summary · Approve · Edit · Reject
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Doctor login
    doctors = st.session_state.doctors
    doc_opts= {f"{v['name']} ({v['dept']})":k for k,v in doctors.items()}
    sel_lbl = st.selectbox('👨‍⚕️ Select Doctor',list(doc_opts.keys()),
                           key='doc_selector')
    active_doc_id = doc_opts[sel_lbl]
    active_doc    = doctors[active_doc_id]

    st.markdown(f"""
    <div style="background:#0A1628;border:1px solid #1E3A5F;border-radius:8px;
                padding:10px 16px;margin-bottom:16px;display:flex;
                align-items:center;gap:12px;">
        <div style="font-size:20px;">🩺</div>
        <div>
            <div style="font-size:13px;font-weight:600;color:#F0F4FF;">
                {active_doc['name']}</div>
            <div style="font-size:11px;color:#64748B;">
                {active_doc['dept']} · {active_doc['specialty']}</div>
        </div>
        <div style="margin-left:auto;font-size:11px;color:#3B82F6;
                    font-family:'IBM Plex Mono',monospace;">LOGGED IN</div>
    </div>
    """, unsafe_allow_html=True)

    # Filter patients for this doctor
    my_patients = {pid:p for pid,p in st.session_state.patients.items()
                   if p.get('doctor_id')==active_doc_id}

    if not my_patients:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;background:#0D1621;
                    border:1px solid #1E293B;border-radius:12px;">
            <div style="font-size:36px;margin-bottom:12px;">📭</div>
            <div style="font-size:14px;color:#64748B;">
                No reports assigned to you yet.<br>
                Go to Patient Portal and send a patient to this doctor.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button('→ Go to Patient Portal',
                     use_container_width=True,key='to_portal'):
            st.session_state.page = 'patient'
            st.rerun()
        return

    # Stats bar
    total   = len(my_patients)
    pending = len([p for p in my_patients.values() if p.get('status')=='PENDING'])
    approved= len([p for p in my_patients.values() if p.get('status')=='APPROVED'])
    severe  = len([p for p in my_patients.values() if p.get('fusion_label')=='Severe'])

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
        ('Total',total,'#3B82F6'),('Pending',pending,'#F59E0B'),
        ('Approved',approved,'#10B981'),('Severe 🔴',severe,'#EF4444')
    ]):
        with col:
            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-left:3px solid {clr};border-radius:8px;
                        padding:12px 16px;text-align:center;">
                <div style="font-size:10px;color:#64748B;">{lbl}</div>
                <div style="font-size:24px;font-weight:700;color:#F0F4FF;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Two-column layout
    left,right = st.columns([1,2],gap='large')

    with left:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:12px;">── Patient Queue</div>
        """, unsafe_allow_html=True)

        sorted_pats = sorted(
            my_patients.items(),
            key=lambda x:(
                0 if x[1].get('fusion_label')=='Severe' else
                1 if x[1].get('status')=='PENDING' else 2
            )
        )

        for pid,p in sorted_pats:
            status = p.get('status','PENDING')
            fus    = p.get('fusion_label','Unknown')
            color  = SEV_COLORS.get(fus,'#94A3B8')
            icon   = {'APPROVED':'✅','REJECTED':'❌','PENDING':'⏳'}.get(status,'⏳')
            urgent = ' 🔴' if fus=='Severe' else ''
            is_sel = st.session_state.current_patient==pid

            if st.button(
                f"{icon} {pid}{urgent}\n{p.get('name','')} · {fus}",
                key=f'doc_pt_{pid}',
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if not pid or pid not in my_patients:
            st.markdown("""
            <div style="text-align:center;padding:80px 20px;background:#0D1621;
                        border:1px solid #1E293B;border-radius:12px;">
                <div style="font-size:36px;margin-bottom:12px;">👈</div>
                <div style="font-size:14px;color:#64748B;">
                    Select a patient from the queue to review
                </div>
            </div>
            """, unsafe_allow_html=True)
            return

        p       = my_patients[pid]
        fus_lbl = p.get('fusion_label','Unknown')
        fus_clr = SEV_COLORS.get(fus_lbl,'#94A3B8')

        # Patient header
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    background:#0D1621;border:1px solid #1E293B;border-radius:10px;
                    padding:12px 18px;margin-bottom:16px;">
            <div>
                <span style="font-family:'IBM Plex Mono',monospace;
                             font-size:16px;color:#F0F4FF;">{pid}</span>
                <span style="font-size:12px;color:#64748B;margin-left:10px;">
                    {p.get('name','')}
                    {(' · ' + p.get('symptoms','')[:40] + '...') if p.get('symptoms') else ''}
                </span>
            </div>
            <span style="background:rgba(0,0,0,.3);border:1px solid {fus_clr};
                         color:{fus_clr};font-size:13px;padding:3px 14px;
                         border-radius:20px;font-weight:600;">{fus_lbl}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── SECTION 1: AI Severity Scores ────────────────────
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:6px;border-bottom:1px solid #1E293B;
                    margin-bottom:12px;">── AI Severity Findings</div>
        """, unsafe_allow_html=True)

        sc1,sc2,sc3,sc4 = st.columns(4)
        for col,(lbl,skey,sevkey) in zip([sc1,sc2,sc3,sc4],[
            ('Lab','lab_score','lab_severity_label'),
            ('CT Scan','ct_score','ct_severity_label'),
            ('Ultrasound','us_score','us_severity_label'),
            ('Fusion','fusion_score','fusion_label')
        ]):
            with col:
                sc  = p.get(skey)
                sev = p.get(sevkey,'N/A')
                clr = SEV_COLORS.get(sev,'#94A3B8')
                val = str(int(sc)) if sc is not None and pd.notna(sc) else '—'
                st.markdown(f"""
                <div style="background:#080C14;border:1px solid #1E293B;
                            border-left:3px solid {clr};border-radius:8px;
                            padding:10px;text-align:center;margin-bottom:8px;">
                    <div style="font-size:9px;color:#64748B;">{lbl}</div>
                    <div style="font-size:22px;font-weight:700;color:#F0F4FF;">{val}</div>
                    <div style="font-size:10px;color:{clr};">{sev}</div>
                </div>
                """, unsafe_allow_html=True)

        # CT + US detail
        ct_c,us_c = st.columns(2)
        with ct_c:
            ct   = p.get('ct_predicted_class','')
            conf = p.get('ct_confidence',0)
            ct_clr = SEV_COLORS.get(p.get('ct_severity_label','Unknown'),'#94A3B8')
            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {ct_clr};border-radius:8px;
                        padding:12px 14px;margin-bottom:8px;">
                <div style="font-size:9px;color:#64748B;margin-bottom:4px;">
                    🧠 CT SCAN</div>
                <div style="font-size:13px;color:#F0F4FF;font-weight:600;">
                    {CT_DESC.get(ct,ct)}</div>
                <div style="font-size:11px;color:{ct_clr};margin-top:3px;">
                    Confidence: {float(conf):.1%}</div>
            </div>
            """, unsafe_allow_html=True)
        with us_c:
            us   = p.get('us_predicted_class','')
            conf = p.get('us_confidence',0)
            us_clr = SEV_COLORS.get(p.get('us_severity_label','Unknown'),'#94A3B8')
            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {us_clr};border-radius:8px;
                        padding:12px 14px;margin-bottom:8px;">
                <div style="font-size:9px;color:#64748B;margin-bottom:4px;">
                    🔬 ULTRASOUND</div>
                <div style="font-size:13px;color:#F0F4FF;font-weight:600;">
                    {US_DESC.get(us,us)}</div>
                <div style="font-size:11px;color:{us_clr};margin-top:3px;">
                    Confidence: {float(conf):.1%}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── SECTION 2: RAG AI Report (always visible) ────────
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#8B5CF6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:6px;border-bottom:1px solid #1E293B;
                    margin:14px 0 12px;">
            ── RAG Clinical Report (AI Generated)
        </div>
        """, unsafe_allow_html=True)

        report_key = f'report_{pid}'

        # Auto-generate report when patient selected
        if report_key not in st.session_state.reports:
            with st.spinner('🤖 RAG retrieving guidelines + generating report...'):
                rag_db = get_rag_db()
                oai    = get_openai_client()
                report = generate_ai_report(p, rag_db, oai)
                st.session_state.reports[report_key] = report
            st.rerun()

        report = st.session_state.reports[report_key]

        # Show report
        st.markdown(f"""
        <div style="background:#0A0D14;border:1px solid #2D1B69;
                    border-left:3px solid #8B5CF6;border-radius:8px;
                    padding:16px 18px;font-size:13px;line-height:1.8;
                    color:#C8D0E0;white-space:pre-wrap;margin-bottom:12px;">
{report}
        </div>
        """, unsafe_allow_html=True)

        col_regen, _ = st.columns([1,3])
        with col_regen:
            if st.button('🔄 Regenerate Report', key=f'regen_{pid}'):
                del st.session_state.reports[report_key]
                st.rerun()

        # ── SECTION 3: Doctor Review (always visible) ────────
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#10B981;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:6px;border-bottom:1px solid #1E293B;
                    margin:14px 0 12px;">
            ── Doctor Review & Decision
        </div>
        """, unsafe_allow_html=True)

        # Editable report
        edited = st.text_area(
            '✏️ Edit report if needed (optional)',
            value=report,
            height=150,
            key=f'edit_{pid}'
        )

        # Doctor notes
        notes = st.text_input(
            '📝 Doctor notes',
            placeholder='Add clinical notes, amendments, or observations...',
            key=f'notes_{pid}'
        )

        # Action buttons — large and clear
        st.markdown('<br>', unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)

        with b1:
            if st.button('✅ APPROVE',
                         key=f'app_{pid}',
                         use_container_width=True,
                         type='primary'):
                st.session_state.patients[pid]['status']       = 'APPROVED'
                st.session_state.patients[pid]['final_report'] = edited
                st.session_state.patients[pid]['doctor_notes'] = notes
                st.session_state.patients[pid]['reviewed_at']  = datetime.now().isoformat()
                st.session_state.patients[pid]['reviewed_by']  = active_doc['name']
                st.success('✅ Report approved! Patient will be notified.')
                st.balloons()

        with b2:
            if st.button('✏️ APPROVE + EDIT',
                         key=f'edit_app_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid]['status']       = 'APPROVED'
                st.session_state.patients[pid]['final_report'] = edited
                st.session_state.patients[pid]['doctor_notes'] = notes
                st.session_state.patients[pid]['reviewed_at']  = datetime.now().isoformat()
                st.session_state.patients[pid]['reviewed_by']  = active_doc['name']
                st.info('✏️ Approved with your edits.')

        with b3:
            if st.button('❌ REJECT',
                         key=f'rej_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid]['status']       = 'REJECTED'
                st.session_state.patients[pid]['doctor_notes'] = notes
                st.session_state.patients[pid]['reviewed_at']  = datetime.now().isoformat()
                st.session_state.patients[pid]['reviewed_by']  = active_doc['name']
                st.error('❌ Report rejected — manual review required.')

        # Show current approval status
        current_status = st.session_state.patients[pid].get('status','PENDING')
        if current_status == 'APPROVED':
            st.markdown(f"""
            <div style="background:#0D2818;border:1px solid #10B981;
                        border-radius:8px;padding:12px 16px;margin-top:10px;">
                <div style="font-size:13px;color:#10B981;font-weight:600;">
                    ✅ APPROVED by {st.session_state.patients[pid].get('reviewed_by','')}
                </div>
                <div style="font-size:11px;color:#64748B;margin-top:4px;">
                    {st.session_state.patients[pid].get('reviewed_at','')[:16]}
                    · Patient notified via My Report page
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button('→ View Patient Result Page',
                         key=f'view_result_{pid}',
                         use_container_width=True):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()

        elif current_status == 'REJECTED':
            st.error('❌ REJECTED — Patient notified to contact doctor.')
