import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

SEV_COLORS  = {'Normal':'#10B981','Mild':'#F59E0B','Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'}
SEV_BG      = {'Normal':'rgba(16,185,129,0.1)','Mild':'rgba(245,158,11,0.1)','Moderate':'rgba(249,115,22,0.1)','Severe':'rgba(239,68,68,0.1)','Unknown':'rgba(148,163,184,0.1)'}
CT_NAMES    = {'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}
US_NAMES    = {'Fetal abdomen':'Fetal Abdomen — Normal','Fetal brain':'Fetal Brain Plane','Fetal femur':'Fetal Femur — Normal Growth','Fetal thorax':'Fetal Thorax Plane'}

# Google Drive paths — exact paths from your Drive
DRIVE_PATHS = {
    'lab':    '/content/drive/MyDrive/MIMIC_DOCTOR_IN_LOOP_PROJECT/checkpoints/NB06_MULTIMODAL_SEVERITY_FUSION.parquet',
    'ct':     '/content/drive/MyDrive/Medical_AI_Project/ct_module/results/CT_SEVERITY_FOR_FUSION.csv',
    'us':     '/content/drive/MyDrive/Medical_AI_Project/ultrasound_module/results/US_SEVERITY_FOR_FUSION.csv',
    'fusion': '/content/drive/MyDrive/Medical_AI_Project/fusion_output/FINAL_MULTIMODAL_FUSION.parquet',
}


@st.cache_data
def load_lab():
    path = DRIVE_PATHS['lab']
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df['_display_id'] = df['hadm_id'].astype(str)
        df['_sev']        = df['final_severity_label'].fillna('Unknown')
        df['_mtype']      = 'Lab Report'
        return df
    return None


@st.cache_data
def load_ct():
    path = DRIVE_PATHS['ct']
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['_display_id'] = df['image_id'].astype(str)
        df['_sev']        = df['ct_severity_label'].fillna('Unknown')
        df['_mtype']      = 'CT Scan'
        return df
    return None


@st.cache_data
def load_us():
    path = DRIVE_PATHS['us']
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['_display_id'] = df['patient_id'].astype(str)
        df['_sev']        = df['us_severity_label'].fillna('Unknown')
        df['_mtype']      = 'Ultrasound'
        return df
    return None


@st.cache_data
def load_fusion():
    path = DRIVE_PATHS['fusion']
    if os.path.exists(path):
        df = pd.read_parquet(path)
        df['_display_id'] = df['case_id'].astype(str)
        df['_sev']        = df['fusion_label'].fillna('Unknown')
        df['_mtype']      = 'Combined Assessment'
        return df
    return None


def sev_badge(label):
    c = SEV_COLORS.get(label,'#94A3B8')
    b = SEV_BG.get(label,'rgba(148,163,184,0.1)')
    return (f'<span style="background:{b};border:1px solid {c}55;color:{c};'
            f'font-size:13px;font-weight:600;padding:4px 14px;'
            f'border-radius:20px;">{label}</span>')


def stat_card(title, val, color):
    return (
        f'<div style="background:#111827;border:1px solid #1E2D40;'
        f'border-top:3px solid {color};border-radius:10px;'
        f'padding:14px 16px;text-align:center;">'
        f'<div style="font-size:26px;font-weight:700;color:{color};">{val:,}</div>'
        f'<div style="font-size:13px;color:#64748B;margin-top:3px;">{title}</div>'
        f'</div>'
    )


def render():
    st.markdown(
        '<div style="font-size:26px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;margin-bottom:6px;">Patient Registration</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:20px;">'
        'Select a patient from your AI model output and assign to a doctor</div>',
        unsafe_allow_html=True
    )

    # Load data — from Drive if running in Colab, else show upload
    lab_df    = load_lab()
    ct_df     = load_ct()
    us_df     = load_us()
    fusion_df = load_fusion()

    drive_loaded = any(df is not None for df in [lab_df, ct_df, us_df, fusion_df])

    # Upload fallback (for Streamlit Cloud where Drive isn't mounted)
    if not drive_loaded:
        st.markdown(
            '<div style="background:#111827;border:1px solid #1E2D40;'
            'border-radius:12px;padding:20px 24px;margin-bottom:20px;">'
            '<div style="font-size:15px;font-weight:600;color:#F1F5F9;margin-bottom:6px;">'
            '📂 Upload Your Model Output Files</div>'
            '<div style="font-size:13px;color:#94A3B8;margin-bottom:16px;">'
            'Download these files from Google Drive and upload here.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        uc1,uc2,uc3,uc4 = st.columns(4)
        with uc1:
            f1 = st.file_uploader('🧪 Lab Report',    type=['parquet'], key='up_lab',
                                  help='NB06_MULTIMODAL_SEVERITY_FUSION.parquet')
        with uc2:
            f2 = st.file_uploader('🧠 CT Scan',        type=['csv'],     key='up_ct',
                                  help='CT_SEVERITY_FOR_FUSION.csv')
        with uc3:
            f3 = st.file_uploader('🔬 Ultrasound',     type=['csv'],     key='up_us',
                                  help='US_SEVERITY_FOR_FUSION.csv')
        with uc4:
            f4 = st.file_uploader('⚡ Combined',       type=['parquet'], key='up_fus',
                                  help='FINAL_MULTIMODAL_FUSION.parquet')

        if f1:
            df = pd.read_parquet(f1)
            df['_display_id'] = df['hadm_id'].astype(str)
            df['_sev']        = df['final_severity_label'].fillna('Unknown')
            df['_mtype']      = 'Lab Report'
            lab_df = df
        if f2:
            df = pd.read_csv(f2)
            df['_display_id'] = df['image_id'].astype(str)
            df['_sev']        = df['ct_severity_label'].fillna('Unknown')
            df['_mtype']      = 'CT Scan'
            ct_df = df
        if f3:
            df = pd.read_csv(f3)
            df['_display_id'] = df['patient_id'].astype(str)
            df['_sev']        = df['us_severity_label'].fillna('Unknown')
            df['_mtype']      = 'Ultrasound'
            us_df = df
        if f4:
            df = pd.read_parquet(f4)
            df['_display_id'] = df['case_id'].astype(str)
            df['_sev']        = df['fusion_label'].fillna('Unknown')
            df['_mtype']      = 'Combined Assessment'
            fusion_df = df

    # 4 tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        '🧪  Lab Report Patients',
        '🧠  CT Scan Patients',
        '🔬  Ultrasound Patients',
        '⚡  Combined Assessment',
    ])

    configs = [
        (tab1, lab_df,    'Lab Report',
         'Chronic disease assessment — kidney function, diabetes, thyroid',
         'NB06_MULTIMODAL_SEVERITY_FUSION.parquet'),
        (tab2, ct_df,     'CT Scan',
         'Brain CT scans — EfficientNet-B0 tumour classification',
         'CT_SEVERITY_FOR_FUSION.csv'),
        (tab3, us_df,     'Ultrasound',
         'Fetal ultrasound — DenseNet121 classification',
         'US_SEVERITY_FOR_FUSION.csv'),
        (tab4, fusion_df, 'Combined Assessment',
         'Patients assessed across multiple test types',
         'FINAL_MULTIMODAL_FUSION.parquet'),
    ]

    for tab, df, mtype, subtitle, fname in configs:
        with tab:
            render_tab(df, mtype, subtitle, fname)


