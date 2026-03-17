import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from utils import (SEV_COLORS, SEV_BG, CT_NAMES, US_NAMES,
                   SCORE_TO_LABEL, DOCTORS, sev_badge, section_title, card)

CT_DETAIL = {
    'notumor':   'Normal brain scan. No suspicious mass or lesion identified.',
    'pituitary': 'Benign pituitary gland tumour. Endocrinology review recommended.',
    'meningioma':'Slow-growing tumour of the meninges. Neurosurgery referral advised.',
    'glioma':    'Malignant brain tumour. Urgent oncology referral required.'
}
US_DETAIL = {
    'Fetal abdomen':'Abdominal measurements within expected range for gestational age.',
    'Fetal brain':  'Neurosonography plane. Detailed anomaly scan recommended.',
    'Fetal femur':  'Femur length within normal range. Fetal growth on track.',
    'Fetal thorax': 'Thoracic plane. Cardiac and pulmonary assessment indicated.'
}
URGENCY = {
    'Severe':   ('URGENT',       '#EF4444', 'rgba(239,68,68,0.1)'),
    'Moderate': ('SEMI-URGENT',  '#F97316', 'rgba(249,115,22,0.1)'),
    'Mild':     ('ROUTINE',      '#F59E0B', 'rgba(245,158,11,0.1)'),
    'Normal':   ('ROUTINE',      '#10B981', 'rgba(16,185,129,0.1)'),
    'Unknown':  ('REVIEW',       '#94A3B8', 'rgba(148,163,184,0.1)'),
}
PRESCRIPTIONS = {
    'Normal': [
        'Continue current medication as prescribed.',
        'Maintain healthy diet and regular exercise.',
        'Schedule routine follow-up in 3 months.',
        'No immediate intervention required.',
    ],
    'Mild': [
        'Monitor symptoms closely over next 2–4 weeks.',
        'Review current medication dosage.',
        'Lifestyle modifications recommended.',
        'Return if symptoms worsen.',
    ],
    'Moderate': [
        'Specialist referral recommended within 7 days.',
        'Medication adjustment may be required.',
        'Avoid strenuous physical activity until reviewed.',
        'Blood work to be repeated in 2 weeks.',
    ],
    'Severe': [
        'Immediate specialist consultation required.',
        'Consider hospital admission for monitoring.',
        'Do not delay treatment — early intervention critical.',
        'Emergency contact available 24/7.',
    ],
}


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
        emb  = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size': 32}
        )
        for path in ['rag_output/baseline_vector_db',
                     'data/baseline_vector_db']:
            if os.path.exists(path):
                return FAISS.load_local(
                    path, emb, allow_dangerous_deserialization=True)
    except Exception:
        pass
    return None


