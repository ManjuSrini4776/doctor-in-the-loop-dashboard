import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (SEV_COLOR, SEV_BG, SEV_EMOJI,
                   CT_NAMES, CT_DESC, US_NAMES, US_DESC,
                   SCORE_TO_LABEL, DOCTORS,
                   load_lab, load_ct, load_us, load_fusion)


def render():
    st.markdown(
        '<div style="font-size:28px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.7px;margin-bottom:6px;">Patient Portal</div>'
        '<div style="font-size:16px;color:#7A90A8;margin-bottom:28px;">'
        'Find your test record, review your results and send to your doctor</div>',
        unsafe_allow_html=True
    )

    # Load data
    loaded = {}
    for key, fn, label in [
        ('lab', load_lab, 'Lab Report'),
        ('ct',  load_ct,  'CT Scan'),
        ('us',  load_us,  'Ultrasound'),
        ('fus', load_fusion, 'Combined Assessment'),
    ]:
        df = fn()
        if df is not None:
            loaded[label] = df

    if not loaded:
        st.markdown(
            '<div style="background:#112033;border:2px dashed #1E3250;'
            'border-radius:14px;padding:56px;text-align:center;">'
            '<div style="font-size:40px;margin-bottom:16px;">📂</div>'
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:8px;">No data files found</div>'
            '<div style="font-size:14px;color:#7A90A8;">'
            'Upload lab_data.csv, ct_data.csv, us_data.csv, fusion_data.csv '
            'to the repository data/ folder.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # ── STEP 1: Find Record ───────────────────────────────────
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-left:4px solid #2563EB;border-radius:12px;'
        'padding:20px 24px;margin-bottom:24px;">'
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
        'margin-bottom:6px;">Step 1 — Find Your Record</div>'
        '<div style="font-size:14px;color:#7A90A8;">'
        'Select your test type, then choose your patient ID from the dropdown. '
        'Severe cases are shown first for easy access.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    fc1, fc2 = st.columns([1, 3])
    with fc1:
        st.markdown(
            '<div style="font-size:14px;font-weight:600;color:#94A3B8;'
            'margin-bottom:6px;">TEST TYPE</div>',
            unsafe_allow_html=True
        )
        test_type = st.selectbox(
            'Test Type', ['All Types'] + list(loaded.keys()),
            key='pp_test_type', label_visibility='collapsed'
        )

    search_in = loaded if test_type == 'All Types' else \
                {test_type: loaded[test_type]} if test_type in loaded else {}

    type_short = {'Lab Report':'Lab','CT Scan':'CT',
                  'Ultrasound':'US','Combined Assessment':'MM'}
    sev_order  = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
    all_opts   = []

    for mtype, df in search_in.items():
        ts = type_short.get(mtype, mtype)
        for _, row in df.head(100).iterrows():
            pid  = str(row['_id'])
            sev  = row.get('_sev','Unknown')
            icon = SEV_EMOJI.get(sev,'⚪')
            all_opts.append({
                'label': icon + '  ' + pid + '   [' + ts + ']   ' + sev,
                'id':    pid,
                'mtype': mtype,
                'sev':   sev
            })

    all_opts.sort(key=lambda x: sev_order.get(x['sev'], 4))

    with fc2:
        st.markdown(
            '<div style="font-size:14px;font-weight:600;color:#94A3B8;'
            'margin-bottom:6px;">PATIENT RECORD  ·  '
            + str(len(all_opts)) + ' records</div>',
            unsafe_allow_html=True
        )
        chosen_label = st.selectbox(
            'Select Patient', [o['label'] for o in all_opts],
            key='pp_select', label_visibility='collapsed'
        )

    chosen    = next((o for o in all_opts if o['label'] == chosen_label), None)
    found_row = None
    found_type= None

    if chosen:
        df = loaded.get(chosen['mtype'])
        if df is not None:
            match = df[df['_id'] == chosen['id']]
            if not match.empty:
                found_row  = match.iloc[0].to_dict()
                found_type = chosen['mtype']

    # ── Record card ───────────────────────────────────────────
    if found_row:
        pid = chosen['id']
        sev = found_row.get('_sev','Unknown')
        clr = SEV_COLOR.get(sev,'#8892A4')
        bg  = SEV_BG.get(sev,'rgba(136,146,164,0.12)')

        st.markdown(
            '<div style="background:' + bg + ';border:2px solid ' + clr + '44;'
            'border-left:5px solid ' + clr + ';border-radius:12px;'
            'padding:18px 24px;margin:16px 0;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;">'
            '<div>'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
            'Record Found</div>'
            '<div style="font-size:24px;font-weight:800;color:#F0F6FF;'
            'font-family:monospace;letter-spacing:-0.5px;">' + pid + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
            + found_type + '</div>'
            '</div>'
            '<div style="background:' + bg + ';border:2px solid ' + clr + '66;'
            'border-radius:10px;padding:12px 24px;text-align:center;">'
            '<div style="font-size:12px;font-weight:600;color:' + clr + ';'
            'letter-spacing:0.08em;margin-bottom:4px;">OVERALL STATUS</div>'
            '<div style="font-size:22px;font-weight:800;color:' + clr + ';">'
            + sev + '</div>'
            '</div>'
            '</div></div>',
            unsafe_allow_html=True
        )

        # Findings
        show_findings(found_row, found_type)

    # ── STEP 2: Upload ────────────────────────────────────────
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-left:4px solid #7C3AED;border-radius:12px;'
        'padding:20px 24px;margin:24px 0 16px;">'
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
        'margin-bottom:6px;">Step 2 — Upload Lab Report (Optional)</div>'
        '<div style="font-size:14px;color:#7A90A8;">'
        'Upload a digital copy of your lab report for additional AI analysis.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader(
        'Upload', type=['csv','pdf','png','jpg','jpeg'],
        key='pp_upload', label_visibility='collapsed'
    )
    if uploaded_file:
        st.success('✅  ' + uploaded_file.name + ' uploaded successfully')

    # ── STEP 3: Details ───────────────────────────────────────
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
        'margin:24px 0 16px;">Step 3 — Your Details</div>',
        unsafe_allow_html=True
    )
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown('<div style="font-size:14px;font-weight:600;color:#94A3B8;margin-bottom:4px;">FULL NAME *</div>', unsafe_allow_html=True)
        pat_name = st.text_input('Name', placeholder='e.g. Ramesh Kumar',
                                 key='pp_name', label_visibility='collapsed')
        st.markdown('<div style="font-size:14px;font-weight:600;color:#94A3B8;margin:12px 0 4px;">AGE</div>', unsafe_allow_html=True)
        pat_age  = st.number_input('Age', min_value=1, max_value=120,
                                   value=35, key='pp_age',
                                   label_visibility='collapsed')
        st.markdown('<div style="font-size:14px;font-weight:600;color:#94A3B8;margin:12px 0 4px;">PHONE NUMBER *</div>', unsafe_allow_html=True)
        pat_phone = st.text_input('Phone', placeholder='+91 98765 43210',
                                  key='pp_phone', label_visibility='collapsed')
    with dc2:
        st.markdown('<div style="font-size:14px;font-weight:600;color:#94A3B8;margin-bottom:4px;">GENDER</div>', unsafe_allow_html=True)
        pat_gender = st.selectbox('Gender', ['Male','Female','Other'],
                                  key='pp_gender', label_visibility='collapsed')
        st.markdown('<div style="font-size:14px;font-weight:600;color:#94A3B8;margin:12px 0 4px;">SYMPTOMS / REASON FOR VISIT</div>', unsafe_allow_html=True)
        pat_symptoms = st.text_area('Symptoms',
                                    placeholder='Describe your symptoms or reason for this test...',
                                    height=130, key='pp_symptoms',
                                    label_visibility='collapsed')

    # ── STEP 4: Doctor ────────────────────────────────────────
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
        'margin:24px 0 16px;">Step 4 — Select Your Doctor</div>',
        unsafe_allow_html=True
    )

    doc_opts = {
        doc_id: doc for doc_id, doc in DOCTORS.items()
        if found_type is None or found_type in doc['sees']
    }
    if not doc_opts:
        doc_opts = DOCTORS

    doc_cols = st.columns(len(doc_opts))
    for col, (doc_id, doc) in zip(doc_cols, doc_opts.items()):
        is_sel = st.session_state.get('selected_doc') == doc_id
        with col:
            st.markdown(
                '<div style="background:' +
                ('rgba(37,99,235,0.15)' if is_sel else '#112033') +
                ';border:' +
                ('2px solid #2563EB' if is_sel else '1.5px solid #1E3250') +
                ';border-radius:12px;padding:18px 14px;text-align:center;'
                'margin-bottom:10px;min-height:150px;">'
                '<div style="font-size:28px;margin-bottom:10px;">🩺</div>'
                '<div style="font-size:14px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:4px;">' + doc['name'] + '</div>'
                '<div style="font-size:12px;color:#7A90A8;margin-bottom:6px;">'
                + doc['dept'] + '</div>'
                '<div style="font-size:11px;color:' + doc['color'] + ';'
                'font-weight:600;">' + '  ·  '.join(doc['sees']) + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button(
                '✓ Selected' if is_sel else 'Select',
                key='doc_' + doc_id,
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                st.session_state['selected_doc'] = doc_id
                st.rerun()

    selected_doc = st.session_state.get('selected_doc')
    st.markdown('<br>', unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────
    if found_row and selected_doc and pat_name and pat_phone:
        pid    = chosen['id']
        already = pid in st.session_state.patients

        if already:
            doc_name = st.session_state.patients[pid].get('doctor_name','')
            status   = st.session_state.patients[pid].get('status','PENDING')
            st.success('✅  Already submitted to ' + doc_name + '  ·  ' + status)
            if st.button('View My Report →', key='pp_goto_result',
                         use_container_width=True, type='primary'):
                st.session_state.patient_lookup = pid
                st.session_state.page = 'result'
                st.rerun()
        else:
            doc = DOCTORS[selected_doc]
            if st.button('📤  Submit for Doctor Review',
                         key='pp_submit',
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
                st.success('✅  Case sent to ' + doc['name'] + ' for review!')
                st.balloons()
                st.markdown(
                    '<div style="background:rgba(0,196,140,0.1);'
                    'border:1.5px solid rgba(0,196,140,0.3);border-radius:12px;'
                    'padding:20px 24px;margin-top:14px;">'
                    '<div style="font-size:16px;font-weight:700;color:#00C48C;'
                    'margin-bottom:10px;">Case Submitted Successfully</div>'
                    '<div style="font-size:15px;color:#94A3B8;line-height:1.8;">'
                    'Reference Number: <b style="color:#F0F6FF;font-family:monospace;'
                    'font-size:17px;">' + pid + '</b><br>'
                    'Doctor: <b style="color:#F0F6FF;">' + doc['name'] + '</b><br>'
                    'You will be notified once your doctor approves the report.<br>'
                    '<span style="color:#00C48C;font-weight:600;">'
                    'No need to visit the hospital for routine results.</span>'
                    '</div></div>',
                    unsafe_allow_html=True
                )
    elif found_row and not selected_doc:
        st.info('👆  Please select a doctor above to continue.')
    elif found_row and selected_doc and (not pat_name or not pat_phone):
        st.info('👆  Please fill in your name and phone number to continue.')


def show_findings(row, mtype):
    if mtype == 'Lab Report':
        ckd = row.get('ckd_severity','')
        dia = row.get('diabetes_severity_final','')
        thy = row.get('thyroid_severity_final','')

        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#F0F6FF;'
            'margin:18px 0 12px;">Your Lab Results</div>',
            unsafe_allow_html=True
        )
        c1, c2, c3 = st.columns(3)
        for col, (lbl, val) in zip([c1,c2,c3], [
            ('Kidney Function', ckd),
            ('Blood Sugar Level', dia),
            ('Thyroid Function', thy)
        ]):
            v = str(val) if val and str(val) not in ['None','nan','NaN',''] \
                else 'Within normal range'
            with col:
                st.markdown(
                    '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                    'border-radius:10px;padding:16px 18px;">'
                    '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                    'letter-spacing:0.08em;text-transform:uppercase;'
                    'margin-bottom:8px;">' + lbl + '</div>'
                    '<div style="font-size:17px;font-weight:600;color:#F0F6FF;">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

    elif mtype == 'CT Scan':
        cls  = row.get('ct_predicted_class','')
        sev  = row.get('ct_severity_label','Unknown')
        clr  = SEV_COLOR.get(sev,'#8892A4')
        name = CT_NAMES.get(cls, cls)
        desc = CT_DESC.get(cls,'')

        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#F0F6FF;'
            'margin:18px 0 12px;">Your CT Scan Result</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid ' + clr + ';border-radius:10px;'
            'padding:18px 22px;">'
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Ultrasound':
        cls  = row.get('predicted_class','')
        sev  = row.get('us_severity_label','Unknown')
        clr  = SEV_COLOR.get(sev,'#8892A4')
        name = US_NAMES.get(cls, cls)
        desc = US_DESC.get(cls,'')

        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#F0F6FF;'
            'margin:18px 0 12px;">Your Ultrasound Result</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid ' + clr + ';border-radius:10px;'
            'padding:18px 22px;">'
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Combined Assessment':
        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#F0F6FF;'
            'margin:18px 0 12px;">Combined Assessment Results</div>',
            unsafe_allow_html=True
        )
        c1,c2,c3 = st.columns(3)
        for col,(lbl,key) in zip([c1,c2,c3],[
            ('Lab Result','lab_score'),
            ('CT Result','ct_score'),
            ('Ultrasound','us_score')
        ]):
            val = row.get(key)
            try:
                v = SCORE_TO_LABEL.get(int(float(val)),'—') \
                    if val is not None and str(val) not in ['None','nan'] else '—'
            except Exception:
                v = '—'
            clr = SEV_COLOR.get(v,'#4A6080')
            with col:
                st.markdown(
                    '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                    'border-radius:10px;padding:16px;text-align:center;">'
                    '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                    'letter-spacing:0.08em;text-transform:uppercase;'
                    'margin-bottom:8px;">' + lbl + '</div>'
                    '<div style="font-size:22px;font-weight:800;color:' + clr + ';">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