def render_tab(df, mtype, subtitle, fname):
    st.markdown(
        f'<div style="padding:14px 0 10px;">'
        f'<div style="font-size:18px;font-weight:600;color:#F1F5F9;margin-bottom:4px;">'
        f'{mtype} Patients</div>'
        f'<div style="font-size:14px;color:#94A3B8;">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if df is None:
        st.markdown(
            '<div style="background:#111827;border:2px dashed #1E2D40;'
            'border-radius:12px;padding:56px;text-align:center;">'
            '<div style="font-size:32px;margin-bottom:12px;">📂</div>'
            f'<div style="font-size:15px;color:#F1F5F9;margin-bottom:6px;">'
            f'Upload <code>{fname}</code></div>'
            '<div style="font-size:13px;color:#64748B;">'
            'Download from Google Drive and upload above</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # For fusion tab — only show multi-modality cases
    if mtype == 'Combined Assessment' and 'modalities_available' in df.columns:
        df = df[df['modalities_available'] >= 2].copy()

    if df.empty:
        st.info('No records found.')
        return

    # Severity stats
    sev_order = ['Severe','Moderate','Mild','Normal','Unknown']
    counts    = df['_sev'].value_counts()
    total     = len(df)

    sc = st.columns(5)
    colors = ['#EF4444','#F97316','#F59E0B','#10B981','#94A3B8']
    for col, (sev, clr) in zip(sc, zip(sev_order, colors)):
        cnt = int(counts.get(sev, 0))
        pct = round(100*cnt/total, 1) if total > 0 else 0
        with col:
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-top:3px solid {clr};border-radius:10px;'
                f'padding:12px 14px;text-align:center;margin-bottom:14px;">'
                f'<div style="font-size:22px;font-weight:700;color:{clr};">{cnt:,}</div>'
                f'<div style="font-size:12px;color:#64748B;margin-top:2px;">{sev}</div>'
                f'<div style="font-size:11px;color:#334155;">{pct}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Search + filter
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        search = st.text_input(
            'Search',
            placeholder='Search by patient ID...',
            key=f'search_{mtype}',
            label_visibility='collapsed'
        )
    with fc2:
        sev_f = st.selectbox(
            'Filter by severity',
            ['All', 'Severe', 'Moderate', 'Mild', 'Normal'],
            key=f'sev_{mtype}',
            label_visibility='collapsed'
        )

    filt = df.copy()
    if search:
        filt = filt[filt['_display_id'].str.contains(search, case=False, na=False)]
    if sev_f != 'All':
        filt = filt[filt['_sev'] == sev_f]

    # Sort severe first
    order = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
    filt  = filt.sort_values('_sev', key=lambda x: x.map(order))
    filt  = filt.head(100)  # limit for performance

    if filt.empty:
        st.warning('No records match your search.')
        return

    st.markdown(
        f'<div style="font-size:13px;color:#64748B;margin-bottom:10px;">'
        f'Showing <b style="color:#F1F5F9;">{len(filt):,}</b> records · '
        f'Total: <b style="color:#F1F5F9;">{total:,}</b></div>',
        unsafe_allow_html=True
    )

    # Dropdown — uses real patient IDs from dataset
    ids    = filt['_display_id'].tolist()
    sevs   = filt['_sev'].tolist()
    labels = []
    for pid, sev in zip(ids, sevs):
        done  = '✓  ' if pid in st.session_state.patients else ''
        labels.append(f'{done}{pid}   ·   {sev}')

    chosen_label = st.selectbox(
        f'Select {mtype} Patient',
        labels,
        key=f'sel_{mtype}'
    )
    chosen_idx = labels.index(chosen_label)
    chosen_id  = ids[chosen_idx]
    row        = filt[filt['_display_id'] == chosen_id].iloc[0].to_dict()
    sev        = row.get('_sev', 'Unknown')
    clr        = SEV_COLORS.get(sev, '#94A3B8')
    bg         = SEV_BG.get(sev, 'rgba(148,163,184,0.1)')

    # Patient detail card
    st.markdown(
        f'<div style="background:#111827;border:2px solid {clr}44;'
        f'border-left:5px solid {clr};border-radius:12px;'
        f'padding:20px 24px;margin:12px 0 16px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<div style="font-size:12px;color:#64748B;font-family:monospace;margin-bottom:4px;">PATIENT ID</div>'
        f'<div style="font-size:22px;font-weight:700;color:#F1F5F9;font-family:monospace;">{chosen_id}</div>'
        f'<div style="font-size:13px;color:#64748B;margin-top:4px;">{mtype}</div>'
        f'</div>'
        f'<div style="background:{bg};border:1px solid {clr}55;border-radius:10px;'
        f'padding:12px 20px;text-align:center;">'
        f'<div style="font-size:12px;color:{clr};font-weight:600;margin-bottom:4px;">OVERALL STATUS</div>'
        f'<div style="font-size:20px;font-weight:700;color:{clr};">{sev}</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Show findings based on modality
    show_findings(row, mtype)

    # Assign to doctor
    st.markdown(
        '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
        'margin:20px 0 12px;">Assign to Doctor</div>',
        unsafe_allow_html=True
    )

    ac1, ac2, ac3 = st.columns([2, 1, 1])
    with ac1:
        docs    = st.session_state.doctors
        doc_opts= {f"{v['name']} — {v['specialty']}": k for k,v in docs.items()}
        sel_lbl = st.selectbox('Doctor', list(doc_opts.keys()),
                               key=f'doc_{mtype}', label_visibility='collapsed')
        sel_doc = doc_opts[sel_lbl]
    with ac2:
        pat_name = st.text_input('Patient Name', placeholder='Full name (optional)',
                                 key=f'name_{mtype}', label_visibility='collapsed')
    with ac3:
        pat_phone = st.text_input('Phone', placeholder='+91 ...',
                                  key=f'phone_{mtype}', label_visibility='collapsed')

    symptoms = st.text_area('Reason for Visit',
                            placeholder='Describe symptoms or reason for this test...',
                            height=70, key=f'sym_{mtype}',
                            label_visibility='collapsed')

    already = chosen_id in st.session_state.patients
    if already:
        doc_n  = st.session_state.patients[chosen_id].get('doctor_name','')
        status = st.session_state.patients[chosen_id].get('status','PENDING')
        st.success(f'✅  Already assigned to {doc_n}  ·  Status: {status}')
        if st.button('Open Doctor Dashboard →', key=f'todoc_{mtype}',
                     use_container_width=True, type='primary'):
            st.session_state.current_patient = chosen_id
            st.session_state.page = 'doctor'
            st.rerun()
    else:
        if st.button('Send to Doctor for Review', key=f'submit_{mtype}',
                     use_container_width=True, type='primary'):
            st.session_state.patients[chosen_id] = {
                **row,
                'patient_id':    chosen_id,
                'case_id':       chosen_id,
                'name':          pat_name or f'Patient {chosen_id}',
                'phone':         pat_phone or 'Not provided',
                'symptoms':      symptoms,
                'doctor_id':     sel_doc,
                'doctor_name':   docs[sel_doc]['name'],
                'status':        'PENDING',
                'modality_type': mtype,
                'fusion_label':  sev,
                'severity_label':sev,
                'registered_at': datetime.now().isoformat(),
            }
            st.success(f'✅  Patient {chosen_id} sent to {docs[sel_doc]["name"]}!')
            st.balloons()
            if st.button('Open Doctor Dashboard →', key=f'todoc2_{mtype}',
                         use_container_width=True):
                st.session_state.current_patient = chosen_id
                st.session_state.page = 'doctor'
                st.rerun()


def show_findings(row, mtype):
    """Display clinical findings cleanly based on modality."""

    # Lab findings
    if mtype == 'Lab Report' or 'final_severity_label' in row:
        st.markdown(
            '<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
            'margin:14px 0 10px;">Lab Results</div>',
            unsafe_allow_html=True
        )
        cols = st.columns(3)
        items = [
            ('Kidney Function',   row.get('ckd_severity','')),
            ('Blood Sugar Level', row.get('diabetes_severity_final','')),
            ('Thyroid Function',  row.get('thyroid_severity_final','')),
        ]
        for col,(lbl,val) in zip(cols, items):
            v = val if val and str(val) not in ['None','nan','NaN',''] else 'Not tested'
            with col:
                st.markdown(
                    f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                    f'border-radius:10px;padding:14px 16px;">'
                    f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                    f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;">{v}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # CT findings
    if mtype == 'CT Scan' or 'ct_predicted_class' in row:
        ct_cls  = row.get('ct_predicted_class','')
        ct_conf = row.get('ct_confidence', 0)
        ct_sev  = row.get('ct_severity_label','Unknown')
        clr     = SEV_COLORS.get(ct_sev,'#94A3B8')
        diag    = CT_NAMES.get(ct_cls, ct_cls)
        st.markdown(
            '<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
            'margin:14px 0 10px;">CT Scan Result</div>',
            unsafe_allow_html=True
        )
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-left:4px solid {clr};border-radius:10px;padding:14px 16px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">Diagnosis</div>'
                f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;">{diag}</div>'
                f'<div style="font-size:13px;color:{clr};margin-top:4px;">{ct_sev}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-radius:10px;padding:14px 16px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">AI Confidence</div>'
                f'<div style="font-size:22px;font-weight:700;color:#F1F5F9;">'
                f'{float(ct_conf):.1%}</div>'
                f'<div style="font-size:12px;color:#64748B;margin-top:4px;">'
                f'EfficientNet-B0</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # US findings
    if mtype == 'Ultrasound' or 'predicted_class' in row:
        us_cls  = row.get('predicted_class', row.get('us_predicted_class',''))
        us_conf = row.get('confidence', row.get('us_confidence',0))
        us_sev  = row.get('us_severity_label','Unknown')
        clr     = SEV_COLORS.get(us_sev,'#94A3B8')
        diag    = US_NAMES.get(us_cls, us_cls)
        st.markdown(
            '<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
            'margin:14px 0 10px;">Ultrasound Result</div>',
            unsafe_allow_html=True
        )
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-left:4px solid {clr};border-radius:10px;padding:14px 16px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">Scan Result</div>'
                f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;">{diag}</div>'
                f'<div style="font-size:13px;color:{clr};margin-top:4px;">{us_sev}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                f'border-radius:10px;padding:14px 16px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">AI Confidence</div>'
                f'<div style="font-size:22px;font-weight:700;color:#F1F5F9;">'
                f'{float(us_conf):.1%}</div>'
                f'<div style="font-size:12px;color:#64748B;margin-top:4px;">'
                f'DenseNet121</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # Combined assessment
    if mtype == 'Combined Assessment' or 'fusion_score' in row:
        st.markdown(
            '<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
            'margin:14px 0 10px;">Combined Assessment</div>',
            unsafe_allow_html=True
        )
        sev_map = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
        c1,c2,c3 = st.columns(3)
        for col,(lbl,key) in zip([c1,c2,c3],[
            ('Lab Score','lab_score'),
            ('CT Score','ct_score'),
            ('Ultrasound Score','us_score')
        ]):
            val = row.get(key)
            v   = str(int(val)) if val is not None and pd.notna(val) else '—'
            sev = sev_map.get(int(val),'—') if val is not None and pd.notna(val) else '—'
            clr = SEV_COLORS.get(sev,'#64748B')
            with col:
                st.markdown(
                    f'<div style="background:#0B1120;border:1px solid #1E2D40;'
                    f'border-radius:10px;padding:14px;text-align:center;">'
                    f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                    f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                    f'<div style="font-size:26px;font-weight:700;color:#F1F5F9;">{v}</div>'
                    f'<div style="font-size:13px;color:{clr};margin-top:4px;">{sev}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