def generate_report(p: dict) -> str:
    """Generate clinical report using RAG + GPT-4o-mini or clean fallback."""
    fus   = p.get('fusion_label', p.get('severity_label', 'Unknown'))
    mtype = p.get('modality_type', '')

    # Build clinical summary
    parts = []
    if mtype == 'Lab Report' or 'final_severity_label' in p:
        ckd = p.get('ckd_severity','')
        dia = p.get('diabetes_severity_final','')
        thy = p.get('thyroid_severity_final','')
        if ckd and str(ckd) not in ['None','nan']: parts.append(f"Kidney: {ckd}.")
        if dia and str(dia) not in ['None','nan']: parts.append(f"Diabetes: {dia}.")
        if thy and str(thy) not in ['None','nan']: parts.append(f"Thyroid: {thy}.")

    if mtype == 'CT Scan' or 'ct_predicted_class' in p:
        cls  = p.get('ct_predicted_class','')
        conf = p.get('ct_confidence', 0)
        parts.append(
            f"CT scan: {CT_NAMES.get(cls,cls)} "
            f"(confidence {float(conf):.1%})."
        )

    if mtype == 'Ultrasound' or 'predicted_class' in p:
        cls  = p.get('predicted_class', p.get('us_predicted_class',''))
        conf = p.get('confidence', p.get('us_confidence', 0))
        parts.append(
            f"Ultrasound: {US_NAMES.get(cls,cls)} "
            f"(confidence {float(conf):.1%})."
        )

    if p.get('symptoms'):
        parts.append(f"Patient complaints: {p['symptoms']}.")
    parts.append(f"Overall assessment: {fus} severity.")

    query = ' '.join(parts)

    # Try OpenAI
    client  = get_openai_client()
    rag_db  = get_rag_db()
    context = ''
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            pass

    if client:
        prompt = (
            "You are a clinical decision support assistant.\n"
            "Generate a professional clinical summary. "
            "Do NOT mention AI, scores, or system names.\n\n"
            f"Assessment:\n{query}\n\n"
            + (f"Guidelines:\n{context}\n\n" if context else "")
            + "Format:\n"
            "**Clinical Summary**\n[2-3 sentences]\n\n"
            "**Key Findings**\n• [finding 1]\n• [finding 2]\n\n"
            "**Recommended Actions**\n[specific steps]\n\n"
            f"**Urgency:** {URGENCY.get(fus,URGENCY['Unknown'])[0]}\n"
            "**Follow-up:** [timeline]\n\n"
            "*This report requires doctor approval before release.*"
        )
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
    urg = URGENCY.get(fus, URGENCY['Unknown'])[0]
    action = {
        'Severe':   'Immediate specialist referral. Consider urgent admission.',
        'Moderate': 'Specialist review within 7 days.',
        'Mild':     'Outpatient follow-up within 2–4 weeks.',
        'Normal':   'Routine follow-up in 3 months.'
    }.get(fus, 'Discuss findings with patient.')

    findings = '\n'.join(
        [f'• {part}' for part in parts if part]
    ) or '• See individual test results.'

    return (
        f"**Clinical Summary**\n"
        f"Patient presents with {fus.lower()} overall findings "
        f"based on {mtype.lower() if mtype else 'multimodal'} assessment.\n\n"
        f"**Key Findings**\n{findings}\n\n"
        f"**Recommended Actions**\n{action}\n\n"
        f"**Urgency:** {urg}\n"
        f"**Follow-up:** "
        f"{'Within 24–48 hours' if fus=='Severe' else 'Within 7–10 days' if fus=='Moderate' else 'Within 2–4 weeks' if fus=='Mild' else '3-month routine review'}\n\n"
        f"*This report requires doctor approval before release.*"
    )


