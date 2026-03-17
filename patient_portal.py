import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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
    'notumor':   'No Brain Tumour Detected',
    'pituitary': 'Pituitary Adenoma',
    'meningioma':'Meningioma',
    'glioma':    'Glioma'
}
US_DIAGNOSIS = {
    'Fetal abdomen':'Fetal Abdomen — Normal',
    'Fetal brain':  'Fetal Brain Plane',
    'Fetal femur':  'Fetal Femur — Normal Growth',
    'Fetal thorax': 'Fetal Thorax Plane'
}

# ── Data loaders ──────────────────────────────────────────────

@st.cache_data
def load_lab_data(uploaded=None):
    if uploaded:
        return pd.read_parquet(uploaded)
    return None

@st.cache_data
def load_ct_data(uploaded=None):
    if uploaded:
        return pd.read_csv(uploaded)
    return None

@st.cache_data
def load_us_data(uploaded=None):
    if uploaded:
        return pd.read_csv(uploaded)
    return None

@st.cache_data
def load_fusion_data(uploaded=None):
    if uploaded:
        return pd.read_parquet(uploaded)
    return None


def sev_pill(label):
    c = SEV_COLORS.get(label,'#94A3B8')
    b = SEV_BG.get(label,'rgba(148,163,184,0.12)')
    return (f'<span style="background:{b};border:1px solid {c}33;'
            f'color:{c};font-size:12px;font-weight:600;'
            f'padding:3px 12px;border-radius:20px;">{label}</span>')


