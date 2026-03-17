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
    'notumor':   'No tumor detected',
    'pituitary': 'Pituitary adenoma',
    'meningioma':'Meningioma',
    'glioma':    'Glioma (high-grade)'
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
        ct  = np.random.choice(ct_cls, p=[0.40,0.20,0.25,0.15])
        us  = np.random.choice(us_cls)
        lab = int(np.random.choice([0,1,2,3], p=[0.35,0.30,0.20,0.15]))
        ct_s=ct_sev[ct]; us_s=us_sev[us]; fus=max(lab,ct_s,us_s)
        rows.append({
            'case_id':f'CASE-{1000+i:04d}',
            'lab_score':lab,'lab_severity_label':SCORE_TO_LABEL[lab],
            'ckd_severity':np.random.choice(['G1 (Normal)','G2 (Mild)','G3a','G3b','G4 (Severe)']),
            'diabetes_severity_final':np.random.choice(['Normal','Mild','Moderate','Severe','Unknown']),
            'thyroid_severity_final':np.random.choice(['Normal','Hypothyroid','Hyperthyroid','Unknown']),
            'ct_score':ct_s,'ct_severity_label':SCORE_TO_LABEL[ct_s],
            'ct_predicted_class':ct,
            'ct_confidence':round(float(np.random.uniform(0.75,0.99)),3),
            'us_score':us_s,'us_severity_label':SCORE_TO_LABEL[us_s],
            'us_predicted_class':us,
            'us_confidence':round(float(np.random.uniform(0.80,0.99)),3),
            'fusion_score':fus,'fusion_label':SCORE_TO_LABEL[fus],
            'modalities_available':3,
        })
    return pd.DataFrame(rows)


