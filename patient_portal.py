import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from utils import (SEV_COLORS, SEV_BG, CT_NAMES, US_NAMES,
                   SCORE_TO_LABEL, DOCTORS,
                   load_lab, load_ct, load_us, load_fusion,
                   sev_badge, section_title)


def render():
    st.markdown(
        '<div style="font-size:26px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;margin-bottom:4px;">Patient Portal</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:24px;">'
        'Search your test results and send them to your doctor for review</div>',
        unsafe_allow_html=True
    )

    # Load all datasets
    data = {
        'Lab Report':          load_lab(),
        'CT Scan':             load_ct(),
        'Ultrasound':          load_us(),
        'Combined Assessment': load_fusion(),
    }
    loaded = {k: v for k, v in data.items() if v is not None}

    # ── STEP 1: Search by patient ID ─────────────────────────
    st.markdown(
        '<div style="background:#111827;border:1px solid #1E2D40;'
        'border-radius:12px;padding:20px 24px;margin-bottom:20px;">'
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin-bottom:6px;">Step 1 — Find Your Record</div>'
        '<div style="font-size:13px;color:#94A3B8;margin-bottom:14px;">'
        'Enter your patient reference number to find your test results. '
        'This was given to you at the hospital reception.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    sc1, sc2, sc3 = st.columns([2, 1, 1])
    with sc1:
        search_id = st.text_input(
            'Patient Reference Number',
            placeholder='e.g. 24992831  or  MM-001  or  168',
            label_visibility='collapsed',
            key='portal_search_id'
        )
    with sc2:
        test_type = st.selectbox(
            'Test Type',
            ['All Types'] + list(loaded.keys()),
            key='portal_test_type',
            label_visibility='collapsed'
        )
    with sc3:
        st.markdown('<br>', unsafe_allow_html=True)
        search_btn = st.button('🔍  Search', key='portal_search_btn',
                               use_container_width=True, type='primary')

    # Search result
    found_row  = None
    found_type = None

    if search_id and search_id.strip():
        sid = search_id.strip()
        search_in = loaded if test_type == 'All Types' else \
                    {test_type: loaded[test_type]} if test_type in loaded else {}

        for mtype, df in search_in.items():
            match = df[df['_id'] == sid]
            if not match.empty:
                found_row  = match.iloc[0].to_dict()
                found_type = mtype
                break

        if found_row:
            sev  = found_row.get('_sev', 'Unknown')
            clr  = SEV_COLORS.get(sev, '#94A3B8')
            st.markdown(
                f'<div style="background:{SEV_BG.get(sev,"rgba(148,163,184,0.1)")};'
                f'border:2px solid {clr}44;border-left:5px solid {clr};'
                f'border-radius:12px;padding:16px 22px;margin:14px 0;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;">'
                f'<div>'
                f'<div style="font-size:12px;color:#64748B;font-family:monospace;'
                f'margin-bottom:4px;">RECORD FOUND</div>'
                f'<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
                f'font-family:monospace;">{sid}</div>'
                f'<div style="font-size:13px;color:#94A3B8;margin-top:3px;">'
                f'{found_type}</div>'
                f'</div>'
                f'<div>{sev_badge(sev, 15)}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )
            # Show findings
            show_findings(found_row, found_type)

        elif search_id.strip():
            st.markdown(
                '<div style="background:rgba(239,68,68,0.08);'
                'border:1px solid rgba(239,68,68,0.2);border-radius:10px;'
                'padding:14px 20px;margin-top:12px;">'
                '<div style="font-size:14px;color:#EF4444;font-weight:600;">'
                'No record found</div>'
                '<div style="font-size:13px;color:#94A3B8;margin-top:4px;">'
                'Please check your reference number and try again, '
                'or contact the hospital reception desk.</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # ── STEP 2: Upload lab report (optional) ─────────────────
    st.markdown(
        '<div style="background:#111827;border:1px solid #1E2D40;'
        'border-radius:12px;padding:20px 24px;margin:20px 0;">'
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin-bottom:6px;">Step 2 — Upload Lab Report (Optional)</div>'
        '<div style="font-size:13px;color:#94A3B8;">'
        'If you have a digital copy of your lab report, upload it here '
        'for AI analysis.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        'Upload your lab report',
        type=['csv', 'pdf', 'png', 'jpg', 'jpeg'],
        key='patient_lab_upload',
        label_visibility='collapsed',
        help='Supported formats: CSV, PDF, Image'
    )
    if uploaded_file:
        st.success(f'✅  {uploaded_file.name} uploaded successfully')

    # ── STEP 3: Patient details + assign doctor ───────────────
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
        pat_gender   = st.selectbox('Gender',
                                    ['Male', 'Female', 'Other'],
                                    key='pat_gender')
        pat_symptoms = st.text_area('Symptoms / Reason for Visit',
                                    placeholder='Describe your symptoms...',
                                    height=120, key='pat_symptoms')

    # Doctor selection — filtered by test type
    st.markdown(
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin:20px 0 14px;">Step 4 — Select Your Doctor</div>',
        unsafe_allow_html=True
    )

    # Show only relevant doctors based on test type found
    relevant_mtype = found_type if found_type else \
                     (test_type if test_type != 'All Types' else None)

    doc_opts = {}
    for doc_id, doc in DOCTORS.items():
        if relevant_mtype is None or relevant_mtype in doc['sees']:
            doc_opts[f"{doc['name']} — {doc['dept']}"] = doc_id

    if not doc_opts:
        doc_opts = {f"{v['name']} — {v['dept']}": k
                    for k, v in DOCTORS.items()}

    doc_cols = st.columns(len(doc_opts))
    selected_doc = None

    for col, (label, doc_id) in zip(doc_cols, doc_opts.items()):
        doc = DOCTORS[doc_id]
        is_sel = st.session_state.get('selected_doc') == doc_id
        with col:
            st.markdown(
                f'<div style="background:{"rgba(59,130,246,0.1)" if is_sel else "#111827"};'
                f'border:{"2px solid #3B82F6" if is_sel else "1px solid #1E2D40"};'
                f'border-radius:10px;padding:14px;text-align:center;'
                f'margin-bottom:8px;">'
                f'<div style="font-size:20px;margin-bottom:6px;">🩺</div>'
                f'<div style="font-size:13px;font-weight:600;color:#F1F5F9;">'
                f'{doc["name"]}</div>'
                f'<div style="font-size:12px;color:#64748B;margin-top:3px;">'
                f'{doc["dept"]}</div>'
                f'<div style="font-size:11px;color:{doc["color"]};margin-top:4px;">'
                f'{", ".join(doc["sees"])}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button('Select', key=f'selDoc_{doc_id}',
                         use_container_width=True,
                         type='primary' if is_sel else 'secondary'):
                st.session_state['selected_doc'] = doc_id
                st.rerun()

    selected_doc = st.session_state.get('selected_doc')

    # Submit
    st.markdown('<br>', unsafe_allow_html=True)

    if found_row and selected_doc and pat_name and pat_phone:
        pid = found_row.get('_id', search_id.strip())
        already = pid in st.session_state.patients

        if already:
            assigned = st.session_state.patients[pid].get('doctor_name','')
            status   = st.session_state.patients[pid].get('status','PENDING')
            st.success(f'✅  Already submitted to {assigned}  ·  Status: {status}')
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
                st.success(
                    f'✅  Your case has been sent to {doc["name"]} for review.'
                )
                st.balloons()
                st.markdown(
                    f'<div style="background:rgba(16,185,129,0.08);'
                    f'border:1px solid rgba(16,185,129,0.2);'
                    f'border-radius:10px;padding:16px 20px;margin-top:12px;">'
                    f'<div style="font-size:15px;font-weight:600;color:#10B981;'
                    f'margin-bottom:6px;">Case submitted successfully</div>'
                    f'<div style="font-size:14px;color:#94A3B8;">'
                    f'Your reference number: '
                    f'<b style="color:#F1F5F9;font-family:monospace;">{pid}</b>'
                    f'<br>Doctor: <b style="color:#F1F5F9;">{doc["name"]}</b>'
                    f'<br>You will be notified once your doctor reviews the report.'
                    f'<br>No need to visit the hospital for routine results.</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    elif not found_row and not search_id:
        # Show dataset overview when nothing searched
        if loaded:
            st.markdown(section_title('Available Records'), unsafe_allow_html=True)
            oc = st.columns(len(loaded))
            icons = {'Lab Report':'🧪','CT Scan':'🧠',
                     'Ultrasound':'🔬','Combined Assessment':'⚡'}
            for col, (mtype, df) in zip(oc, loaded.items()):
                with col:
                    sev_counts = df['_sev'].value_counts()
                    severe_n   = sev_counts.get('Severe', 0)
                    st.markdown(
                        f'<div style="background:#111827;border:1px solid #1E2D40;'
                        f'border-radius:10px;padding:16px;text-align:center;">'
                        f'<div style="font-size:24px;margin-bottom:8px;">'
                        f'{icons.get(mtype,"📋")}</div>'
                        f'<div style="font-size:14px;font-weight:600;color:#F1F5F9;'
                        f'margin-bottom:4px;">{mtype}</div>'
                        f'<div style="font-size:22px;font-weight:700;color:#3B82F6;">'
                        f'{len(df):,}</div>'
                        f'<div style="font-size:12px;color:#64748B;">records</div>'
                        f'{"<div style=font-size:12px;color:#EF4444;margin-top:4px;>" + str(severe_n) + " severe</div>" if severe_n > 0 else ""}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
    elif not selected_doc and found_row:
        st.info('Please select a doctor above to proceed.')
    elif not pat_name or not pat_phone:
        if found_row:
            st.info('Please fill in your name and phone number to proceed.')


def show_findings(row, mtype):
    """Show clean clinical findings per modality."""

    if mtype == 'Lab Report':
        ckd = row.get('ckd_severity','')
        dia = row.get('diabetes_severity_final','')
        thy = row.get('thyroid_severity_final','')

        st.markdown(section_title('Your Lab Results'), unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        for col,(lbl,val) in zip([c1,c2,c3],[
            ('Kidney Function', ckd),
            ('Blood Sugar', dia),
            ('Thyroid Function', thy)
        ]):
            v = val if val and str(val) not in ['None','nan','NaN',''] \
                else 'Within normal range'
            with col:
                st.markdown(
                    f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                    f'border-radius:10px;padding:14px;">'
                    f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                    f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;">{v}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    elif mtype == 'CT Scan':
        cls  = row.get('ct_predicted_class','')
        conf = row.get('ct_confidence', 0)
        sev  = row.get('ct_severity_label','Unknown')
        clr  = SEV_COLORS.get(sev,'#94A3B8')
        diag = CT_NAMES.get(cls, cls)
        st.markdown(section_title('Your CT Scan Result'), unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:#0B1120;border:1px solid #1E2D40;'
            f'border-left:4px solid {clr};border-radius:10px;padding:16px 20px;">'
            f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
            f'margin-bottom:6px;">{diag}</div>'
            f'<div style="font-size:13px;color:{clr};">{sev}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Ultrasound':
        cls  = row.get('predicted_class','')
        conf = row.get('confidence', 0)
        sev  = row.get('us_severity_label','Unknown')
        clr  = SEV_COLORS.get(sev,'#94A3B8')
        diag = US_NAMES.get(cls, cls)
        st.markdown(section_title('Your Ultrasound Result'), unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:#0B1120;border:1px solid #1E2D40;'
            f'border-left:4px solid {clr};border-radius:10px;padding:16px 20px;">'
            f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
            f'margin-bottom:6px;">{diag}</div>'
            f'<div style="font-size:13px;color:{clr};">{sev}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Combined Assessment':
        st.markdown(section_title('Your Combined Assessment'), unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        for col,(lbl,key) in zip([c1,c2,c3],[
            ('Lab Result','lab_score'),
            ('CT Result','ct_score'),
            ('Ultrasound','us_score')
        ]):
            val = row.get(key)
            v   = SCORE_TO_LABEL.get(int(float(val)),'—') \
                  if val is not None and str(val) not in ['None','nan','NaN'] \
                  else '—'
            clr = SEV_COLORS.get(v,'#64748B')
            with col:
                st.markdown(
                    f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                    f'border-radius:10px;padding:14px;text-align:center;">'
                    f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                    f'<div style="font-size:18px;font-weight:700;color:{clr};">{v}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
