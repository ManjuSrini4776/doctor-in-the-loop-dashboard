import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

SCORE_TO_LABEL = {0: 'Normal', 1: 'Mild', 2: 'Moderate', 3: 'Severe'}
SEV_COLORS = {
    'Normal':  '#10B981', 'Mild':     '#F59E0B',
    'Moderate':'#F97316', 'Severe':   '#EF4444', 'Unknown':'#94A3B8'
}
CT_DESC = {
    'notumor':   'No tumor detected',   'pituitary': 'Pituitary adenoma',
    'meningioma':'Meningioma',           'glioma':    'Glioma (high-grade)'
}
US_DESC = {
    'Fetal abdomen':'Normal abdominal plane',
    'Fetal brain':  'Brain anomaly assessment',
    'Fetal femur':  'Normal femur growth',
    'Fetal thorax': 'Thoracic assessment'
}


def sev_badge(label):
    return f'<span class="sev sev-{label}">{label}</span>'


def get_openai_client():
    try:
        from openai import OpenAI
        key = st.secrets.get('OPENAI_API_KEY',
                             os.environ.get('OPENAI_API_KEY', ''))
        if key:
            return OpenAI(api_key=key)
    except Exception:
        pass
    return None


def get_rag_db():
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size': 32}
        )
        path = 'rag_output/baseline_vector_db'
        if os.path.exists(path):
            return FAISS.load_local(
                path, emb, allow_dangerous_deserialization=True
            )
    except Exception:
        pass
    return None


def generate_ai_report(patient: dict, rag_db=None, client=None) -> str:
    """Generate clinical report using RAG + GPT-4o-mini."""
    parts = []
    if patient.get('lab_score') is not None:
        parts.append(
            f"Lab findings: {patient.get('lab_severity_label','Unknown')} "
            f"chronic disease severity."
        )
    if patient.get('ct_score') is not None:
        cls = patient.get('ct_predicted_class','')
        parts.append(
            f"CT scan: {CT_DESC.get(cls, cls)} "
            f"({patient.get('ct_severity_label','Unknown')} severity, "
            f"confidence {patient.get('ct_confidence',0):.1%})."
        )
    if patient.get('us_score') is not None:
        cls = patient.get('us_predicted_class','')
        parts.append(
            f"Ultrasound: {US_DESC.get(cls, cls)} "
            f"({patient.get('us_severity_label','Unknown')} risk)."
        )
    parts.append(
        f"Overall multimodal fusion severity: "
        f"{patient.get('fusion_label','Unknown')}."
    )
    query = ' '.join(parts)

    context = ''
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            pass

    if not client:
        # Fallback without OpenAI
        fus = patient.get('fusion_label', 'Unknown')
        urgency = ('High' if fus == 'Severe' else
                   'Medium' if fus == 'Moderate' else 'Low')
        return (
            f"Clinical Interpretation: Patient presents with {fus} overall "
            f"severity based on multimodal assessment. "
            + (f"CT imaging indicates {CT_DESC.get(patient.get('ct_predicted_class',''),'findings')}. "
               if patient.get('ct_score') is not None else '')
            + (f"Ultrasound assessment shows {US_DESC.get(patient.get('us_predicted_class',''),'findings')}. "
               if patient.get('us_score') is not None else '')
            + f"\n\nRecommended Actions: "
            + ("Urgent specialist referral and further imaging required. "
               if fus == 'Severe' else
               "Schedule follow-up within 2 weeks for monitoring. "
               if fus == 'Moderate' else
               "Routine monitoring; next check-up in 3 months. ")
            + f"\n\nUrgency: {urgency}"
            + "\n\n⚠️ AI-generated draft — requires doctor review and validation."
        )

    prompt = f"""You are a clinical decision support assistant.

Patient: {patient.get('name','')} | Age: {patient.get('age','')} | 
Symptoms: {patient.get('symptoms','Not specified')}

Assessment:
{query}

{"Clinical Evidence:\n" + context if context else ""}

Write a concise clinical report. Format:
Clinical Interpretation: <2 sentences>
Recommended Actions: <specific steps>
Urgency: <Low / Medium / High>
Follow-up: <timeline>

End with:
⚠️ AI-generated draft — requires doctor review."""

    try:
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2, max_tokens=350
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Report generation error: {e}\n\n⚠️ Check API key."