def render():
    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;border-radius:12px;
                padding:18px 24px;margin-bottom:20px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;color:#F0F4FF;">
            👤 Patient Portal</div>
        <div style="font-size:12px;color:#64748B;margin-top:3px;
                    font-family:'IBM Plex Mono',monospace;">
            Select patient → View AI findings → Assign doctor → Route for review
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander('📂 Upload Your Fusion Dataset (optional)'):
        st.caption('Upload FINAL_MULTIMODAL_FUSION.parquet from NB08 — '
                   'case_id = hadm_id (Lab) / image_id (CT) / patient_num (US). '
                   'Sample data used by default.')
        up = st.file_uploader('Upload',type=['parquet','csv'],
                              key='fusion_up',label_visibility='collapsed')
        if up:
            try:
                df_up = (pd.read_parquet(up) if up.name.endswith('.parquet')
                         else pd.read_csv(up))
                st.session_state['fusion_df'] = df_up
                st.success(f'✅ Loaded {len(df_up):,} patients!')
            except Exception as e:
                st.error(f'Error: {e}')

    if 'fusion_df' not in st.session_state:
        st.session_state['fusion_df'] = build_sample_df()
    df = st.session_state['fusion_df']

    # Filters
    fc1,fc2,fc3 = st.columns([2,1,1])
    with fc1:
        search = st.text_input('Search',placeholder='Search Case ID...',
                               label_visibility='collapsed')
    with fc2:
        sev_f = st.selectbox('Severity',['All','Severe','Moderate','Mild','Normal'],
                             label_visibility='collapsed')
    with fc3:
        sort_sev = st.checkbox('Severe first',value=True)

    filt = df.copy()
    if search:
        filt = filt[filt['case_id'].astype(str).str.contains(
            search,case=False,na=False)]
    if sev_f != 'All':
        filt = filt[filt['fusion_label']==sev_f]
    if sort_sev:
        order={'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        filt  = filt.sort_values('fusion_label',key=lambda x:x.map(order))

    if filt.empty:
        st.warning('No patients match your filter.')
        return

    # Build dropdown labels — shows case_id + severity + CT finding
    def row_label(r):
        done = '✅ ' if str(r['case_id']) in st.session_state.patients else ''
        ct   = CT_DESC.get(r.get('ct_predicted_class',''),'')[:22]
        return (f"{done}{r['case_id']}  |  "
                f"{r.get('fusion_label','?')}  |  CT: {ct}")

    options   = filt['case_id'].astype(str).tolist()
    opt_labels= [row_label(filt[filt['case_id'].astype(str)==c].iloc[0])
                 for c in options]

    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                color:#64748B;margin-bottom:6px;">
        {len(options):,} patients found — select one below
    </div>
    """, unsafe_allow_html=True)

    # SELECTBOX — stays selected on rerun, no disappearing
    chosen_label = st.selectbox(
        '📋 Select Patient from Dataset',
        opt_labels,
        key='portal_selectbox'
    )
    chosen_idx = opt_labels.index(chosen_label)
    chosen_cid = options[chosen_idx]
    p = filt[filt['case_id'].astype(str)==chosen_cid].iloc[0].to_dict()

    cid   = str(p.get('case_id',''))
    fus   = p.get('fusion_label','Unknown')
    color = SEV_COLORS.get(fus,'#94A3B8')

    # Patient detail — shown immediately below selectbox
    st.markdown(f"""
    <div style="background:#0D1621;border:2px solid {color};border-radius:12px;
                padding:16px 20px;margin:10px 0 14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-family:'IBM Plex Mono',monospace;
                         font-size:17px;color:#F0F4FF;font-weight:500;">
                {cid}
            </span>
            <span style="background:rgba(0,0,0,.4);border:1px solid {color};
                         color:{color};font-size:14px;padding:4px 16px;
                         border-radius:20px;font-weight:600;">
                Overall Severity: {fus}
            </span>
        </div>
        <div style="font-size:11px;color:#475569;margin-top:6px;
                    font-family:'IBM Plex Mono',monospace;">
            Modalities: {p.get('modalities_available',0)} · 
            Lab+CT+Ultrasound multimodal fusion
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Score cards
    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,skey,sevkey) in zip([c1,c2,c3,c4],[
        ('🧪 Lab Report','lab_score','lab_severity_label'),
        ('🧠 CT Scan','ct_score','ct_severity_label'),
        ('🔬 Ultrasound','us_score','us_severity_label'),
        ('⚡ Fusion','fusion_score','fusion_label')
    ]):
        with col:
            sc  = p.get(skey)
            sev = p.get(sevkey,'N/A')
            clr = SEV_COLORS.get(sev,'#94A3B8')
            val = str(int(sc)) if sc is not None and pd.notna(sc) else '—'
            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-left:3px solid {clr};border-radius:8px;
                        padding:12px;text-align:center;">
                <div style="font-size:9px;color:#64748B;margin-bottom:2px;">{lbl}</div>
                <div style="font-size:24px;font-weight:700;color:#F0F4FF;">{val}</div>
                <div style="font-size:11px;color:{clr};font-weight:500;">{sev}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Lab breakdown
    d1,d2,d3 = st.columns(3)
    for col,(lbl,key) in zip([d1,d2,d3],[
        ('🔵 CKD Stage','ckd_severity'),
        ('🟠 Diabetes','diabetes_severity_final'),
        ('🟣 Thyroid','thyroid_severity_final')
    ]):
        with col:
            v = p.get(key,'N/A')
            v = 'N/A' if not v or str(v)=='nan' else v
            st.markdown(f"""
            <div style="background:#080C14;border:1px solid #1E293B;
                        border-radius:8px;padding:10px 14px;">
                <div style="font-size:10px;color:#64748B;">{lbl}</div>
                <div style="font-size:12px;color:#F0F4FF;margin-top:2px;">{v}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # CT + US
    ct_c,us_c = st.columns(2)
    with ct_c:
        ct   = p.get('ct_predicted_class','')
        conf = p.get('ct_confidence',0)
        ct_clr = SEV_COLORS.get(p.get('ct_severity_label','Unknown'),'#94A3B8')
        st.markdown(f"""
        <div style="background:#080C14;border:1px solid #1E293B;
                    border-left:3px solid {ct_clr};border-radius:8px;padding:14px;">
            <div style="font-size:10px;color:#64748B;
                        font-family:'IBM Plex Mono',monospace;margin-bottom:5px;">
                🧠 CT SCAN RESULT</div>
            <div style="font-size:14px;color:#F0F4FF;font-weight:600;">
                {CT_DESC.get(ct,ct)}</div>
            <div style="font-size:11px;color:{ct_clr};margin-top:4px;">
                {p.get('ct_severity_label','N/A')} · Confidence: {float(conf):.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with us_c:
        us   = p.get('us_predicted_class','')
        conf = p.get('us_confidence',0)
        us_clr = SEV_COLORS.get(p.get('us_severity_label','Unknown'),'#94A3B8')
        st.markdown(f"""
        <div style="background:#080C14;border:1px solid #1E293B;
                    border-left:3px solid {us_clr};border-radius:8px;padding:14px;">
            <div style="font-size:10px;color:#64748B;
                        font-family:'IBM Plex Mono',monospace;margin-bottom:5px;">
                🔬 ULTRASOUND RESULT</div>
            <div style="font-size:14px;color:#F0F4FF;font-weight:600;">
                {US_DESC.get(us,us)}</div>
            <div style="font-size:11px;color:{us_clr};margin-top:4px;">
                {p.get('us_severity_label','N/A')} · Confidence: {float(conf):.1%}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Assign to doctor
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                padding-bottom:8px;border-bottom:1px solid #1E293B;
                margin-bottom:14px;">── Assign to Doctor
    </div>
    """, unsafe_allow_html=True)

    ac1,ac2 = st.columns(2)
    with ac1:
        docs    = st.session_state.doctors
        doc_opts= {f"{v['name']} — {v['dept']}":k for k,v in docs.items()}
        sel_lbl = st.selectbox('Doctor',list(doc_opts.keys()),key='portal_doc')
        sel_doc = doc_opts[sel_lbl]
    with ac2:
        pat_name  = st.text_input('Patient Name',placeholder='e.g. Ramesh Kumar',
                                  key='portal_name')
        pat_phone = st.text_input('Phone',placeholder='+91 98765 43210',
                                  key='portal_phone')

    symptoms = st.text_area('Symptoms / Reason for Visit',
                            placeholder='e.g. Persistent headache, fatigue...',
                            height=70,key='portal_symptoms')

    already = cid in st.session_state.patients
    if already:
        st.success(f'✅ {cid} already sent to '
                   f'{st.session_state.patients[cid]["doctor_name"]}')
        if st.button('→ Go to Doctor Dashboard',
                     use_container_width=True,type='primary',key='goto_doc2'):
            st.session_state.current_patient = cid
            st.session_state.page = 'doctor'
            st.rerun()
    else:
        if st.button('🚀 Send to Doctor for AI Review',
                     use_container_width=True,type='primary',key='portal_submit'):
            st.session_state.patients[cid] = {
                **p,
                'patient_id':cid,
                'name':pat_name or cid,
                'phone':pat_phone or 'N/A',
                'symptoms':symptoms,
                'doctor_id':sel_doc,
                'doctor_name':docs[sel_doc]['name'],
                'status':'PENDING',
                'registered_at':datetime.now().isoformat(),
            }
            st.success(f'✅ {cid} routed to {docs[sel_doc]["name"]}!')
            st.balloons()
            if st.button('→ Go to Doctor Dashboard',
                         use_container_width=True,key='goto_doc3'):
                st.session_state.current_patient = cid
                st.session_state.page = 'doctor'
                st.rerun()