def render():
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:26px;font-weight:700;color:#F1F5F9;
                    letter-spacing:-0.5px;margin-bottom:6px;">
            Patient Registration
        </div>
        <div style="font-size:15px;color:#94A3B8;">
            Upload your test data files to find and register your case
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── File upload section ───────────────────────────────────
    with st.expander('📂  Upload Test Result Files', expanded=True):
        st.markdown("""
        <div style="font-size:14px;color:#94A3B8;margin-bottom:16px;">
            Upload the output files from your AI models. 
            All files are from your Google Drive.
        </div>
        """, unsafe_allow_html=True)

        uc1,uc2,uc3,uc4 = st.columns(4)
        with uc1:
            lab_up = st.file_uploader(
                '🧪 Lab Report Data',
                type=['parquet'],
                key='lab_up',
                help='NB06_MULTIMODAL_SEVERITY_FUSION.parquet'
            )
        with uc2:
            ct_up = st.file_uploader(
                '🧠 CT Scan Data',
                type=['csv'],
                key='ct_up',
                help='CT_SEVERITY_FOR_FUSION.csv'
            )
        with uc3:
            us_up = st.file_uploader(
                '🔬 Ultrasound Data',
                type=['csv'],
                key='us_up',
                help='US_SEVERITY_FOR_FUSION.csv'
            )
        with uc4:
            fus_up = st.file_uploader(
                '⚡ Combined Assessment',
                type=['parquet'],
                key='fus_up',
                help='FINAL_MULTIMODAL_FUSION.parquet'
            )

        # Load uploaded files into session
        if lab_up and 'lab_df' not in st.session_state:
            df = pd.read_parquet(lab_up)
            df['modality_type']    = 'Lab Report'
            df['display_id']       = df['hadm_id'].astype(str)
            df['severity_label']   = df['final_severity_label']
            df['fusion_label']     = df['final_severity_label']
            st.session_state['lab_df'] = df
            st.success(f'✅  Lab data loaded — {len(df):,} patient records')

        if ct_up and 'ct_df' not in st.session_state:
            df = pd.read_csv(ct_up)
            df['modality_type']  = 'CT Scan'
            df['display_id']     = df['image_id'].astype(str)
            df['severity_label'] = df['ct_severity_label']
            df['fusion_label']   = df['ct_severity_label']
            st.session_state['ct_df'] = df
            st.success(f'✅  CT data loaded — {len(df):,} scan records')

        if us_up and 'us_df' not in st.session_state:
            df = pd.read_csv(us_up)
            df['modality_type']  = 'Ultrasound'
            df['display_id']     = df['patient_id'].astype(str)
            df['severity_label'] = df['us_severity_label']
            df['fusion_label']   = df['us_severity_label']
            st.session_state['us_df'] = df
            st.success(f'✅  Ultrasound data loaded — {len(df):,} scan records')

        if fus_up and 'fus_df' not in st.session_state:
            df = pd.read_parquet(fus_up)
            df['modality_type'] = 'Combined Assessment'
            df['display_id']    = df['case_id'].astype(str)
            df['severity_label']= df['fusion_label']
            st.session_state['fus_df'] = df
            # Filter multi-modality only
            multi = df[df['modalities_available'] >= 2]
            st.success(
                f'✅  Combined data loaded — {len(df):,} cases '
                f'({len(multi):,} with multiple tests)'
            )

    # ── 4 tabs with real data ─────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        '🧪  Lab Report Patients',
        '🧠  CT Scan Patients',
        '🔬  Ultrasound Patients',
        '⚡  Combined Assessment'
    ])

    with tab1:
        render_patient_list(
            df_key        = 'lab_df',
            tab_key       = 'lab',
            title         = 'Lab Report Patients',
            subtitle      = 'Patients with chronic disease assessment — kidney, diabetes, thyroid',
            id_col        = 'hadm_id',
            sev_col       = 'final_severity_label',
            modality_type = 'Lab Report',
            empty_msg     = 'Upload NB06_MULTIMODAL_SEVERITY_FUSION.parquet to view lab patients'
        )

    with tab2:
        render_patient_list(
            df_key        = 'ct_df',
            tab_key       = 'ct',
            title         = 'CT Scan Patients',
            subtitle      = 'Brain CT scans — EfficientNet-B0 tumour classification',
            id_col        = 'image_id',
            sev_col       = 'ct_severity_label',
            modality_type = 'CT Scan',
            empty_msg     = 'Upload CT_SEVERITY_FOR_FUSION.csv to view CT patients'
        )

    with tab3:
        render_patient_list(
            df_key        = 'us_df',
            tab_key       = 'us',
            title         = 'Ultrasound Patients',
            subtitle      = 'Fetal ultrasound — DenseNet121 plane classification',
            id_col        = 'patient_id',
            sev_col       = 'us_severity_label',
            modality_type = 'Ultrasound',
            empty_msg     = 'Upload US_SEVERITY_FOR_FUSION.csv to view ultrasound patients'
        )

    with tab4:
        render_patient_list(
            df_key        = 'fus_df',
            tab_key       = 'fus',
            title         = 'Combined Assessment Patients',
            subtitle      = 'Patients with results from multiple tests — multimodal fusion score',
            id_col        = 'case_id',
            sev_col       = 'fusion_label',
            modality_type = 'Combined Assessment',
            empty_msg     = 'Upload FINAL_MULTIMODAL_FUSION.parquet to view combined cases',
            multi_only    = True
        )