def render():
    st.markdown(
        '<div style="font-size:26px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;margin-bottom:4px;">Doctor Dashboard</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:20px;">'
        'Review patient reports, approve findings, '
        'add prescriptions and release results</div>',
        unsafe_allow_html=True
    )

    # Doctor selector
    doc_opts = {
        f"{v['name']} — {v['dept']}": k
        for k, v in DOCTORS.items()
    }
    sel_label = st.selectbox(
        'Logged in as',
        list(doc_opts.keys()),
        key='doc_selector',
        label_visibility='collapsed'
    )
    active_id = doc_opts[sel_label]
    active    = DOCTORS[active_id]

    # Doctor info bar
    st.markdown(
        f'<div style="background:#111827;border:1px solid #1E2D40;'
        f'border-radius:10px;padding:14px 20px;margin-bottom:20px;'
        f'display:flex;align-items:center;gap:16px;">'
        f'<div style="background:{active["color"]}22;width:44px;height:44px;'
        f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
        f'font-size:20px;border:2px solid {active["color"]}44;">🩺</div>'
        f'<div style="flex:1;">'
        f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;">'
        f'{active["name"]}</div>'
        f'<div style="font-size:13px;color:#64748B;margin-top:2px;">'
        f'{active["dept"]} · {active["specialty"]}</div>'
        f'<div style="font-size:12px;color:{active["color"]};margin-top:3px;">'
        f'Sees: {", ".join(active["sees"])}</div>'
        f'</div>'
        f'<div style="background:rgba(16,185,129,0.12);border:1px solid '
        f'rgba(16,185,129,0.25);color:#10B981;font-size:12px;font-weight:500;'
        f'padding:5px 14px;border-radius:20px;font-family:monospace;">● Active</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Filter patients for this doctor by dept routing
    my_patients = {
        pid: p for pid, p in st.session_state.patients.items()
        if p.get('doctor_id') == active_id
    }

    if not my_patients:
        st.markdown(
            '<div style="background:#111827;border:2px dashed #1E2D40;'
            'border-radius:12px;padding:64px;text-align:center;">'
            '<div style="font-size:40px;margin-bottom:16px;">📭</div>'
            '<div style="font-size:18px;font-weight:600;color:#F1F5F9;'
            'margin-bottom:8px;">No reports assigned yet</div>'
            '<div style="font-size:14px;color:#64748B;">'
            'Patient cases will appear here once submitted '
            'from the Patient Portal.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # Stats
    total    = len(my_patients)
    pending  = sum(1 for p in my_patients.values()
                   if p.get('status') == 'PENDING')
    approved = sum(1 for p in my_patients.values()
                   if p.get('status') == 'APPROVED')
    urgent   = sum(1 for p in my_patients.values()
                   if p.get('fusion_label','') == 'Severe'
                   and p.get('status') == 'PENDING')

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
        ('Total Cases',     total,    '#3B82F6'),
        ('Awaiting Review', pending,  '#F59E0B'),
        ('Approved',        approved, '#10B981'),
        ('Urgent',          urgent,   '#EF4444'),
    ]):
        with col:
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-top:3px solid {clr};border-radius:10px;'
                f'padding:14px;text-align:center;margin-bottom:16px;">'
                f'<div style="font-size:28px;font-weight:700;color:{clr};">'
                f'{val}</div>'
                f'<div style="font-size:13px;color:#64748B;margin-top:4px;">'
                f'{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Two column layout
    left, right = st.columns([1, 2.2], gap='large')

    with left:
        st.markdown(section_title('Cases Queue'), unsafe_allow_html=True)

        sorted_pats = sorted(my_patients.items(), key=lambda x: (
            0 if x[1].get('fusion_label','') == 'Severe' else
            1 if x[1].get('fusion_label','') == 'Moderate' else
            2 if x[1].get('status') == 'PENDING' else 3
        ))

        for pid, p in sorted_pats:
            status  = p.get('status', 'PENDING')
            fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
            clr     = SEV_COLORS.get(fus, '#94A3B8')
            is_sel  = st.session_state.current_patient == pid
            s_icon  = {'APPROVED':'✓','REJECTED':'✗','PENDING':'○'}.get(status,'○')

            if st.button(
                f"{s_icon}  {pid}\n{p.get('name','')}  ·  {fus}",
                key=f'dpat_{pid}',
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                # Pre-generate report on selection
                rkey = f'report_{pid}'
                if rkey not in st.session_state.reports:
                    with st.spinner('Preparing clinical report...'):
                        st.session_state.reports[rkey] = generate_report(p)
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if not pid or pid not in my_patients:
            st.markdown(
                '<div style="background:#111827;border:2px dashed #1E2D40;'
                'border-radius:12px;padding:80px;text-align:center;">'
                '<div style="font-size:32px;margin-bottom:12px;">👈</div>'
                '<div style="font-size:15px;color:#64748B;">'
                'Select a case from the queue</div>'
                '</div>',
                unsafe_allow_html=True
            )
            return

        p       = my_patients[pid]
        fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
        fus_clr = SEV_COLORS.get(fus, '#94A3B8')
        mtype   = p.get('modality_type','')
        urg_tag, urg_clr, urg_bg = URGENCY.get(fus, URGENCY['Unknown'])

        # Patient header
        st.markdown(
            f'<div style="background:#111827;border:1px solid #1E2D40;'
            f'border-radius:12px;padding:18px 22px;margin-bottom:18px;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:flex-start;">'
            f'<div>'
            f'<div style="font-size:12px;color:#64748B;font-family:monospace;'
            f'margin-bottom:4px;">PATIENT</div>'
            f'<div style="font-size:18px;font-weight:700;color:#F1F5F9;">'
            f'{p.get("name","Patient")}</div>'
            f'<div style="font-size:13px;color:#64748B;margin-top:2px;">'
            f'Ref: <span style="font-family:monospace;">{pid}</span>  ·  '
            f'{p.get("age","")}{" yrs  ·  " + p.get("gender","") if p.get("age") else ""}'
            f'  ·  {mtype}</div>'
            f'{("<div style=font-size:13px;color:#94A3B8;margin-top:6px;>"+"Complaint: "+p.get("symptoms","")+"</div>") if p.get("symptoms") else ""}'
            f'<div style="font-size:12px;color:#475569;margin-top:6px;">'
            f'Submitted: {p.get("registered_at","")[:16]}</div>'
            f'</div>'
            f'<div style="background:{urg_bg};border:1px solid {urg_clr}44;'
            f'border-radius:10px;padding:10px 18px;text-align:center;">'
            f'<div style="font-size:11px;color:{urg_clr};font-weight:700;'
            f'letter-spacing:0.1em;margin-bottom:4px;">{urg_tag}</div>'
            f'<div style="font-size:18px;font-weight:700;color:{fus_clr};">'
            f'{fus}</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        # ── Clinical Findings ─────────────────────────────────
        st.markdown(section_title('Clinical Findings'), unsafe_allow_html=True)

        if mtype == 'Lab Report' or 'final_severity_label' in p:
            ckd = p.get('ckd_severity','')
            dia = p.get('diabetes_severity_final','')
            thy = p.get('thyroid_severity_final','')
            c1,c2,c3 = st.columns(3)
            for col,(lbl,val) in zip([c1,c2,c3],[
                ('Kidney Function', ckd),
                ('Blood Sugar', dia),
                ('Thyroid Function', thy)
            ]):
                v   = val if val and str(val) not in ['None','nan','NaN'] \
                      else 'Normal'
                sev = v if v in SEV_COLORS else 'Unknown'
                clr = SEV_COLORS.get(sev, '#94A3B8')
                with col:
                    st.markdown(
                        f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                        f'border-radius:10px;padding:14px;margin-bottom:10px;">'
                        f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                        f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                        f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;">'
                        f'{v}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        if mtype == 'CT Scan' or 'ct_predicted_class' in p:
            cls  = p.get('ct_predicted_class','')
            conf = p.get('ct_confidence', 0)
            sev  = p.get('ct_severity_label','Unknown')
            clr  = SEV_COLORS.get(sev,'#94A3B8')
            name = CT_NAMES.get(cls,cls)
            det  = CT_DETAIL.get(cls,'')
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-left:4px solid {clr};border-radius:10px;'
                f'padding:14px 18px;margin-bottom:10px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">CT Brain Scan</div>'
                f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
                f'margin-bottom:4px;">{name}</div>'
                f'<div style="font-size:13px;color:#94A3B8;margin-bottom:4px;">{det}</div>'
                f'<div style="font-size:12px;color:{clr};">'
                f'{sev}  ·  Confidence: {float(conf):.1%}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # GradCAM
            gpath = p.get('gradcam_path','')
            if gpath and os.path.exists(str(gpath)):
                from PIL import Image as PILImage
                gc1,gc2 = st.columns(2)
                with gc1:
                    st.image(PILImage.open(gpath),
                             caption='CT Scan', use_column_width=True)
                with gc2:
                    st.image(PILImage.open(gpath),
                             caption='AI Attention Map', use_column_width=True)

        if mtype == 'Ultrasound' or 'predicted_class' in p:
            cls  = p.get('predicted_class', p.get('us_predicted_class',''))
            conf = p.get('confidence', p.get('us_confidence', 0))
            sev  = p.get('us_severity_label','Unknown')
            clr  = SEV_COLORS.get(sev,'#94A3B8')
            name = US_NAMES.get(cls,cls)
            det  = US_DETAIL.get(cls,'')
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-left:4px solid {clr};border-radius:10px;'
                f'padding:14px 18px;margin-bottom:10px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">Obstetric Ultrasound</div>'
                f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
                f'margin-bottom:4px;">{name}</div>'
                f'<div style="font-size:13px;color:#94A3B8;margin-bottom:4px;">{det}</div>'
                f'<div style="font-size:12px;color:{clr};">'
                f'{sev}  ·  Confidence: {float(conf):.1%}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        if mtype == 'Combined Assessment':
            c1,c2,c3 = st.columns(3)
            for col,(lbl,key) in zip([c1,c2,c3],[
                ('Lab','lab_score'),('CT','ct_score'),('Ultrasound','us_score')
            ]):
                val = p.get(key)
                v   = SCORE_TO_LABEL.get(
                    int(float(val)),'—') \
                    if val is not None and str(val) not in ['None','nan'] else '—'
                clr = SEV_COLORS.get(v,'#64748B')
                with col:
                    st.markdown(
                        f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                        f'border-radius:10px;padding:14px;text-align:center;'
                        f'margin-bottom:10px;">'
                        f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                        f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                        f'<div style="font-size:20px;font-weight:700;color:{clr};">{v}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        # ── AI Clinical Report ────────────────────────────────
        st.markdown(section_title('AI Clinical Report'), unsafe_allow_html=True)

        rkey = f'report_{pid}'
        if rkey not in st.session_state.reports:
            with st.spinner('Generating report...'):
                st.session_state.reports[rkey] = generate_report(p)

        report = st.session_state.reports[rkey]
        st.markdown(
            f'<div style="background:#0B1120;border:1px solid #1E3A5F;'
            f'border-left:4px solid #8B5CF6;border-radius:10px;'
            f'padding:18px 20px;font-size:14px;line-height:1.8;'
            f'color:#E2E8F0;white-space:pre-wrap;margin-bottom:8px;">'
            f'{report}</div>',
            unsafe_allow_html=True
        )

        rc1, _ = st.columns([1,4])
        with rc1:
            if st.button('↺ Regenerate', key=f'regen_{pid}'):
                del st.session_state.reports[rkey]
                st.rerun()

        # ── Doctor Review ────────────────────────────────────
        st.markdown(section_title('Your Review'), unsafe_allow_html=True)

        edited = st.text_area(
            'Edit report if needed',
            value=report, height=150,
            key=f'edit_{pid}',
            label_visibility='collapsed'
        )

        # Prescription
        st.markdown(
            '<div style="font-size:14px;font-weight:500;color:#F1F5F9;'
            'margin:12px 0 8px;">Prescription / Instructions for Patient</div>',
            unsafe_allow_html=True
        )

        default_rx = '\n'.join(
            PRESCRIPTIONS.get(fus, PRESCRIPTIONS['Unknown'])
        ) if fus in PRESCRIPTIONS else ''

        prescription = st.text_area(
            'Prescription',
            value=default_rx,
            height=120,
            key=f'rx_{pid}',
            label_visibility='collapsed',
            placeholder='Enter prescription and follow-up instructions...'
        )

        notes = st.text_input(
            'Additional clinical notes',
            placeholder='Add any observations or amendments...',
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
                    'status':        'APPROVED',
                    'final_report':  edited,
                    'prescription':  prescription,
                    'doctor_notes':  notes,
                    'reviewed_at':   datetime.now().isoformat(),
                    'reviewed_by':   active['name'],
                })
                st.success('✅  Report approved and released to patient.')
                st.balloons()

        with b2:
            if st.button('✏️  Approve with Edits',
                         key=f'edit_app_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':        'APPROVED',
                    'final_report':  edited,
                    'prescription':  prescription,
                    'doctor_notes':  notes,
                    'reviewed_at':   datetime.now().isoformat(),
                    'reviewed_by':   active['name'],
                })
                st.info('Report approved with your amendments.')

        with b3:
            if st.button('❌  Reject',
                         key=f'rej_{pid}',
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':        'REJECTED',
                    'doctor_notes':  notes,
                    'reviewed_at':   datetime.now().isoformat(),
                    'reviewed_by':   active['name'],
                })
                st.error('Report rejected. Patient notified to contact clinic.')

        cur = st.session_state.patients[pid].get('status','PENDING')
        if cur == 'APPROVED':
            rev  = st.session_state.patients[pid].get('reviewed_by','')
            time = st.session_state.patients[pid].get('reviewed_at','')[:16]
            st.markdown(
                f'<div style="background:rgba(16,185,129,0.08);'
                f'border:1px solid rgba(16,185,129,0.2);border-radius:10px;'
                f'padding:14px 18px;margin-top:12px;">'
                f'<div style="font-size:14px;font-weight:600;color:#10B981;">'
                f'✅  Approved by {rev}  ·  {time}</div>'
                f'<div style="font-size:13px;color:#64748B;margin-top:4px;">'
                f'Report released to patient.</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button('View Patient Notification →',
                         key=f'view_{pid}'):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
