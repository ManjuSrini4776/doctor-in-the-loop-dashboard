import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (SEV_COLORS, SEV_BG, CT_NAMES, US_NAMES,
                   SCORE_TO_LABEL, DOCTORS,
                   load_lab, load_ct, load_us, load_fusion,
                   sev_badge, section_title)

SEV_EMOJI = {'Normal':'🟢','Mild':'🟡','Moderate':'🟠','Severe':'🔴','Unknown':'⚪'}


def render():
    st.markdown(
        '<div style="font-size:26px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;margin-bottom:4px;">Patient Portal</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:24px;">'
        'Select your record, fill in your details and send to your doctor</div>',
        unsafe_allow_html=True
    )

    # Load data
    loaded = {}
    lab = load_lab()
    ct  = load_ct()
    us  = load_us()
    fus = load_fusion()
    if lab is not None: loaded['Lab Report']          = lab
    if ct  is not None: loaded['CT Scan']             = ct
    if us  is not None: loaded['Ultrasound']          = us
    if fus is not None: loaded['Combined Assessment'] = fus

    if not loaded:
        st.markdown(
            '<div style="background:#111827;border:2px dashed #1E2D40;'
            'border-radius:12px;padding:48px;text-align:center;">'
            '<div style="font-size:32px;margin-bottom:12px;">📂</div>'
            '<div style="font-size:16px;font-weight:500;color:#F1F5F9;'
            'margin-bottom:8px;">No data files found</div>'
            '<div style="font-size:13px;color:#64748B;">'
            'Upload lab_data.csv, ct_data.csv, us_data.csv, fusion_data.csv '
            'to the repository data/ folder.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # ── STEP 1: Select patient from dropdown ─────────────────
    st.markdown(
        '<div style="background:#111827;border:1px solid #1E2D40;'
        'border-radius:12px;padding:18px 22px;margin-bottom:20px;">'
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin-bottom:6px;">Step 1 — Select Your Record</div>'
        '<div style="font-size:13px;color:#94A3B8;">'
        'Choose your test type and select your patient ID from the list below. '
        'Severe cases are shown first.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Test type filter
    fc1, fc2 = st.columns([1, 3])
    with fc1:
        test_type = st.selectbox(
            'Test Type',
            ['All Types'] + list(loaded.keys()),
            key='portal_test_type',
            label_visibility='collapsed'
        )

    # Build dropdown options
    search_in = loaded if test_type == 'All Types' else \
                {test_type: loaded[test_type]} if test_type in loaded else {}

    all_opts = []
    type_short = {
        'Lab Report':'Lab', 'CT Scan':'CT',
        'Ultrasound':'US',  'Combined Assessment':'MM'
    }
    sev_order = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}

    for mtype, df in search_in.items():
        ts = type_short.get(mtype, mtype)
        for _, row in df.head(100).iterrows():
            pid  = str(row['_id'])
            sev  = row.get('_sev', 'Unknown')
            icon = SEV_EMOJI.get(sev, '⚪')
            all_opts.append({
                'label': f"{icon}  {pid}  ·  [{ts}]  ·  {sev}",
                'id':    pid,
                'mtype': mtype,
                'sev':   sev
            })

    # Sort: severe first
    all_opts.sort(key=lambda x: sev_order.get(x['sev'], 4))

    with fc2:
        st.markdown(
            '<div style="font-size:12px;color:#64748B;margin-bottom:4px;">'
            + str(len(all_opts)) + ' records — severe cases shown first</div>',
            unsafe_allow_html=True
        )
        chosen_label = st.selectbox(
            'Select Patient',
            [o['label'] for o in all_opts],
            key='portal_select',
            label_visibility='collapsed'
        )

    # Find selected patient
    chosen = next((o for o in all_opts if o['label'] == chosen_label), None)
    found_row  = None
    found_type = None

    if chosen:
        df = loaded.get(chosen['mtype'])
        if df is not None:
            match = df[df['_id'] == chosen['id']]
            if not match.empty:
                found_row  = match.iloc[0].to_dict()
                found_type = chosen['mtype']

    # Show record
    if found_row:
        sev = found_row.get('_sev', 'Unknown')
        clr = SEV_COLORS.get(sev, '#94A3B8')
        bg  = SEV_BG.get(sev, 'rgba(148,163,184,0.1)')
        pid = chosen['id']

        st.markdown(
            '<div style="background:' + bg + ';border:2px solid ' + clr + '44;'
            'border-left:5px solid ' + clr + ';border-radius:12px;'
            'padding:14px 20px;margin:14px 0;">'
            '<div style="display:flex;justify-content:space-between;align-items:center;">'
            '<div>'
            '<div style="font-size:12px;color:#64748B;font-family:monospace;'
            'margin-bottom:4px;">RECORD FOUND</div>'
            '<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
            'font-family:monospace;">' + pid + '</div>'
            '<div style="font-size:13px;color:#94A3B8;margin-top:3px;">'
            + found_type + '</div>'
            '</div>'
            '<div>' + sev_badge(sev, 15) + '</div>'
            '</div></div>',
            unsafe_allow_html=True
        )
        show_findings(found_row, found_type)

    # ── STEP 2: Upload lab report ─────────────────────────────
    st.markdown(
        '<div style="background:#111827;border:1px solid #1E2D40;'
        'border-radius:12px;padding:18px 22px;margin:20px 0;">'
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin-bottom:6px;">Step 2 — Upload Lab Report (Optional)</div>'
        '<div style="font-size:13px;color:#94A3B8;">'
        'Upload a digital copy of your lab report for additional analysis.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader(
        'Upload report',
        type=['csv', 'pdf', 'png', 'jpg', 'jpeg'],
        key='patient_lab_upload',
        label_visibility='collapsed'
    )
    if uploaded_file:
        st.success('✅  ' + uploaded_file.name + ' uploaded')

    # ── STEP 3: Patient details ───────────────────────────────
    st.markdown(
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin:20px 0 14px;">Step 3 — Your Details</div>',
        unsafe_allow_html=True
    )
    dc1, dc2 = st.columns(2)
    with dc1:
        pat_name  = st.text_input('Full Name *',
                                  placeholder='e.g. Ramesh Kumar',
                                  key='pat_name')
        pat_age   = st.number_input('Age', min_value=1, max_value=120,
                                    value=35, key='pat_age')
        pat_phone = st.text_input('Phone Number *',
                                  placeholder='+91 98765 43210',
                                  key='pat_phone')
    with dc2:
        pat_gender   = st.selectbox('Gender', ['Male','Female','Other'],
                                    key='pat_gender')
        pat_symptoms = st.text_area('Symptoms / Reason for Visit',
                                    placeholder='Describe your symptoms...',
                                    height=120, key='pat_symptoms')

    # ── STEP 4: Select doctor ─────────────────────────────────
    st.markdown(
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin:20px 0 14px;">Step 4 — Select Your Doctor</div>',
        unsafe_allow_html=True
    )

    # Filter doctors by modality
    doc_opts = {}
    for doc_id, doc in DOCTORS.items():
        if found_type is None or found_type in doc['sees']:
            doc_opts[doc_id] = doc

    if not doc_opts:
        doc_opts = DOCTORS

    doc_cols = st.columns(len(doc_opts))
    for col, (doc_id, doc) in zip(doc_cols, doc_opts.items()):
        is_sel = st.session_state.get('selected_doc') == doc_id
        with col:
            st.markdown(
                '<div style="background:' +
                ('rgba(59,130,246,0.12)' if is_sel else '#111827') +
                ';border:' +
                ('2px solid #3B82F6' if is_sel else '1px solid #1E2D40') +
                ';border-radius:10px;padding:14px;text-align:center;margin-bottom:8px;">'
                '<div style="font-size:20px;margin-bottom:6px;">🩺</div>'
                '<div style="font-size:13px;font-weight:600;color:#F1F5F9;">'
                + doc['name'] +
                '</div>'
                '<div style="font-size:12px;color:#64748B;margin-top:3px;">'
                + doc['dept'] +
                '</div>'
                '<div style="font-size:11px;color:' + doc['color'] + ';margin-top:4px;">'
                + ', '.join(doc['sees']) +
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button('Select', key='selDoc_' + doc_id,
                         use_container_width=True,
                         type='primary' if is_sel else 'secondary'):
                st.session_state['selected_doc'] = doc_id
                st.rerun()

    selected_doc = st.session_state.get('selected_doc')
    st.markdown('<br>', unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────
    if found_row and selected_doc and pat_name and pat_phone:
        pid    = chosen['id']
        already = pid in st.session_state.patients

        if already:
            assigned = st.session_state.patients[pid].get('doctor_name','')
            status   = st.session_state.patients[pid].get('status','PENDING')
            st.success('✅  Already submitted to ' + assigned + '  ·  Status: ' + status)
            if st.button('Go to My Report →', key='goto_result',
                         use_container_width=True, type='primary'):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
        else:
            doc = DOCTORS[selected_doc]
            if st.button('📤  Submit for Doctor Review',
                         key='portal_submit',
                         use_container_width=True,
                         type='primary'):
                st.session_state.patients[pid] = {
                    **found_row,
                    'patient_id':    pid,
                    'case_id':       pid,
                    'name':          pat_name,
                    'age':           pat_age,
                    'gender':        pat_gender,
                    'phone':         pat_phone,
                    'symptoms':      pat_symptoms,
                    'doctor_id':     selected_doc,
                    'doctor_name':   doc['name'],
                    'doctor_dept':   doc['dept'],
                    'modality_type': found_type or 'Unknown',
                    'fusion_label':  found_row.get('_sev','Unknown'),
                    'severity_label':found_row.get('_sev','Unknown'),
                    'status':        'PENDING',
                    'registered_at': datetime.now().isoformat(),
                    'uploaded_file': uploaded_file.name if uploaded_file else None,
                }
                st.success('✅  Case sent to ' + doc['name'] + ' for review.')
                st.balloons()
                st.markdown(
                    '<div style="background:rgba(16,185,129,0.08);'
                    'border:1px solid rgba(16,185,129,0.2);border-radius:10px;'
                    'padding:16px 20px;margin-top:12px;">'
                    '<div style="font-size:15px;font-weight:600;color:#10B981;'
                    'margin-bottom:8px;">Case submitted successfully</div>'
                    '<div style="font-size:14px;color:#94A3B8;">'
                    'Reference: <b style="color:#F1F5F9;font-family:monospace;">'
                    + pid + '</b><br>'
                    'Doctor: <b style="color:#F1F5F9;">' + doc['name'] + '</b><br>'
                    'You will be notified once your doctor approves the report.<br>'
                    'No need to visit the hospital for routine results.</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
    elif not selected_doc and found_row:
        st.info('Please select a doctor above to continue.')
    elif (not pat_name or not pat_phone) and found_row and selected_doc:
        st.info('Please fill in your name and phone number to continue.')


def show_findings(row, mtype):
    if mtype == 'Lab Report':
        ckd = row.get('ckd_severity', '')
        dia = row.get('diabetes_severity_final', '')
        thy = row.get('thyroid_severity_final', '')
        st.markdown(section_title('Your Lab Results'), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        for col, (lbl, val) in zip([c1,c2,c3], [
            ('Kidney Function', ckd),
            ('Blood Sugar', dia),
            ('Thyroid Function', thy)
        ]):
            v = val if val and str(val) not in ['None','nan','NaN',''] \
                else 'Within normal range'
            with col:
                st.markdown(
                    '<div style="background:#0B1120;border:1px solid #1E2D40;'
                    'border-radius:10px;padding:14px;">'
                    '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    'letter-spacing:0.06em;margin-bottom:6px;">' + lbl + '</div>'
                    '<div style="font-size:15px;font-weight:600;color:#F1F5F9;">'
                    + str(v) + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

    elif mtype == 'CT Scan':
        cls  = row.get('ct_predicted_class', '')
        sev  = row.get('ct_severity_label', 'Unknown')
        clr  = SEV_COLORS.get(sev, '#94A3B8')
        diag = CT_NAMES.get(cls, cls)
        st.markdown(section_title('Your CT Scan Result'), unsafe_allow_html=True)
        st.markdown(
            '<div style="background:#0B1120;border:1px solid #1E2D40;'
            'border-left:4px solid ' + clr + ';border-radius:10px;padding:16px 20px;">'
            '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
            'margin-bottom:6px;">' + diag + '</div>'
            '<div style="font-size:13px;color:' + clr + ';">' + sev + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Ultrasound':
        cls  = row.get('predicted_class', '')
        sev  = row.get('us_severity_label', 'Unknown')
        clr  = SEV_COLORS.get(sev, '#94A3B8')
        diag = US_NAMES.get(cls, cls)
        st.markdown(section_title('Your Ultrasound Result'), unsafe_allow_html=True)
        st.markdown(
            '<div style="background:#0B1120;border:1px solid #1E2D40;'
            'border-left:4px solid ' + clr + ';border-radius:10px;padding:16px 20px;">'
            '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
            'margin-bottom:6px;">' + diag + '</div>'
            '<div style="font-size:13px;color:' + clr + ';">' + sev + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Combined Assessment':
        st.markdown(section_title('Your Combined Assessment'), unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        for col, (lbl, key) in zip([c1,c2,c3], [
            ('Lab Result', 'lab_score'),
            ('CT Result',  'ct_score'),
            ('Ultrasound', 'us_score')
        ]):
            val = row.get(key)
            try:
                v = SCORE_TO_LABEL.get(int(float(val)), '—') \
                    if val is not None and str(val) not in ['None','nan'] else '—'
            except Exception:
                v = '—'
            clr = SEV_COLORS.get(v, '#64748B')
            with col:
                st.markdown(
                    '<div style="background:#0B1120;border:1px solid #1E2D40;'
                    'border-radius:10px;padding:14px;text-align:center;">'
                    '<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    'letter-spacing:0.06em;margin-bottom:6px;">' + lbl + '</div>'
                    '<div style="font-size:18px;font-weight:700;color:' + clr + ';">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
