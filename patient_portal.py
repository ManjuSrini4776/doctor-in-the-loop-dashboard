import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

SCORE_TO_LABEL = {0:'Normal', 1:'Mild', 2:'Moderate', 3:'Severe'}
SEV_COLORS = {
    'Normal':'#10B981','Mild':'#F59E0B',
    'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
}
CT_DESC = {
    'notumor':   'No tumor detected',   'pituitary': 'Pituitary adenoma',
    'meningioma':'Meningioma',           'glioma':    'Glioma (high-grade)'
}
US_DESC = {
    'Fetal abdomen':'Normal abdominal plane',
    'Fetal brain':  'Brain anomaly — urgent',
    'Fetal femur':  'Normal femur growth',
    'Fetal thorax': 'Thoracic assessment'
}


@st.cache_data
def build_sample_df():
    np.random.seed(42)
    n = 100
    ct_cls = ['notumor','pituitary','meningioma','glioma']
    us_cls = ['Fetal abdomen','Fetal brain','Fetal femur','Fetal thorax']
    ct_sev = {'notumor':0,'pituitary':1,'meningioma':2,'glioma':3}
    us_sev = {'Fetal abdomen':0,'Fetal femur':1,'Fetal thorax':2,'Fetal brain':3}
    rows = []
    for i in range(n):
        ct = np.random.choice(ct_cls, p=[0.40,0.20,0.25,0.15])
        us = np.random.choice(us_cls)
        lab= int(np.random.choice([0,1,2,3], p=[0.35,0.30,0.20,0.15]))
        ct_s=ct_sev[ct]; us_s=us_sev[us]; fus=max(lab,ct_s,us_s)
        rows.append({
            'case_id':f'CASE-{1000+i:04d}',
            'lab_score':lab, 'lab_severity_label':SCORE_TO_LABEL[lab],
            'ckd_severity':np.random.choice(['G1 (Normal/High)','G2 (Mild)','G3a','G3b','G4 (Severe)']),
            'diabetes_severity_final':np.random.choice(['Normal','Mild','Moderate','Severe','Unknown']),
            'thyroid_severity_final':np.random.choice(['Normal','Hypothyroid','Hyperthyroid','Unknown']),
            'ct_score':ct_s, 'ct_severity_label':SCORE_TO_LABEL[ct_s],
            'ct_predicted_class':ct,
            'ct_confidence':round(float(np.random.uniform(0.75,0.99)),3),
            'us_score':us_s, 'us_severity_label':SCORE_TO_LABEL[us_s],
            'us_predicted_class':us,
            'us_confidence':round(float(np.random.uniform(0.80,0.99)),3),
            'fusion_score':fus, 'fusion_label':SCORE_TO_LABEL[fus],
            'modalities_available':3,
        })
    return pd.DataFrame(rows)