def render_patient_list(df_key, tab_key, title, subtitle,
                        id_col, sev_col, modality_type,
                        empty_msg, multi_only=False):

    st.markdown(f"""
    <div style="padding:16px 0 12px;">
        <div style="font-size:18px;font-weight:600;color:#F1F5F9;
                    margin-bottom:4px;">{title}</div>
        <div style="font-size:14px;color:#94A3B8;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

    if df_key not in st.session_state:
        st.markdown(f"""
        <div style="background:#111827;border:2px dashed #1E2D40;
                    border-radius:12px;padding:48px;text-align:center;">
            <div style="font-size:32px;margin-bottom:12px;">📂</div>
            <div style="font-size:15px;color:#64748B;">{empty_msg}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    df = st.session_state[df_key].copy()

    # Multi-modality filter
    if multi_only and 'modalities_available' in df.columns:
        df = df[df['modalities_available'] >= 2].copy()
        if df.empty:
            st.info('No patients with multiple test types found in this dataset.')
            return

    # Severity distribution mini stats
    sev_order = ['Severe','Moderate','Mild','Normal','Unknown']
    counts    = df[sev_col].value_counts()
    total     = len(df)

    cols = st.columns(5)
    for col, sev in zip(cols, sev_order):
        cnt = counts.get(sev, 0)
        pct = round(100*cnt/total, 1) if total > 0 else 0
        clr = SEV_COLORS.get(sev,'#94A3B8')
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-top:3px solid {clr};border-radius:10px;
                        padding:14px 16px;text-align:center;margin-bottom:16px;">
                <div style="font-size:24px;font-weight:700;color:{clr};">
                    {cnt:,}
                </div>
                <div style="font-size:13px;color:#64748B;margin-top:2px;">
                    {sev}
                </div>
                <div style="font-size:11px;color:#334155;margin-top:2px;">
                    {pct}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Search + filter
    fc1, fc2 = st.columns([3,1])
    with fc1:
        search = st.text_input(
            'Search',
            placeholder=f'Search by ID...',
            key=f'{tab_key}_search',
            label_visibility='collapsed'
        )
    with fc2:
        sev_filter = st.selectbox(
            'Filter',
            ['All Patients','Severe','Moderate','Mild','Normal'],
            key=f'{tab_key}_sev_filter',
            label_visibility='collapsed'
        )

    filt = df.copy()
    if search:
        filt = filt[filt[id_col].astype(str)
                    .str.contains(search, case=False, na=False)]
    if sev_filter != 'All Patients':
        filt = filt[filt[sev_col] == sev_filter]

    # Sort severe first
    order_map = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
    filt = filt.sort_values(sev_col, key=lambda x: x.map(order_map))

    st.markdown(f"""
    <div style="font-size:13px;color:#64748B;margin-bottom:12px;">
        Showing <b style="color:#F1F5F9;">{min(len(filt),50):,}</b> of
        <b style="color:#F1F5F9;">{len(filt):,}</b> records
    </div>
    """, unsafe_allow_html=True)

    if filt.empty:
        st.warning('No records match your search.')
        return

    # Patient dropdown — stays selected
    def make_label(row):
        done = '✓ ' if str(row[id_col]) in st.session_state.patients else ''
        sev  = row.get(sev_col,'Unknown')
        return f"{done}{row[id_col]}  ·  {sev}"

    options = filt[id_col].astype(str).tolist()[:50]
    labels  = [make_label(filt[filt[id_col].astype(str)==c].iloc[0])
               for c in options]

    chosen_label = st.selectbox(
        'Select a patient record',
        labels,
        key=f'{tab_key}_select'
    )
    chosen_idx = labels.index(chosen_label)
    chosen_id  = options[chosen_idx]
    row = filt[filt[id_col].astype(str)==chosen_id].iloc[0].to_dict()

    # ── Patient detail card ───────────────────────────────────
    sev   = row.get(sev_col,'Unknown')
    clr   = SEV_COLORS.get(sev,'#94A3B8')
    bg    = SEV_BG.get(sev,'rgba(148,163,184,0.12)')

    st.markdown(f"""
    <div style="background:#111827;border:2px solid {clr}33;
                border-left:4px solid {clr};border-radius:12px;
                padding:20px 24px;margin:12px 0 16px;">
        <div style="display:flex;justify-content:space-between;
                    align-items:flex-start;">
            <div>
                <div style="font-size:13px;color:#64748B;
                            font-family:'JetBrains Mono',monospace;
                            margin-bottom:4px;">CASE REFERENCE</div>
                <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                            font-family:'JetBrains Mono',monospace;">
                    {chosen_id}
                </div>
                <div style="font-size:13px;color:#64748B;margin-top:4px;">
                    {modality_type}
                </div>
            </div>
            <div style="background:{bg};border:1px solid {clr}44;
                        border-radius:10px;padding:12px 20px;
                        text-align:center;min-width:140px;">
                <div style="font-size:12px;color:{clr};font-weight:600;
                            text-transform:uppercase;letter-spacing:0.08em;
                            margin-bottom:4px;">Overall Status</div>
                <div style="font-size:22px;font-weight:700;color:{clr};">
                    {sev}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show relevant findings per modality
    render_findings(row, tab_key, sev_col)

    # Assign to doctor
    st.markdown("""
    <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                margin:20px 0 12px;">Assign to Doctor</div>
    """, unsafe_allow_html=True)

    ac1, ac2, ac3 = st.columns([2,1,1])
    with ac1:
        docs    = st.session_state.doctors
        doc_opts= {f"{v['name']} — {v['specialty']}": k
                   for k,v in docs.items()}
        sel_lbl = st.selectbox('Doctor', list(doc_opts.keys()),
                               key=f'{tab_key}_doc',
                               label_visibility='collapsed')
        sel_doc = doc_opts[sel_lbl]
    with ac2:
        pat_name = st.text_input('Patient Name',
                                 placeholder='Full name (optional)',
                                 key=f'{tab_key}_name',
                                 label_visibility='collapsed')
    with ac3:
        pat_phone = st.text_input('Phone',
                                  placeholder='Phone number',
                                  key=f'{tab_key}_phone',
                                  label_visibility='collapsed')

    symptoms = st.text_area(
        'Reason for Visit',
        placeholder='Describe symptoms or reason for this test...',
        height=70, key=f'{tab_key}_symptoms',
        label_visibility='collapsed'
    )

    already = chosen_id in st.session_state.patients
    if already:
        doc_name = st.session_state.patients[chosen_id].get('doctor_name','')
        status   = st.session_state.patients[chosen_id].get('status','PENDING')
        st.success(f'✅  Already assigned to {doc_name} · Status: {status}')
        if st.button('Open Doctor Dashboard →',
                     key=f'{tab_key}_goto_doc',
                     use_container_width=True,
                     type='primary'):
            st.session_state.current_patient = chosen_id
            st.session_state.page = 'doctor'
            st.rerun()
    else:
        if st.button('Send to Doctor for Review',
                     key=f'{tab_key}_submit',
                     use_container_width=True,
                     type='primary'):
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
                'modality_type': modality_type,
                'severity_label':sev,
                'fusion_label':  sev,
                'registered_at': datetime.now().isoformat(),
            }
            st.success(
                f'✅  Case {chosen_id} sent to '
                f'{docs[sel_doc]["name"]} for review.'
            )
            st.balloons()
            if st.button('Open Doctor Dashboard →',
                         key=f'{tab_key}_after_submit',
                         use_container_width=True):
                st.session_state.current_patient = chosen_id
                st.session_state.page = 'doctor'
                st.rerun()


def render_findings(row, tab_key, sev_col):
    """Show relevant clinical findings based on modality."""

    mtype = row.get('modality_type','')

    # Lab findings
    if mtype == 'Lab Report' or 'final_severity_label' in row:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin:16px 0 12px;">Lab Findings</div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        findings = [
            ('Kidney Function', row.get('ckd_severity','Not tested'),
             row.get('ckd_score')),
            ('Blood Sugar', row.get('diabetes_severity_final','Not tested'),
             row.get('diabetes_score')),
            ('Thyroid', row.get('thyroid_severity_final','Not tested'),
             row.get('thyroid_score')),
        ]
        for col,(lbl,val,score) in zip([c1,c2,c3],findings):
            with col:
                v   = val if val and str(val) not in ['None','nan','NaN'] else 'Not tested'
                clr = '#10B981' if v in ['None','Not tested','Normal'] else '#F59E0B'
                st.markdown(f"""
                <div style="background:#0B1120;border:1px solid #1E2D40;
                            border-radius:10px;padding:16px;">
                    <div style="font-size:12px;color:#64748B;
                                text-transform:uppercase;letter-spacing:0.06em;
                                margin-bottom:6px;">{lbl}</div>
                    <div style="font-size:16px;font-weight:600;color:#F1F5F9;">
                        {v}</div>
                </div>
                """, unsafe_allow_html=True)

    # CT findings
    if mtype == 'CT Scan' or 'ct_predicted_class' in row:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin:16px 0 12px;">CT Scan Findings</div>
        """, unsafe_allow_html=True)

        ct_cls  = row.get('ct_predicted_class','')
        ct_conf = row.get('ct_confidence', 0)
        ct_sev  = row.get('ct_severity_label','Unknown')
        ct_clr  = SEV_COLORS.get(ct_sev,'#94A3B8')
        diag    = CT_DIAGNOSIS.get(ct_cls, ct_cls)

        c1,c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-left:4px solid {ct_clr};
                        border-radius:10px;padding:16px;">
                <div style="font-size:12px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:6px;">Diagnosis</div>
                <div style="font-size:16px;font-weight:600;color:#F1F5F9;">
                    {diag}</div>
                <div style="font-size:13px;color:{ct_clr};margin-top:4px;">
                    {ct_sev}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-radius:10px;padding:16px;">
                <div style="font-size:12px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:6px;">AI Confidence</div>
                <div style="font-size:24px;font-weight:700;color:#F1F5F9;">
                    {float(ct_conf):.1%}</div>
                <div style="font-size:12px;color:#64748B;margin-top:4px;">
                    EfficientNet-B0 model</div>
            </div>
            """, unsafe_allow_html=True)

    # US findings
    if mtype == 'Ultrasound' or 'predicted_class' in row:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin:16px 0 12px;">Ultrasound Findings</div>
        """, unsafe_allow_html=True)

        us_cls  = row.get('predicted_class', row.get('us_predicted_class',''))
        us_conf = row.get('confidence', row.get('us_confidence',0))
        us_sev  = row.get('us_severity_label','Unknown')
        us_clr  = SEV_COLORS.get(us_sev,'#94A3B8')
        diag    = US_DIAGNOSIS.get(us_cls, us_cls)

        c1,c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-left:4px solid {us_clr};
                        border-radius:10px;padding:16px;">
                <div style="font-size:12px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:6px;">Scan Result</div>
                <div style="font-size:16px;font-weight:600;color:#F1F5F9;">
                    {diag}</div>
                <div style="font-size:13px;color:{us_clr};margin-top:4px;">
                    {us_sev}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:#0B1120;border:1px solid #1E2D40;
                        border-radius:10px;padding:16px;">
                <div style="font-size:12px;color:#64748B;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:6px;">AI Confidence</div>
                <div style="font-size:24px;font-weight:700;color:#F1F5F9;">
                    {float(us_conf):.1%}</div>
                <div style="font-size:12px;color:#64748B;margin-top:4px;">
                    DenseNet121 model</div>
            </div>
            """, unsafe_allow_html=True)

    # Fusion / Combined
    if mtype == 'Combined Assessment' or 'fusion_score' in row:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin:16px 0 12px;">Combined Assessment</div>
        """, unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        for col,(lbl,key) in zip([c1,c2,c3],[
            ('Lab Score','lab_score'),
            ('CT Score','ct_score'),
            ('Ultrasound Score','us_score')
        ]):
            with col:
                val = row.get(key)
                v   = str(int(val)) if val is not None and pd.notna(val) else '—'
                from pandas import isna
                sev = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}.get(
                    int(val) if val is not None and not isna(val) else -1,
                    'Not available'
                )
                clr = SEV_COLORS.get(sev,'#64748B')
                st.markdown(f"""
                <div style="background:#0B1120;border:1px solid #1E2D40;
                            border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:12px;color:#64748B;
                                text-transform:uppercase;letter-spacing:0.06em;
                                margin-bottom:6px;">{lbl}</div>
                    <div style="font-size:28px;font-weight:700;color:#F1F5F9;">
                        {v}</div>
                    <div style="font-size:13px;color:{clr};margin-top:4px;">
                        {sev}</div>
                </div>
                """, unsafe_allow_html=True)
