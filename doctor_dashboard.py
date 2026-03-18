import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import (SEV_COLOR, SEV_BG, CT_NAMES, CT_DESC, CT_IMAGE,
                   US_NAMES, US_DESC, US_IMAGE,
                   SCORE_TO_LABEL, DOCTORS, PRESCRIPTIONS)

URGENCY = {
    'Severe':   ('URGENT',      '#FF3B3B', 'rgba(255,59,59,0.12)'),
    'Moderate': ('SEMI-URGENT', '#FF6B35', 'rgba(255,107,53,0.12)'),
    'Mild':     ('ROUTINE',     '#FFB800', 'rgba(255,184,0,0.12)'),
    'Normal':   ('ROUTINE',     '#00C48C', 'rgba(0,196,140,0.12)'),
    'Unknown':  ('REVIEW',      '#8892A4', 'rgba(136,146,164,0.12)'),
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
        emb = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size':32}
        )
        for path in ['rag_output/baseline_vector_db',
                     'data/baseline_vector_db']:
            if os.path.exists(path):
                return FAISS.load_local(
                    path, emb, allow_dangerous_deserialization=True)
    except Exception:
        pass
    return None


def generate_report(p):
    fus   = p.get('fusion_label', p.get('severity_label','Unknown'))
    mtype = p.get('modality_type','')
    parts = []

    if mtype == 'Lab Report' or 'final_severity_label' in p:
        ckd = p.get('ckd_severity','')
        dia = p.get('diabetes_severity_final','')
        thy = p.get('thyroid_severity_final','')
        if ckd and str(ckd) not in ['None','nan']:
            parts.append('Kidney function: ' + str(ckd) + '.')
        if dia and str(dia) not in ['None','nan']:
            parts.append('Diabetes status: ' + str(dia) + '.')
        if thy and str(thy) not in ['None','nan']:
            parts.append('Thyroid function: ' + str(thy) + '.')

    if mtype == 'CT Scan' or 'ct_predicted_class' in p:
        cls  = p.get('ct_predicted_class','')
        conf = p.get('ct_confidence',0)
        parts.append('CT scan: ' + CT_NAMES.get(cls,cls) +
                     ' (confidence ' + str(round(float(conf)*100,1)) + '%).')

    if mtype == 'Ultrasound' or 'predicted_class' in p:
        cls  = p.get('predicted_class', p.get('us_predicted_class',''))
        conf = p.get('confidence', p.get('us_confidence',0))
        parts.append('Ultrasound: ' + US_NAMES.get(cls,cls) +
                     ' (confidence ' + str(round(float(conf)*100,1)) + '%).')

    if p.get('symptoms'):
        parts.append('Patient complaints: ' + str(p['symptoms']) + '.')
    parts.append('Overall assessment: ' + fus + ' severity.')
    query = ' '.join(parts)

    client = get_openai_client()
    rag_db = get_rag_db()
    context = ''
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            pass

    urg = URGENCY.get(fus, URGENCY['Unknown'])[0]
    action = {
        'Severe':   'Immediate specialist referral. Consider urgent admission.',
        'Moderate': 'Specialist review within 7 days.',
        'Mild':     'Outpatient follow-up within 2-4 weeks.',
        'Normal':   'Routine follow-up in 3 months.'
    }.get(fus, 'Discuss findings and arrange appropriate follow-up.')

    if client:
        prompt = (
            'You are a clinical decision support assistant.\n'
            'Generate a professional clinical summary. '
            'Do NOT mention AI, scores, model names or system details.\n\n'
            'Assessment:\n' + query + '\n\n' +
            ('Guidelines:\n' + context + '\n\n' if context else '') +
            'Format exactly as:\n'
            '**Clinical Summary**\n[2-3 sentences]\n\n'
            '**Key Findings**\n• [finding 1]\n• [finding 2]\n\n'
            '**Recommended Actions**\n[specific clinical steps]\n\n'
            '**Urgency:** ' + urg + '\n'
            '**Follow-up:** [specific timeline]\n\n'
            '*This report requires doctor approval before release to patient.*'
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

    findings = '\n'.join(['• ' + part for part in parts if part]) \
               or '• See individual test results above.'

    return (
        '**Clinical Summary**\n'
        'Patient presents with ' + fus.lower() + ' overall findings based on '
        + mtype.lower() + ' assessment. ' +
        ('Immediate clinical attention is warranted.'
         if fus == 'Severe' else
         'Clinical review and management planning required.'
         if fus in ['Moderate','Mild'] else
         'Results are within acceptable limits.') + '\n\n'
        '**Key Findings**\n' + findings + '\n\n'
        '**Recommended Actions**\n' + action + '\n\n'
        '**Urgency:** ' + urg + '\n'
        '**Follow-up:** ' +
        ('Within 24-48 hours' if fus == 'Severe' else
         'Within 7-10 days' if fus == 'Moderate' else
         'Within 2-4 weeks' if fus == 'Mild' else
         '3-month routine review') + '\n\n'
        '*This report requires doctor approval before release to patient.*'
    )


def render():
    st.markdown(
        '<div style="font-size:28px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.7px;margin-bottom:6px;">Doctor Dashboard</div>'
        '<div style="font-size:16px;color:#7A90A8;margin-bottom:20px;">'
        'Review patient reports, add prescriptions and release results</div>',
        unsafe_allow_html=True
    )

    # Doctor selector
    doc_opts = {doc['name'] + ' — ' + doc['dept']: k
                for k, doc in DOCTORS.items()}
    sel_label = st.selectbox('You are logged in as',
                             list(doc_opts.keys()),
                             key='dd_doctor',
                             label_visibility='collapsed')
    active_id = doc_opts[sel_label]
    active    = DOCTORS[active_id]

    # Doctor card
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-radius:12px;padding:16px 22px;margin-bottom:22px;'
        'display:flex;align-items:center;gap:16px;">'
        '<div style="background:' + active['color'] + '22;width:48px;height:48px;'
        'border-radius:50%;display:flex;align-items:center;justify-content:center;'
        'font-size:22px;border:2px solid ' + active['color'] + '44;flex-shrink:0;">'
        '🩺</div>'
        '<div style="flex:1;">'
        '<div style="font-size:17px;font-weight:700;color:#F0F6FF;">'
        + active['name'] + '</div>'
        '<div style="font-size:14px;color:#7A90A8;margin-top:2px;">'
        + active['dept'] + '  ·  ' + active['specialty'] + '</div>'
        '<div style="font-size:13px;color:' + active['color'] + ';'
        'font-weight:600;margin-top:4px;">'
        'Assigned cases: ' + ', '.join(active['sees']) + '</div>'
        '</div>'
        '<div style="background:rgba(0,196,140,0.12);border:1.5px solid '
        'rgba(0,196,140,0.3);color:#00C48C;font-size:13px;font-weight:600;'
        'padding:6px 16px;border-radius:20px;">● Active</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Filter patients
    my_patients = {
        pid: p for pid, p in st.session_state.patients.items()
        if p.get('doctor_id') == active_id
    }

    if not my_patients:
        st.markdown(
            '<div style="background:#112033;border:2px dashed #1E3250;'
            'border-radius:14px;padding:72px;text-align:center;">'
            '<div style="font-size:48px;margin-bottom:18px;">📭</div>'
            '<div style="font-size:20px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:10px;">No reports assigned yet</div>'
            '<div style="font-size:15px;color:#7A90A8;">'
            'Patient cases assigned to you will appear here.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # Stats row
    total    = len(my_patients)
    pending  = sum(1 for p in my_patients.values() if p.get('status')=='PENDING')
    approved = sum(1 for p in my_patients.values() if p.get('status')=='APPROVED')
    urgent   = sum(1 for p in my_patients.values()
                   if p.get('fusion_label','')=='Severe'
                   and p.get('status')=='PENDING')

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,clr) in zip([c1,c2,c3,c4],[
        ('Total Cases',     total,    '#4A9EFF'),
        ('Awaiting Review', pending,  '#FFB800'),
        ('Approved',        approved, '#00C48C'),
        ('Urgent',          urgent,   '#FF3B3B'),
    ]):
        with col:
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-top:3px solid ' + clr + ';border-radius:12px;'
                'padding:18px;text-align:center;margin-bottom:18px;">'
                '<div style="font-size:36px;font-weight:800;color:' + clr + ';'
                'line-height:1;">' + str(val) + '</div>'
                '<div style="font-size:14px;color:#7A90A8;margin-top:6px;'
                'font-weight:500;">' + lbl + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # Two column layout
    left, right = st.columns([1, 2.5], gap='large')

    with left:
        st.markdown(
            '<div style="font-size:15px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:0.08em;'
            'margin-bottom:14px;">Patient Queue</div>',
            unsafe_allow_html=True
        )

        sorted_pats = sorted(my_patients.items(), key=lambda x:(
            0 if x[1].get('fusion_label','')=='Severe' else
            1 if x[1].get('fusion_label','')=='Moderate' else
            2 if x[1].get('status')=='PENDING' else 3
        ))

        for pid, p in sorted_pats:
            status = p.get('status','PENDING')
            fus    = p.get('fusion_label', p.get('severity_label','Unknown'))
            clr    = SEV_COLOR.get(fus,'#8892A4')
            is_sel = st.session_state.current_patient == pid
            s_icon = {'APPROVED':'✓','REJECTED':'✗','PENDING':'○'}.get(status,'○')

            if st.button(
                s_icon + '  ' + str(pid) + '\n' +
                p.get('name','Patient') + '  ·  ' + fus,
                key='dd_pt_' + pid,
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                rkey = 'report_' + pid
                if rkey not in st.session_state.reports:
                    with st.spinner('Generating clinical report...'):
                        st.session_state.reports[rkey] = generate_report(p)
                st.session_state.current_patient = pid
                st.rerun()

    with right:
        pid = st.session_state.current_patient
        if not pid or pid not in my_patients:
            st.markdown(
                '<div style="background:#112033;border:2px dashed #1E3250;'
                'border-radius:14px;padding:96px;text-align:center;">'
                '<div style="font-size:40px;margin-bottom:14px;">👈</div>'
                '<div style="font-size:16px;color:#7A90A8;">'
                'Select a patient case from the queue</div>'
                '</div>',
                unsafe_allow_html=True
            )
            return

        p       = my_patients[pid]
        fus     = p.get('fusion_label', p.get('severity_label','Unknown'))
        fus_clr = SEV_COLOR.get(fus,'#8892A4')
        mtype   = p.get('modality_type','')
        urg_tag, urg_clr, urg_bg = URGENCY.get(fus, URGENCY['Unknown'])

        # Patient header card
        st.markdown(
            '<div style="background:#112033;border:1.5px solid #1E3250;'
            'border-radius:14px;padding:20px 24px;margin-bottom:22px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:flex-start;">'
            '<div>'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
            'Patient</div>'
            '<div style="font-size:22px;font-weight:800;color:#F0F6FF;'
            'letter-spacing:-0.3px;">' + p.get('name','Patient') + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
            'Ref: <span style="font-family:monospace;color:#94A3B8;">' +
            str(pid) + '</span>'
            + ('  ·  ' + str(p.get('age','')) + ' yrs' if p.get('age') else '') +
            '  ·  ' + mtype + '</div>'
            + ('<div style="font-size:14px;color:#94A3B8;margin-top:6px;">'
               'Complaint: ' + str(p.get('symptoms','')) + '</div>'
               if p.get('symptoms') else '') +
            '<div style="font-size:12px;color:#4A6080;margin-top:6px;">'
            'Submitted: ' + p.get('registered_at','')[:16] + '</div>'
            '</div>'
            '<div style="background:' + urg_bg + ';border:2px solid ' +
            urg_clr + '44;border-radius:12px;padding:14px 22px;text-align:center;">'
            '<div style="font-size:12px;font-weight:700;color:' + urg_clr + ';'
            'letter-spacing:0.12em;margin-bottom:6px;">' + urg_tag + '</div>'
            '<div style="font-size:22px;font-weight:800;color:' + fus_clr + ';">'
            + fus + '</div>'
            '</div></div></div>',
            unsafe_allow_html=True
        )

        # ── Clinical Findings ─────────────────────────────────
        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:0.08em;'
            'margin-bottom:14px;">Clinical Findings</div>',
            unsafe_allow_html=True
        )

        # Lab findings
        if mtype == 'Lab Report' or 'final_severity_label' in p:
            ckd = p.get('ckd_severity','')
            dia = p.get('diabetes_severity_final','')
            thy = p.get('thyroid_severity_final','')
            c1,c2,c3 = st.columns(3)
            for col,(lbl,val) in zip([c1,c2,c3],[
                ('Kidney Function',  ckd),
                ('Blood Sugar',      dia),
                ('Thyroid Function', thy)
            ]):
                v = str(val) if val and str(val) not in ['None','nan','NaN'] \
                    else 'Normal'
                with col:
                    st.markdown(
                        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                        'border-radius:10px;padding:16px 18px;margin-bottom:12px;">'
                        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                        'letter-spacing:0.08em;text-transform:uppercase;'
                        'margin-bottom:8px;">' + lbl + '</div>'
                        '<div style="font-size:17px;font-weight:600;color:#F0F6FF;">'
                        + v + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )

        # CT findings + GradCAM
        if mtype == 'CT Scan' or 'ct_predicted_class' in p:
            cls  = p.get('ct_predicted_class','')
            conf = p.get('ct_confidence',0)
            sev  = p.get('ct_severity_label','Unknown')
            clr  = SEV_COLOR.get(sev,'#8892A4')
            name = CT_NAMES.get(cls,cls)
            desc = CT_DESC.get(cls,'')

            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-left:5px solid ' + clr + ';border-radius:10px;'
                'padding:18px 22px;margin-bottom:16px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">'
                'CT Brain Scan</div>'
                '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:6px;">' + name + '</div>'
                '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
                + desc + '</div>'
                '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
                + sev + '  ·  Confidence: ' + str(round(float(conf)*100,1)) + '%'
                '</div></div>',
                unsafe_allow_html=True
            )

            # GradCAM image
            img_path = CT_IMAGE.get(cls,'')
            if img_path and os.path.exists(img_path):
                st.markdown(
                    '<div style="font-size:15px;font-weight:700;color:#F0F6FF;'
                    'margin-bottom:10px;">AI Attention Map (Grad-CAM)</div>',
                    unsafe_allow_html=True
                )
                gc1, gc2 = st.columns(2)
                with gc1:
                    st.image(img_path, caption='CT Scan',
                             use_column_width=True)
                with gc2:
                    st.image(img_path, caption='Grad-CAM Heatmap',
                             use_column_width=True)
                st.markdown(
                    '<div style="font-size:13px;color:#4A6080;margin-bottom:14px;">'
                    'Highlighted regions show where the AI model focused '
                    'to reach its classification decision.</div>',
                    unsafe_allow_html=True
                )

        # US findings + GradCAM
        if mtype == 'Ultrasound' or 'predicted_class' in p:
            cls  = p.get('predicted_class', p.get('us_predicted_class',''))
            conf = p.get('confidence', p.get('us_confidence',0))
            sev  = p.get('us_severity_label','Unknown')
            clr  = SEV_COLOR.get(sev,'#8892A4')
            name = US_NAMES.get(cls,cls)
            desc = US_DESC.get(cls,'')

            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-left:5px solid ' + clr + ';border-radius:10px;'
                'padding:18px 22px;margin-bottom:16px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">'
                'Obstetric Ultrasound</div>'
                '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:6px;">' + name + '</div>'
                '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
                + desc + '</div>'
                '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
                + sev + '  ·  Confidence: ' + str(round(float(conf)*100,1)) + '%'
                '</div></div>',
                unsafe_allow_html=True
            )

            img_path = US_IMAGE.get(cls,'')
            if img_path and os.path.exists(img_path):
                st.markdown(
                    '<div style="font-size:15px;font-weight:700;color:#F0F6FF;'
                    'margin-bottom:10px;">AI Attention Map (Grad-CAM)</div>',
                    unsafe_allow_html=True
                )
                ug1, ug2 = st.columns(2)
                with ug1:
                    st.image(img_path, caption='Ultrasound Scan',
                             use_column_width=True)
                with ug2:
                    st.image(img_path, caption='Grad-CAM Heatmap',
                             use_column_width=True)

        # Combined
        if mtype == 'Combined Assessment':
            c1,c2,c3 = st.columns(3)
            for col,(lbl,key) in zip([c1,c2,c3],[
                ('Lab Score','lab_score'),
                ('CT Score','ct_score'),
                ('Ultrasound Score','us_score')
            ]):
                val = p.get(key)
                try:
                    v = SCORE_TO_LABEL.get(int(float(val)),'—') \
                        if val is not None and str(val) not in ['None','nan'] else '—'
                except Exception:
                    v = '—'
                clr = SEV_COLOR.get(v,'#4A6080')
                with col:
                    st.markdown(
                        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                        'border-radius:10px;padding:16px;text-align:center;'
                        'margin-bottom:12px;">'
                        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                        'letter-spacing:0.08em;text-transform:uppercase;'
                        'margin-bottom:8px;">' + lbl + '</div>'
                        '<div style="font-size:26px;font-weight:800;color:' + clr + ';">'
                        + v + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )

        # ── AI Clinical Report ────────────────────────────────
        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:0.08em;'
            'margin:20px 0 12px;">AI Clinical Report</div>',
            unsafe_allow_html=True
        )

        rkey = 'report_' + pid
        if rkey not in st.session_state.reports:
            with st.spinner('Generating...'):
                st.session_state.reports[rkey] = generate_report(p)

        report = st.session_state.reports[rkey]

        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #263A55;'
            'border-left:5px solid #7C3AED;border-radius:12px;'
            'padding:22px 26px;font-size:15px;line-height:1.85;'
            'color:#E8EDF5;white-space:pre-wrap;margin-bottom:10px;">'
            + report +
            '</div>',
            unsafe_allow_html=True
        )

        rc1, _ = st.columns([1,5])
        with rc1:
            if st.button('↺ Regenerate', key='regen_' + pid):
                del st.session_state.reports[rkey]
                st.rerun()

        # ── Doctor Review ─────────────────────────────────────
        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#94A3B8;'
            'text-transform:uppercase;letter-spacing:0.08em;'
            'margin:20px 0 12px;">Your Review</div>',
            unsafe_allow_html=True
        )

        edited = st.text_area(
            'Edit report if needed',
            value=report, height=150,
            key='edit_' + pid,
            label_visibility='collapsed'
        )

        # Prescription
        st.markdown(
            '<div style="font-size:15px;font-weight:700;color:#F0F6FF;'
            'margin:16px 0 8px;">Prescription & Instructions for Patient</div>',
            unsafe_allow_html=True
        )
        default_rx = '\n'.join(PRESCRIPTIONS.get(fus, []))
        prescription = st.text_area(
            'Prescription',
            value=default_rx, height=120,
            key='rx_' + pid,
            label_visibility='collapsed',
            placeholder='Enter prescription and follow-up instructions...'
        )

        notes = st.text_input(
            'Additional clinical notes (internal)',
            placeholder='Add observations, amendments or private notes...',
            key='notes_' + pid,
            label_visibility='collapsed'
        )

        st.markdown('<br>', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button('✅  Approve & Release',
                         key='app_' + pid,
                         use_container_width=True,
                         type='primary'):
                st.session_state.patients[pid].update({
                    'status':       'APPROVED',
                    'final_report': edited,
                    'prescription': prescription,
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name'],
                })
                st.success('✅  Report approved and released to patient!')
                st.balloons()
        with b2:
            if st.button('✏️  Approve with Edits',
                         key='edit_app_' + pid,
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':       'APPROVED',
                    'final_report': edited,
                    'prescription': prescription,
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name'],
                })
                st.info('Report approved with your amendments.')
        with b3:
            if st.button('❌  Reject',
                         key='rej_' + pid,
                         use_container_width=True):
                st.session_state.patients[pid].update({
                    'status':       'REJECTED',
                    'doctor_notes': notes,
                    'reviewed_at':  datetime.now().isoformat(),
                    'reviewed_by':  active['name'],
                })
                st.error('Report rejected. Patient notified to contact clinic.')

        cur = st.session_state.patients[pid].get('status','PENDING')
        if cur == 'APPROVED':
            rev  = st.session_state.patients[pid].get('reviewed_by','')
            time = st.session_state.patients[pid].get('reviewed_at','')[:16]
            st.markdown(
                '<div style="background:rgba(0,196,140,0.1);'
                'border:1.5px solid rgba(0,196,140,0.3);border-radius:10px;'
                'padding:16px 20px;margin-top:14px;">'
                '<div style="font-size:15px;font-weight:700;color:#00C48C;">'
                '✅  Approved by ' + rev + '  ·  ' + time + '</div>'
                '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
                'Report has been released to the patient.</div>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button('View Patient Notification →',
                         key='view_' + pid):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
        elif cur == 'REJECTED':
            st.markdown(
                '<div style="background:rgba(255,59,59,0.1);'
                'border:1.5px solid rgba(255,59,59,0.3);border-radius:10px;'
                'padding:16px 20px;margin-top:14px;">'
                '<div style="font-size:15px;font-weight:700;color:#FF3B3B;">'
                '❌  Report Rejected</div>'
                '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
                'Patient notified to contact the clinic.</div>'
                '</div>',
                unsafe_allow_html=True
            )