def render():

    # ── Back button ───────────────────────────────────────────
    if st.button('← Back to Home', key='pat_back'):
        st.session_state.page = 'home'
        st.rerun()

    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;
                border-radius:12px;padding:20px 28px;margin:12px 0 20px;">
        <div style="font-family:'Playfair Display',serif;
                    font-size:20px;color:#F0F4FF;">👤 Patient Portal</div>
        <div style="font-size:12px;color:#64748B;margin-top:4px;
                    font-family:'IBM Plex Mono',monospace;">
            Select patient from dataset → Assign doctor → Auto-route for AI review
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Dataset loader ────────────────────────────────────────
    with st.expander('📂 Load Your Fusion Dataset', expanded=False):
        st.caption('Upload FINAL_MULTIMODAL_FUSION.parquet from NB08. '
                   'Sample data used if not uploaded.')
        up = st.file_uploader('Upload', type=['parquet','csv'],
                              key='fusion_up', label_visibility='collapsed')
        if up:
            try:
                df_up = (pd.read_parquet(up)
                         if up.name.endswith('.parquet')
                         else pd.read_csv(up))
                st.session_state['fusion_df'] = df_up
                st.success(f'Loaded {len(df_up):,} patients from your dataset!')
            except Exception as e:
                st.error(f'Error loading file: {e}')

    if 'fusion_df' not in st.session_state:
        st.session_state['fusion_df'] = build_sample_df()
    df = st.session_state['fusion_df']

    tab1, tab2 = st.tabs(['🔍 Select & Submit Patient', '📊 Track Submissions'])

    # ── Tab 1: Select patient ─────────────────────────────────
    with tab1:

        # Search & filter
        fc1, fc2, fc3 = st.columns([2,1,1])
        with fc1:
            search = st.text_input('Search Case ID',
                                   placeholder='e.g. CASE-1001',
                                   label_visibility='collapsed')
        with fc2:
            sev_f = st.selectbox('Severity',
                                 ['All','Severe','Moderate','Mild','Normal'],
                                 label_visibility='collapsed')
        with fc3:
            sort_sev = st.checkbox('Sort: Severe first', value=True)

        # Filter
        filt = df.copy()
        if search:
            filt = filt[filt['case_id'].astype(str).str.contains(
                search, case=False, na=False)]
        if sev_f != 'All':
            filt = filt[filt['fusion_label'] == sev_f]
        if sort_sev:
            order = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
            filt  = filt.sort_values(
                'fusion_label', key=lambda x: x.map(order)
            )

        st.caption(f'Showing {len(filt):,} of {len(df):,} patients')

        # Patient list
        for _, row in filt.head(25).iterrows():
            cid   = str(row['case_id'])
            fus   = row.get('fusion_label','Unknown')
            color = SEV_COLORS.get(fus,'#94A3B8')
            done  = cid in st.session_state.patients

            rc1, rc2 = st.columns([1,5])
            with rc1:
                label = '✅ Selected' if done else 'Select →'
                if st.button(label, key=f'sel_{cid}',
                             use_container_width=True):
                    st.session_state['portal_selected'] = row.to_dict()
                    st.rerun()
            with rc2:
                ct = row.get('ct_predicted_class','')
                us = row.get('us_predicted_class','')
                st.markdown(f"""
                <div style="background:#0D1621;border:1px solid #1E293B;
                            border-left:3px solid {color};
                            border-radius:6px;padding:8px 14px;
                            display:flex;align-items:center;gap:14px;">
                    <span style="font-family:'IBM Plex Mono',monospace;
                                 font-size:13px;color:#F0F4FF;
                                 min-width:110px;">{cid}</span>
                    <span style="border:1px solid {color};color:{color};
                                 font-size:11px;padding:1px 9px;
                                 border-radius:20px;">{fus}</span>
                    <span style="font-size:11px;color:#64748B;">
                        Lab:{row.get('lab_score','—')} &nbsp;
                        CT:{CT_DESC.get(ct,ct)[:20]} &nbsp;
                        US:{us[:18] if us else '—'}
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # ── Selected patient detail ───────────────────────────
        if 'portal_selected' in st.session_state:
            p     = st.session_state['portal_selected']
            cid   = str(p.get('case_id',''))
            fus   = p.get('fusion_label','Unknown')
            color = SEV_COLORS.get(fus,'#94A3B8')

            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                        color:#10B981;letter-spacing:.1em;text-transform:uppercase;
                        padding-bottom:8px;border-bottom:1px solid #1E293B;
                        margin-bottom:14px;">
                ── Selected: {cid}
            </div>
            """, unsafe_allow_html=True)

            # Score cards
            c1,c2,c3,c4 = st.columns(4)
            for col,(lbl,skey,sevkey) in zip(
                [c1,c2,c3,c4],
                [('🧪 Lab','lab_score','lab_severity_label'),
                 ('🧠 CT','ct_score','ct_severity_label'),
                 ('🔬 US','us_score','us_severity_label'),
                 ('⚡ Fusion','fusion_score','fusion_label')]
            ):
                with col:
                    sc  = p.get(skey)
                    sev = p.get(sevkey,'N/A')
                    clr = SEV_COLORS.get(sev,'#94A3B8')
                    val = str(int(sc)) if sc is not None and pd.notna(sc) else '—'
                    st.markdown(f"""
                    <div style="background:#0D1621;border:1px solid #1E293B;
                                border-left:3px solid {clr};border-radius:8px;
                                padding:12px 14px;text-align:center;">
                        <div style="font-size:10px;color:#64748B;">{lbl}</div>
                        <div style="font-size:22px;font-weight:600;
                                    color:#F0F4FF;">{val}</div>
                        <div style="font-size:11px;color:{clr};">{sev}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Lab breakdown
            st.markdown('<br>', unsafe_allow_html=True)
            d1,d2,d3 = st.columns(3)
            for col,(lbl,key) in zip([d1,d2,d3],[
                ('CKD','ckd_severity'),
                ('Diabetes','diabetes_severity_final'),
                ('Thyroid','thyroid_severity_final')
            ]):
                with col:
                    v = p.get(key,'N/A')
                    st.markdown(f"""
                    <div style="background:#0D1621;border:1px solid #1E293B;
                                border-radius:6px;padding:10px 14px;">
                        <div style="font-size:10px;color:#64748B;">{lbl}</div>
                        <div style="font-size:12px;color:#F0F4FF;">
                            {v if v and str(v)!='nan' else 'N/A'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # CT + US
            st.markdown('<br>', unsafe_allow_html=True)
            ct_col, us_col = st.columns(2)
            with ct_col:
                ct  = p.get('ct_predicted_class','')
                st.markdown(f"""
                <div style="background:#0D1621;border:1px solid #1E293B;
                            border-radius:8px;padding:14px;">
                    <div style="font-size:10px;color:#64748B;
                                font-family:'IBM Plex Mono',monospace;">
                        🧠 CT SCAN</div>
                    <div style="font-size:13px;color:#F0F4FF;
                                font-weight:500;margin-top:4px;">
                        {CT_DESC.get(ct,ct)}</div>
                    <div style="font-size:11px;color:#64748B;margin-top:3px;">
                        Confidence: {float(p.get('ct_confidence',0)):.1%}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with us_col:
                us  = p.get('us_predicted_class','')
                st.markdown(f"""
                <div style="background:#0D1621;border:1px solid #1E293B;
                            border-radius:8px;padding:14px;">
                    <div style="font-size:10px;color:#64748B;
                                font-family:'IBM Plex Mono',monospace;">
                        🔬 ULTRASOUND</div>
                    <div style="font-size:13px;color:#F0F4FF;
                                font-weight:500;margin-top:4px;">
                        {US_DESC.get(us,us)}</div>
                    <div style="font-size:11px;color:#64748B;margin-top:3px;">
                        Confidence: {float(p.get('us_confidence',0)):.1%}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Assign to doctor
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown("""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                        color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                        padding-bottom:8px;border-bottom:1px solid #1E293B;
                        margin-bottom:12px;">── Assign to Doctor</div>
            """, unsafe_allow_html=True)

            ac1, ac2 = st.columns(2)
            with ac1:
                docs = st.session_state.doctors
                doc_opts = {f"{v['name']} — {v['dept']}": k
                            for k,v in docs.items()}
                sel_lbl = st.selectbox('Doctor *',
                                       list(doc_opts.keys()),
                                       key='portal_doc')
                sel_doc_id = doc_opts[sel_lbl]
            with ac2:
                pat_name  = st.text_input('Patient Name (optional)',
                                          placeholder='Ramesh Kumar',
                                          key='portal_name')
                pat_phone = st.text_input('Phone (optional)',
                                          placeholder='+91 98765 43210',
                                          key='portal_phone')

            symptoms = st.text_area('Symptoms / Reason',
                                    placeholder='e.g. Persistent headache...',
                                    height=60, key='portal_symptoms')

            already = cid in st.session_state.patients
            if already:
                st.info(f'✅ Already routed to '
                        f'{st.session_state.patients[cid]["doctor_name"]}')
            else:
                if st.button('🚀 Send to Doctor for Review',
                             use_container_width=True,
                             type='primary', key='portal_submit'):
                    st.session_state.patients[cid] = {
                        **p,
                        'patient_id':    cid,
                        'name':          pat_name or cid,
                        'phone':         pat_phone or 'N/A',
                        'symptoms':      symptoms,
                        'doctor_id':     sel_doc_id,
                        'doctor_name':   docs[sel_doc_id]['name'],
                        'status':        'PENDING',
                        'registered_at': datetime.now().isoformat(),
                    }
                    st.success(
                        f'✅ Case {cid} routed to '
                        f'{docs[sel_doc_id]["name"]}!'
                    )
                    st.balloons()

                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button('Go to Doctor Dashboard →',
                                     key='to_doctor', use_container_width=True):
                            st.session_state.current_patient = cid
                            st.session_state.page = 'doctor'
                            st.rerun()
                    with bc2:
                        if st.button('Select Another Patient',
                                     key='another', use_container_width=True):
                            del st.session_state['portal_selected']
                            st.rerun()

    # ── Tab 2: Track ──────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:14px;">── Submitted Cases</div>
        """, unsafe_allow_html=True)

        if not st.session_state.patients:
            st.info('No cases submitted yet. Select patients from the dataset.')
        else:
            for pid, pat in sorted(
                st.session_state.patients.items(),
                key=lambda x: x[1].get('registered_at',''), reverse=True
            ):
                status = pat.get('status','PENDING')
                fus    = pat.get('fusion_label','Unknown')
                clr    = SEV_COLORS.get(fus,'#94A3B8')
                st_clr = {'APPROVED':'#10B981','REJECTED':'#EF4444',
                          'PENDING':'#F59E0B'}.get(status,'#64748B')

                tc1, tc2 = st.columns([4,1])
                with tc1:
                    st.markdown(f"""
                    <div style="background:#0D1621;border:1px solid #1E293B;
                                border-left:3px solid {clr};border-radius:6px;
                                padding:10px 14px;display:flex;
                                align-items:center;gap:12px;">
                        <span style="font-family:'IBM Plex Mono',monospace;
                                     font-size:13px;color:#F0F4FF;">{pid}</span>
                        <span style="border:1px solid {clr};color:{clr};
                                     font-size:11px;padding:1px 8px;
                                     border-radius:20px;">{fus}</span>
                        <span style="font-size:12px;color:#64748B;">
                            → {pat.get('doctor_name','')}
                        </span>
                        <span style="font-size:11px;color:{st_clr};
                                     margin-left:auto;
                                     font-family:'IBM Plex Mono',monospace;">
                            {status}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with tc2:
                    if status == 'APPROVED':
                        if st.button('View →', key=f'view_{pid}',
                                     use_container_width=True):
                            st.session_state.patient_lookup = pid
                            st.session_state.page = 'result'
                            st.rerun()