def render():
    # ── Back button ──────────────────────────────────────────
    if st.button('← Back to Home', key='doc_back'):
        st.session_state.page = 'home'
        st.rerun()

        # Doctor selector
    doctors = st.session_state.doctors

    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;
                border-radius:12px;padding:20px 28px;margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;
                    color:#F0F4FF;">🩺 Doctor Dashboard</div>
        <div style="font-size:12px;color:#64748B;margin-top:4px;
                    font-family:'IBM Plex Mono',monospace;">
            Review AI-generated reports · Approve · Edit · Reject
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Doctor login selector
    doc_options = {f"{v['name']} ({v['dept']})": k
                   for k, v in doctors.items()}
    selected_label = st.selectbox(
        '👨‍⚕️ Select Doctor (Login)',
        list(doc_options.keys()),
        key='doc_selector'
    )
    active_doc_id = doc_options[selected_label]
    active_doc    = doctors[active_doc_id]

    st.markdown(f"""
    <div style="background:#0A1628;border:1px solid #1E3A5F;
                border-radius:8px;padding:10px 16px;margin-bottom:16px;
                display:flex;align-items:center;gap:12px;">
        <div style="font-size:20px;">🩺</div>
        <div>
            <div style="font-size:13px;font-weight:600;color:#F0F4FF;">
                {active_doc['name']}
            </div>
            <div style="font-size:11px;color:#64748B;">
                {active_doc['dept']} · {active_doc['specialty']}
            </div>
        </div>
        <div style="margin-left:auto;font-size:11px;color:#3B82F6;
                    font-family:'IBM Plex Mono',monospace;">LOGGED IN</div>
    </div>
    """, unsafe_allow_html=True)

    # Filter patients for this doctor
    my_patients = {
        pid: p for pid, p in st.session_state.patients.items()
        if p.get('doctor_id') == active_doc_id
    }

    if not my_patients:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;
                    background:#0D1621;border:1px solid #1E293B;
                    border-radius:12px;">
            <div style="font-size:36px;margin-bottom:12px;">📭</div>
            <div style="font-size:14px;color:#64748B;">
                No reports assigned to you yet.<br>
                Patients will appear here once they register.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Stats
    total   = len(my_patients)
    pending = len([p for p in my_patients.values()
                   if p.get('status') == 'PENDING'])
    approved= len([p for p in my_patients.values()
                   if p.get('status') == 'APPROVED'])
    severe  = len([p for p in my_patients.values()
                   if p.get('fusion_label') == 'Severe'])

    c1, c2, c3, c4 = st.columns(4)
    for col, (label, val, color) in zip(
        [c1,c2,c3,c4],
        [('Total Assigned', total,    '#3B82F6'),
         ('Pending Review', pending,  '#F59E0B'),
         ('Approved',       approved, '#10B981'),
         ('Severe Cases',   severe,   '#EF4444')]
    ):
        with col:
            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-left:3px solid {color};border-radius:8px;
                        padding:14px 18px;">
                <div style="font-size:11px;color:#64748B;
                            font-family:'IBM Plex Mono',monospace;
                            margin-bottom:4px;">{label}</div>
                <div style="font-size:26px;font-weight:600;color:#F0F4FF;">
                    {val}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Two-col layout: list + detail
    left, right = st.columns([1, 2], gap='large')

    with left:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:12px;">── Patient Queue</div>
        """, unsafe_allow_html=True)

        # Sort: Severe first, then Pending
        sorted_patients = sorted(
            my_patients.items(),
            key=lambda x: (
                0 if x[1].get('fusion_label') == 'Severe' else
                1 if x[1].get('status') == 'PENDING' else 2,
                x[1].get('registered_at', '')
            )
        )

        for pid, p in sorted_patients:
            status = p.get('status', 'PENDING')
            fus    = p.get('fusion_label', 'Unknown')
            color  = SEV_COLORS.get(fus, '#94A3B8')
            icon   = {'APPROVED':'✅','REJECTED':'❌','PENDING':'⏳'
                      }.get(status, '⏳')
            urgent = ' 🔴' if fus == 'Severe' else ''

            is_selected = st.session_state.current_patient == pid
            btn_style   = 'primary' if is_selected else 'secondary'

            if st.button(
                f"{icon} {pid}{urgent}\n"
                f"{p.get('name','')} · {p.get('test_type','')}",
                key=f'doc_pt_{pid}',
                use_container_width=True,
                type=btn_style
            ):
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if pid and pid in my_patients:
            p = my_patients[pid]

            fus_lbl = p.get('fusion_label', 'Unknown')
            fus_clr = SEV_COLORS.get(fus_lbl, '#94A3B8')

            # Patient header
            st.markdown(f"""
            <div style="display:flex;align-items:center;
                        justify-content:space-between;margin-bottom:16px;">
                <div>
                    <span style="font-family:'IBM Plex Mono',monospace;
                                 font-size:17px;color:#F0F4FF;">
                        {pid}
                    </span>
                    <span style="margin-left:10px;">
                        {sev_badge(fus_lbl)}
                    </span>
                    <span style="margin-left:8px;font-size:12px;color:#64748B;">
                        {p.get('name','')} · {p.get('age','')}y ·
                        {p.get('gender','')}
                    </span>
                </div>
                <div style="font-size:11px;color:#475569;
                            font-family:'IBM Plex Mono',monospace;">
                    {p.get('registered_at','')[:16]}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if p.get('symptoms'):
                st.markdown(f"""
                <div style="background:#0A1628;border-left:3px solid #3B82F6;
                            border-radius:0 6px 6px 0;padding:8px 14px;
                            margin-bottom:14px;font-size:12px;color:#94A3B8;">
                    <b style="color:#64748B;">Symptoms:</b>
                    {p.get('symptoms','')}
                </div>
                """, unsafe_allow_html=True)

            # Severity scores
            tab1, tab2, tab3 = st.tabs(
                ['📊 AI Findings', '🧠 Explainability', '📋 Report & Review']
            )

            with tab1:
                sc1, sc2, sc3, sc4 = st.columns(4)
                score_items = [
                    ('Lab Score',   p.get('lab_score'),
                     p.get('lab_severity_label','N/A')),
                    ('CT Score',    p.get('ct_score'),
                     p.get('ct_severity_label','N/A')),
                    ('US Score',    p.get('us_score'),
                     p.get('us_severity_label','N/A')),
                    ('Fusion',      p.get('fusion_score'), fus_lbl),
                ]
                for col, (lbl, score, sev_lbl) in zip(
                    [sc1,sc2,sc3,sc4], score_items
                ):
                    with col:
                        color = SEV_COLORS.get(sev_lbl, '#94A3B8') \
                                if score is not None else '#475569'
                        val   = str(int(score)) if score is not None else '—'
                        st.markdown(f"""
                        <div style="background:#0D1621;
                                    border:1px solid #1E293B;
                                    border-left:3px solid {color};
                                    border-radius:8px;padding:12px 14px;">
                            <div style="font-size:10px;color:#64748B;
                                        font-family:'IBM Plex Mono',monospace;">
                                {lbl}
                            </div>
                            <div style="font-size:24px;font-weight:600;
                                        color:#F0F4FF;">{val}</div>
                            <div style="font-size:11px;color:{color};">
                                {sev_lbl}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown('<br>', unsafe_allow_html=True)

                # CT details
                if p.get('ct_score') is not None:
                    st.markdown("""
                    <div style="font-family:'IBM Plex Mono',monospace;
                                font-size:11px;color:#3B82F6;
                                letter-spacing:.1em;text-transform:uppercase;
                                padding-bottom:6px;border-bottom:1px solid #1E293B;
                                margin-bottom:12px;">── CT Analysis</div>
                    """, unsafe_allow_html=True)
                    cls  = p.get('ct_predicted_class', '')
                    conf = p.get('ct_confidence', 0)
                    st.markdown(f"""
                    <div style="background:#0D1621;border:1px solid #1E293B;
                                border-radius:8px;padding:14px 18px;">
                        <div style="font-size:13px;color:#F0F4FF;
                                    font-weight:500;">
                            {CT_DESC.get(cls, cls)}
                        </div>
                        <div style="font-size:12px;color:#64748B;margin-top:4px;">
                            Class: {cls} · Confidence: {conf:.1%}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # US details
                if p.get('us_score') is not None:
                    st.markdown("""
                    <div style="font-family:'IBM Plex Mono',monospace;
                                font-size:11px;color:#3B82F6;
                                letter-spacing:.1em;text-transform:uppercase;
                                padding-bottom:6px;border-bottom:1px solid #1E293B;
                                margin:12px 0;">── Ultrasound Analysis</div>
                    """, unsafe_allow_html=True)
                    cls  = p.get('us_predicted_class', '')
                    conf = p.get('us_confidence', 0)
                    st.markdown(f"""
                    <div style="background:#0D1621;border:1px solid #1E293B;
                                border-radius:8px;padding:14px 18px;">
                        <div style="font-size:13px;color:#F0F4FF;
                                    font-weight:500;">
                            {US_DESC.get(cls, cls)}
                        </div>
                        <div style="font-size:12px;color:#64748B;margin-top:4px;">
                            Plane: {cls} · Confidence: {conf:.1%}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with tab2:
                st.markdown("""
                <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                            color:#3B82F6;letter-spacing:.1em;
                            text-transform:uppercase;padding-bottom:6px;
                            border-bottom:1px solid #1E293B;margin-bottom:14px;">
                    ── Grad-CAM Explainability
                </div>
                """, unsafe_allow_html=True)

                ec1, ec2 = st.columns(2)

                with ec1:
                    st.markdown("**🧠 CT Scan Heatmap**")
                    ct_gradcam = p.get('gradcam_path', '')
                    if ct_gradcam and os.path.exists(str(ct_gradcam)):
                        from PIL import Image
                        st.image(Image.open(ct_gradcam),
                                 caption='CT Grad-CAM',
                                 use_column_width=True)
                    else:
                        st.markdown("""
                        <div style="background:#0D1621;
                                    border:1px dashed #1E293B;
                                    border-radius:8px;padding:30px;
                                    text-align:center;color:#475569;
                                    font-size:12px;">
                            🧠 GradCAM not available<br>
                            Run CT_NB03 to generate
                        </div>
                        """, unsafe_allow_html=True)

                with ec2:
                    st.markdown("**🔬 Ultrasound Heatmap**")
                    us_gradcam = p.get('us_gradcam_path', '')
                    if us_gradcam and os.path.exists(str(us_gradcam)):
                        from PIL import Image
                        st.image(Image.open(us_gradcam),
                                 caption='US Grad-CAM',
                                 use_column_width=True)
                    else:
                        st.markdown("""
                        <div style="background:#0D1621;
                                    border:1px dashed #1E293B;
                                    border-radius:8px;padding:30px;
                                    text-align:center;color:#475569;
                                    font-size:12px;">
                            🔬 GradCAM not available<br>
                            Run US_NB03 to generate
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("""
                <div style="font-size:11px;color:#475569;margin-top:8px;
                            font-family:'IBM Plex Mono',monospace;">
                    Heatmaps show regions the AI model focused on
                    for classification. Bright areas = high attention.
                </div>
                """, unsafe_allow_html=True)

            with tab3:
                st.markdown("""
                <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                            color:#3B82F6;letter-spacing:.1em;
                            text-transform:uppercase;padding-bottom:6px;
                            border-bottom:1px solid #1E293B;margin-bottom:14px;">
                    ── AI Clinical Report
                </div>
                """, unsafe_allow_html=True)

                # Generate report
                report_key = f'report_{pid}'
                if report_key not in st.session_state.reports:
                    if st.button('🤖 Generate AI Report',
                                 use_container_width=True,
                                 key=f'gen_{pid}'):
                        with st.spinner('Retrieving guidelines + generating...'):
                            rag_db = get_rag_db()
                            oai    = get_openai_client()
                            report = generate_ai_report(p, rag_db, oai)
                            st.session_state.reports[report_key] = report
                        st.rerun()
                else:
                    report = st.session_state.reports[report_key]

                    st.markdown(f"""
                    <div style="background:#0A0D14;border:1px solid #1E293B;
                                border-radius:8px;padding:16px 20px;
                                font-size:13px;line-height:1.8;
                                color:#C8D0E0;white-space:pre-wrap;
                                margin-bottom:14px;">
{report}
                    </div>
                    """, unsafe_allow_html=True)

                    # Editable
                    edited = st.text_area(
                        'Edit report if needed',
                        value=report, height=180,
                        key=f'edit_{pid}',
                        label_visibility='collapsed'
                    )
                    notes = st.text_input(
                        'Doctor notes',
                        placeholder='Additional clinical notes...',
                        key=f'notes_{pid}',
                        label_visibility='collapsed'
                    )

                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button('✅ Approve Report',
                                     key=f'app_{pid}',
                                     use_container_width=True,
                                     type='primary'):
                            st.session_state.patients[pid]['status'] = 'APPROVED'
                            st.session_state.patients[pid]['final_report'] = edited
                            st.session_state.patients[pid]['doctor_notes'] = notes
                            st.session_state.patients[pid]['reviewed_at'] = \
                                datetime.now().isoformat()
                            st.session_state.patients[pid]['reviewed_by'] = \
                                active_doc['name']
                            st.success(
                                f'✅ Report approved! '
                                f'Patient {pid} notified.'
                            )
                            st.balloons()
                    with b2:
                        if st.button('✏️ Approve with Edits',
                                     key=f'edit_app_{pid}',
                                     use_container_width=True):
                            st.session_state.patients[pid]['status'] = 'APPROVED'
                            st.session_state.patients[pid]['final_report'] = edited
                            st.session_state.patients[pid]['doctor_notes'] = notes
                            st.session_state.patients[pid]['reviewed_at'] = \
                                datetime.now().isoformat()
                            st.session_state.patients[pid]['reviewed_by'] = \
                                active_doc['name']
                            st.info('✏️ Approved with edits.')
                    with b3:
                        if st.button('❌ Reject',
                                     key=f'rej_{pid}',
                                     use_container_width=True):
                            st.session_state.patients[pid]['status'] = 'REJECTED'
                            st.session_state.patients[pid]['doctor_notes'] = notes
                            st.error('Report rejected — needs manual review.')

                    # Regen
                    if st.button('🔄 Regenerate Report',
                                 key=f'regen_{pid}'):
                        del st.session_state.reports[report_key]
                        st.rerun()

        else:
            st.markdown("""
            <div style="text-align:center;padding:80px 20px;
                        background:#0D1621;border:1px solid #1E293B;
                        border-radius:12px;">
                <div style="font-size:36px;margin-bottom:12px;">👈</div>
                <div style="font-size:14px;color:#64748B;">
                    Select a patient from the queue to review
                </div>
            </div>
            """, unsafe_allow_html=True)
