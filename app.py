import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="MedAI — Doctor Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#0D1B2E!important;color:#E8EDF5!important;}
.stApp{background:#0D1B2E!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stTextInput>div>div>input{background:#162236!important;color:#E8EDF5!important;border:1.5px solid #263A55!important;border-radius:8px!important;font-size:16px!important;padding:10px 14px!important;}
.stSelectbox>div>div{background:#162236!important;color:#E8EDF5!important;border:1.5px solid #263A55!important;border-radius:8px!important;font-size:15px!important;}
.stTextArea textarea{background:#162236!important;color:#E8EDF5!important;border:1.5px solid #263A55!important;border-radius:8px!important;font-size:14px!important;}
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:600!important;font-size:15px!important;border-radius:8px!important;padding:10px 20px!important;}
.stButton>button[kind="primary"]{background:#2563EB!important;border:none!important;color:white!important;}
.stButton>button[kind="secondary"]{background:#162236!important;border:1.5px solid #263A55!important;color:#94A3B8!important;}
.stTabs [data-baseweb="tab-list"]{background:#0A1628!important;border-bottom:2px solid #1E3250!important;padding:0 8px!important;}
.stTabs [data-baseweb="tab"]{font-size:15px!important;font-weight:500!important;color:#64748B!important;padding:14px 22px!important;}
.stTabs [aria-selected="true"]{color:#4A9EFF!important;border-bottom:3px solid #4A9EFF!important;background:transparent!important;font-weight:700!important;}
hr{border-color:#1E3250!important;}
label{color:#94A3B8!important;font-size:14px!important;}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
SEV_COLOR = {
    'Normal':'#00C48C','Mild':'#FFB800',
    'Moderate':'#FF6B35','Severe':'#FF3B3B','Unknown':'#8892A4'
}
SEV_BG = {
    'Normal':'rgba(0,196,140,0.12)','Mild':'rgba(255,184,0,0.12)',
    'Moderate':'rgba(255,107,53,0.12)','Severe':'rgba(255,59,59,0.12)',
    'Unknown':'rgba(136,146,164,0.12)'
}
CT_NAMES = {
    'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma',
    'meningioma':'Meningioma','glioma':'Glioma'
}
CT_DESC = {
    'notumor':   'Normal brain parenchyma. No suspicious mass or lesion identified.',
    'pituitary': 'Benign pituitary gland tumour. Endocrinology review recommended.',
    'meningioma':'Slow-growing meningeal tumour. Neurosurgery referral advised.',
    'glioma':    'Malignant brain tumour. Urgent oncology referral required.'
}
US_NAMES = {
    'Fetal abdomen':'Fetal Abdomen — Normal',
    'Fetal brain':  'Fetal Brain Plane',
    'Fetal femur':  'Fetal Femur — Normal Growth',
    'Fetal thorax': 'Fetal Thorax Plane'
}
US_DESC = {
    'Fetal abdomen':'Abdominal measurements within expected range for gestational age.',
    'Fetal brain':  'Neurosonography plane identified. Detailed anomaly scan recommended.',
    'Fetal femur':  'Femur length within normal range. Fetal growth on track.',
    'Fetal thorax': 'Thoracic plane identified. Cardiac and pulmonary assessment indicated.'
}
CT_IMAGE = {
    'glioma':    'images/ct_glioma.png',
    'meningioma':'images/ct_meningioma.png',
    'pituitary': 'images/ct_pituitary.png',
    'notumor':   'images/ct_notumor.png'
}
US_IMAGE = {
    'Fetal abdomen':'images/us_abdomen.png',
    'Fetal brain':  'images/us_brain.png',
    'Fetal femur':  'images/us_femur.png',
    'Fetal thorax': 'images/us_thorax.png'
}
SCORE_MAP = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}

# ── Doctor definitions with department routing ────────────────
DOCTORS = {
    'DR001': {
        'name':     'Dr. Priya Sharma',
        'dept':     'Internal Medicine',
        'specialty':'Nephrology & Chronic Disease',
        'color':    '#4A9EFF',
        'password': '1234',
        'mtype':    'Lab Report',
        'tab_idx':  0,
    },
    'DR002': {
        'name':     'Dr. Arjun Mehta',
        'dept':     'Neurology',
        'specialty':'Neuro-Oncology',
        'color':    '#A78BFA',
        'password': '1234',
        'mtype':    'CT Scan',
        'tab_idx':  1,
    },
    'DR003': {
        'name':     'Dr. Kavitha Rajan',
        'dept':     'Obstetrics',
        'specialty':'Fetal Medicine',
        'color':    '#34D399',
        'password': '1234',
        'mtype':    'Ultrasound',
        'tab_idx':  2,
    },
    'DR004': {
        'name':     'Dr. Suresh Kumar',
        'dept':     'General Medicine',
        'specialty':'Multimodal Assessment',
        'color':    '#FBBF24',
        'password': '1234',
        'mtype':    'Combined Assessment',
        'tab_idx':  3,
    },
}

PATIENT_MSG = {
    'Normal': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Good news — your results are within the normal healthy range. "
        "No immediate medical attention is required.\n\n"
        "Please continue your current medication and maintain a healthy lifestyle. "
        "Routine follow-up in 3 months is recommended.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Mild': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results show mild findings that need monitoring. "
        "No emergency at this time.\n\n"
        "Please follow your doctor's prescription and schedule "
        "a follow-up within 2 to 4 weeks.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Moderate': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results indicate findings that need medical attention. "
        "Please follow your doctor's instructions carefully.\n\n"
        "Book a follow-up appointment within 7 to 10 days.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Severe': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results require prompt medical attention. "
        "Please contact your doctor today.\n\n"
        "Do not delay — early treatment leads to the best outcomes.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
}


# ── Data loader ───────────────────────────────────────────────
@st.cache_data
def load_all_data():
    def find(name):
        for p in [f'data/{name}', name]:
            if os.path.exists(p):
                return p
        return None

    lab = ct = us = fus = None
    rag = {}

    p = find('lab_data.csv')
    if p:
        lab = pd.read_csv(p)
        lab['final_severity_label'] = lab['final_severity_label'].replace('Stable','Normal')

    p = find('ct_data.csv')
    if p:
        ct = pd.read_csv(p)

    p = find('us_data.csv')
    if p:
        us = pd.read_csv(p)

    p = find('fusion_data.csv')
    if p:
        fus = pd.read_csv(p)

    p = find('rag_summaries.json')
    if p:
        with open(p) as f:
            rag = json.load(f)

    return lab, ct, us, fus, rag


def parse_rag(raw_text: str) -> dict:
    sections = {
        'clinical_summary':'','key_findings':[],
        'recommendations':[],'followup':'','urgency':'',
    }
    current = None
    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        lu = line.upper()
        if 'CLINICAL SUMMARY' in lu:
            current = 'clinical_summary'
        elif 'KEY FINDINGS' in lu:
            current = 'key_findings'
        elif 'RECOMMENDATION' in lu:
            current = 'recommendations'
        elif 'FOLLOW' in lu and 'PLAN' in lu:
            current = 'followup'
        elif lu.startswith('URGENCY'):
            sections['urgency'] = line.split(':')[-1].strip()
            current = None
        elif current == 'clinical_summary' and not lu.startswith('CLINICAL'):
            sections['clinical_summary'] += line + ' '
        elif current == 'key_findings' and line.startswith('•'):
            sections['key_findings'].append(line[1:].strip())
        elif current == 'recommendations' and line.startswith('•'):
            sections['recommendations'].append(line[1:].strip())
        elif current == 'followup' and not lu.startswith('FOLLOW'):
            sections['followup'] += line + ' '
    return sections


def get_mm_rag_key(row: dict, rag_data: dict) -> str:
    """
    For combined patients pick best matching RAG key
    based on highest severity modality.
    """
    fusion_sev = str(row.get('fusion_label', row.get('_sev','Normal'))).lower()

    # Check each modality score — pick the most severe one
    lab_s = row.get('lab_score')
    ct_s  = row.get('ct_score')
    us_s  = row.get('us_score')

    try:
        lab_s = int(float(lab_s)) if lab_s is not None and str(lab_s) not in ['None','nan'] else -1
    except Exception:
        lab_s = -1
    try:
        ct_s = int(float(ct_s)) if ct_s is not None and str(ct_s) not in ['None','nan'] else -1
    except Exception:
        ct_s = -1
    try:
        us_s = int(float(us_s)) if us_s is not None and str(us_s) not in ['None','nan'] else -1
    except Exception:
        us_s = -1

    # Pick dominant modality
    scores = {'lab': lab_s, 'ct': ct_s, 'us': us_s}
    dominant = max(scores, key=lambda k: scores[k])

    sev_str = {0:'normal',1:'mild',2:'moderate',3:'severe'}.get(
        max(lab_s, ct_s, us_s), 'normal')

    if dominant == 'ct':
        ct_cls = str(row.get('ct_predicted_class','notumor')).lower()
        key    = f'ct_{ct_cls}'
        if key in rag_data:
            return key
    elif dominant == 'us':
        us_cls = str(row.get('us_predicted_class',
                              row.get('predicted_class','')))
        if 'brain'   in us_cls.lower(): return 'us_brain'
        if 'thorax'  in us_cls.lower(): return 'us_thorax'
        if 'femur'   in us_cls.lower(): return 'us_femur'
        if 'abdomen' in us_cls.lower(): return 'us_abdomen'

    # Default to lab diabetes key
    return f'lab_diabetes_{sev_str}'


# ── Session state ─────────────────────────────────────────────
for k, v in {
    'logged_in':     False,
    'active_doctor': None,
    'selected':      {},    # doc_id → pid
    'decisions':     {},    # pid → 'APPROVED'/'REJECTED' + details
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

lab_df, ct_df, us_df, fus_df, rag_data = load_all_data()


# ══════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════
def render_login():
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown('<div style="margin-top:80px;">', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;margin-bottom:32px;">'
            '<div style="background:#2563EB;width:56px;height:56px;'
            'border-radius:14px;display:flex;align-items:center;'
            'justify-content:center;font-size:28px;margin:0 auto 14px;">🏥</div>'
            '<div style="font-size:26px;font-weight:800;color:#F0F6FF;">'
            'MedAI Clinical System</div>'
            '<div style="font-size:15px;color:#7A90A8;margin-top:6px;">'
            'Doctor Login</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:#112033;border:1.5px solid #1E3250;'
            'border-radius:16px;padding:32px 36px;">',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:13px;font-weight:600;color:#64748B;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
            'Select Doctor</div>',
            unsafe_allow_html=True
        )
        doc_labels = {
            f"{v['name']} — {v['dept']}": k for k,v in DOCTORS.items()
        }
        sel_label = st.selectbox(
            'Doctor', list(doc_labels.keys()),
            label_visibility='collapsed', key='login_doc'
        )
        sel_id = doc_labels[sel_label]

        st.markdown(
            '<div style="font-size:13px;font-weight:600;color:#64748B;'
            'text-transform:uppercase;letter-spacing:0.08em;'
            'margin:16px 0 6px;">Password</div>',
            unsafe_allow_html=True
        )
        pwd = st.text_input(
            'Password', type='password',
            placeholder='Enter your password',
            label_visibility='collapsed', key='login_pwd'
        )

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('Login →', use_container_width=True, type='primary'):
            if pwd == DOCTORS[sel_id]['password']:
                st.session_state.logged_in     = True
                st.session_state.active_doctor = sel_id
                st.rerun()
            else:
                st.error('Incorrect password.')

        st.markdown(
            '<div style="font-size:12px;color:#4A6080;text-align:center;'
            'margin-top:14px;">Demo password: 1234</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════
def render_dashboard():
    active_id = st.session_state.active_doctor
    active    = DOCTORS[active_id]

    # Top bar
    c1,c2,c3 = st.columns([1,4,1])
    with c1:
        st.markdown(
            '<div style="padding:16px 0 0 28px;font-size:18px;'
            'font-weight:800;color:#F0F6FF;">🏥 MedAI</div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            '<div style="padding:12px 0;">'
            '<span style="font-size:15px;font-weight:700;color:#F0F6FF;">'
            + active['name'] + '</span>'
            '<span style="font-size:13px;color:#7A90A8;margin-left:12px;">'
            + active['dept'] + '  ·  ' + active['specialty'] + '</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown('<div style="padding:14px 28px 0 0;">', unsafe_allow_html=True)
        if st.button('Logout', key='logout_btn'):
            for k in ['logged_in','active_doctor','selected']:
                st.session_state[k] = False if k=='logged_in' else None if k=='active_doctor' else {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:0;">', unsafe_allow_html=True)
    st.markdown('<div style="padding:20px 28px;">', unsafe_allow_html=True)

    # ── DEPARTMENT ROUTING ────────────────────────────────────
    # Each doctor sees ONLY their department tab + a summary of others
    mtype     = active['mtype']
    dept_icon = {'Lab Report':'🧪','CT Scan':'🧠',
                 'Ultrasound':'🔬','Combined Assessment':'⚡'}.get(mtype,'📋')

    st.markdown(
        '<div style="font-size:22px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.5px;margin-bottom:6px;">'
        + dept_icon + '  ' + active['dept'] + ' — Patient Reports</div>'
        '<div style="font-size:15px;color:#7A90A8;margin-bottom:20px;">'
        'Showing reports ordered by ' + active['name'] + '</div>',
        unsafe_allow_html=True
    )

    # Get correct dataframe and columns for this doctor
    df_map = {
        'Lab Report':          (lab_df,  'patient_id',  'final_severity_label'),
        'CT Scan':             (ct_df,   'patient_id',  'fusion_label'),
        'Ultrasound':          (us_df,   'patient_id',  'fusion_label'),
        'Combined Assessment': (fus_df,  'patient_id',  'fusion_label'),
    }
    df, id_col, sev_col = df_map.get(mtype, (None, None, None))

    if df is None:
        st.warning('No data available for your department.')
        return

    render_dept(active_id, df, mtype, id_col, sev_col)
    st.markdown('</div>', unsafe_allow_html=True)


def render_dept(doc_id, df, mtype, id_col, sev_col):
    doc = DOCTORS[doc_id]

    # Stats
    sev_counts = df[sev_col].value_counts() if sev_col in df.columns else {}
    s1,s2,s3,s4 = st.columns(4)
    for col,(lbl,clr) in zip([s1,s2,s3,s4],[
        ('Severe','#FF3B3B'),('Moderate','#FF6B35'),
        ('Mild','#FFB800'),  ('Normal','#00C48C')
    ]):
        cnt = int(sev_counts.get(lbl, 0))
        with col:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-top:3px solid ' + clr + ';border-radius:10px;'
                'padding:14px;text-align:center;margin-bottom:16px;">'
                '<div style="font-size:30px;font-weight:800;color:' + clr + ';">'
                + str(cnt) + '</div>'
                '<div style="font-size:13px;color:#7A90A8;margin-top:4px;">'
                + lbl + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    left, right = st.columns([1, 2.5], gap='large')

    with left:
        st.markdown(
            '<div style="font-size:12px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">'
            'Patient Queue</div>',
            unsafe_allow_html=True
        )
        sev_filter = st.selectbox(
            'Filter', ['All','Severe','Moderate','Mild','Normal'],
            key='filter_' + doc_id, label_visibility='collapsed'
        )
        filt = df if sev_filter == 'All' \
               else df[df[sev_col] == sev_filter]
        sev_ord = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        if sev_col in filt.columns:
            filt = filt.sort_values(sev_col, key=lambda x: x.map(sev_ord))

        for _, row in filt.iterrows():
            pid    = str(row[id_col])
            sev    = str(row.get(sev_col,'Unknown'))
            is_sel = st.session_state.selected.get(doc_id) == pid
            dec    = st.session_state.decisions.get(pid,{}).get('status','')
            icon   = {'APPROVED':'✓ ','REJECTED':'✗ '}.get(dec,'')

            if st.button(
                icon + pid + '  ·  ' + sev,
                key='pat_' + doc_id + '_' + pid,
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                st.session_state.selected[doc_id] = pid
                st.rerun()

    with right:
        sel_pid = st.session_state.selected.get(doc_id)
        if not sel_pid:
            st.markdown(
                '<div style="background:#112033;border:2px dashed #1E3250;'
                'border-radius:14px;padding:80px;text-align:center;">'
                '<div style="font-size:36px;margin-bottom:14px;">👈</div>'
                '<div style="font-size:16px;color:#7A90A8;">'
                'Select a patient from the queue</div>'
                '</div>',
                unsafe_allow_html=True
            )
            return

        match = df[df[id_col] == sel_pid]
        if match.empty:
            return
        row = match.iloc[0].to_dict()
        sev = str(row.get(sev_col,'Unknown'))
        clr = SEV_COLOR.get(sev,'#8892A4')
        bg  = SEV_BG.get(sev,'rgba(136,146,164,0.1)')

        render_patient(row, sel_pid, sev, clr, bg, mtype, doc_id)


def render_patient(row, pid, sev, clr, bg, mtype, doc_id):
    doc     = DOCTORS[doc_id]
    urgency = {'Severe':'URGENT','Moderate':'SEMI-URGENT',
               'Mild':'ROUTINE','Normal':'ROUTINE'}.get(sev,'REVIEW')
    urg_clr = {'Severe':'#FF3B3B','Moderate':'#FF6B35',
               'Mild':'#FFB800','Normal':'#00C48C'}.get(sev,'#8892A4')

    # Current decision
    current_decision = st.session_state.decisions.get(pid,{}).get('status','')

    # Patient header
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-radius:14px;padding:18px 22px;margin-bottom:18px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;">'
        '<div>'
        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">Patient ID</div>'
        '<div style="font-size:22px;font-weight:800;color:#F0F6FF;'
        'font-family:monospace;">' + pid + '</div>'
        '<div style="font-size:13px;color:#7A90A8;margin-top:4px;">'
        + mtype + '  ·  Ordered by ' + doc['name'] + '</div>'
        '</div>'
        '<div style="background:' + bg + ';border:2px solid ' + urg_clr + '44;'
        'border-radius:10px;padding:10px 18px;text-align:center;">'
        '<div style="font-size:11px;font-weight:700;color:' + urg_clr + ';'
        'letter-spacing:0.12em;margin-bottom:4px;">' + urgency + '</div>'
        '<div style="font-size:20px;font-weight:800;color:' + clr + ';">'
        + sev + '</div>'
        '</div></div></div>',
        unsafe_allow_html=True
    )

    # ── Test Findings ─────────────────────────────────────────
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">'
        'Test Findings</div>',
        unsafe_allow_html=True
    )

    if mtype == 'Lab Report':
        render_lab_findings(row, sev, clr)

    elif mtype == 'CT Scan':
        render_ct_findings(row, sev, clr)

    elif mtype == 'Ultrasound':
        render_us_findings(row, sev, clr)

    elif mtype == 'Combined Assessment':
        render_combined_findings(row)

    # ── RAG Summary ───────────────────────────────────────────
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:18px 0 12px;">'
        'AI Clinical Summary</div>',
        unsafe_allow_html=True
    )

    # Get correct RAG key
    if mtype == 'Combined Assessment':
        rag_key = get_mm_rag_key(row, rag_data)
    else:
        rag_key = str(row.get('rag_class_key',''))

    rag_raw   = rag_data.get(rag_key,{})
    raw_text  = rag_raw.get('raw_text','') if isinstance(rag_raw, dict) else ''
    citations = rag_raw.get('citations',[]) if isinstance(rag_raw, dict) else []

    if raw_text:
        parsed = parse_rag(raw_text)
        render_rag_sections(parsed, citations)
    else:
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-radius:10px;padding:16px 20px;color:#64748B;">'
            'RAG summary not available for this patient class.</div>',
            unsafe_allow_html=True
        )

    # ── Decision section ──────────────────────────────────────
    # Show decision section ONLY if not yet decided
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:18px 0 10px;">'
        'Doctor Review & Decision</div>',
        unsafe_allow_html=True
    )

    if current_decision == 'APPROVED':
        ap = st.session_state.decisions[pid]
        st.markdown(
            '<div style="background:rgba(0,196,140,0.1);'
            'border:1.5px solid rgba(0,196,140,0.3);border-radius:12px;'
            'padding:18px 22px;">'
            '<div style="font-size:16px;font-weight:700;color:#00C48C;'
            'margin-bottom:8px;">✅  Report Approved</div>'
            '<div style="font-size:14px;color:#7A90A8;line-height:1.7;">'
            'Approved by: <b style="color:#F0F6FF;">' + ap['doctor'] + '</b><br>'
            'Time: ' + ap['time'] + '<br>'
            'Patient message has been sent.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Show message preview for reference
        with st.expander('📱 View Patient Message Sent'):
            st.markdown(
                '<div style="background:#0A1628;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:16px 20px;font-size:14px;'
                'color:#C8D6E8;white-space:pre-wrap;line-height:1.8;">'
                + ap['message'] + '</div>',
                unsafe_allow_html=True
            )

    elif current_decision == 'REJECTED':
        st.markdown(
            '<div style="background:rgba(255,59,59,0.1);'
            'border:1.5px solid rgba(255,59,59,0.3);border-radius:12px;'
            'padding:18px 22px;">'
            '<div style="font-size:16px;font-weight:700;color:#FF3B3B;'
            'margin-bottom:8px;">❌  Report Rejected</div>'
            '<div style="font-size:14px;color:#7A90A8;">'
            'This report has been rejected. Patient has NOT been notified.<br>'
            'Please review and resubmit or request further tests.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button('↺  Reset Decision', key='reset_' + pid):
            del st.session_state.decisions[pid]
            st.rerun()

    else:
        # No decision yet — show input form
        notes = st.text_area(
            'Clinical notes / prescription',
            placeholder='Add prescription, amendments, or clinical instructions...',
            height=100,
            key='notes_' + doc_id + '_' + pid,
            label_visibility='collapsed'
        )

        # Patient message preview
        pat_msg = PATIENT_MSG.get(sev, PATIENT_MSG['Normal'])
        if notes:
            pat_msg += '\n\nDoctor\'s additional instructions:\n' + notes

        with st.expander('📱  Preview Patient Message'):
            st.markdown(
                '<div style="background:#0A1628;border:1.5px solid #1E3250;'
                'border-radius:12px;padding:18px 22px;">'
                '<div style="font-size:12px;font-weight:600;color:#00C48C;'
                'margin-bottom:10px;letter-spacing:0.08em;">MESSAGE TO PATIENT</div>'
                '<div style="font-size:14px;color:#C8D6E8;line-height:1.8;'
                'white-space:pre-wrap;">' + pat_msg + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        st.markdown('<br>', unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)

        with b1:
            if st.button('✅  Approve & Send',
                         key='app_' + doc_id + '_' + pid,
                         use_container_width=True, type='primary'):
                st.session_state.decisions[pid] = {
                    'status':  'APPROVED',
                    'doctor':  doc['name'],
                    'time':    datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'notes':   notes,
                    'message': pat_msg,
                }
                st.rerun()

        with b2:
            if st.button('✏️  Approve with Edits',
                         key='edit_' + doc_id + '_' + pid,
                         use_container_width=True):
                st.session_state.decisions[pid] = {
                    'status':  'APPROVED',
                    'doctor':  doc['name'],
                    'time':    datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'notes':   notes,
                    'message': pat_msg,
                }
                st.rerun()

        with b3:
            if st.button('❌  Reject',
                         key='rej_' + doc_id + '_' + pid,
                         use_container_width=True):
                st.session_state.decisions[pid] = {
                    'status':  'REJECTED',
                    'doctor':  doc['name'],
                    'time':    datetime.now().strftime('%Y-%m-%d %H:%M'),
                }
                st.rerun()


# ── Findings renderers ────────────────────────────────────────
def render_lab_findings(row, sev, clr):
    ckd = str(row.get('ckd_severity','Not tested'))
    dia = str(row.get('diabetes_severity_final','Not tested'))
    thy = str(row.get('thyroid_severity_final','Not tested'))
    disease = str(row.get('disease_type','')).lower()

    # Clean up None/nan
    ckd = 'Not tested' if ckd in ['None','nan','NaN','Unknown'] else ckd
    dia = 'Not tested' if dia in ['None','nan','NaN','Unknown'] else dia
    thy = 'Not tested' if thy in ['None','nan','NaN','Unknown'] else thy

    c1,c2,c3 = st.columns(3)
    for col,(lbl,val) in zip([c1,c2,c3],[
        ('Kidney Function (eGFR)', ckd),
        ('Blood Sugar (HbA1c)',    dia),
        ('Thyroid (TSH)',           thy)
    ]):
        v_clr = clr if val != 'Not tested' else '#4A6080'
        with col:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:16px;margin-bottom:12px;">'
                '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">'
                + lbl + '</div>'
                '<div style="font-size:17px;font-weight:700;color:' + v_clr + ';">'
                + val + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # Patient-specific reference range based on disease type
    if 'ckd' in disease or 'kidney' in disease:
        ref_html = (
            '<b style="color:#F0F6FF;">Patient Condition: Chronic Kidney Disease</b><br>'
            'eGFR Stages: G1 ≥90 (Normal) · G2 60–89 (Mild) · '
            'G3a 45–59 (Mild-Moderate) · G3b 30–44 (Moderate-Severe) · '
            'G4 15–29 (Severe) · G5 &lt;15 (Kidney Failure)<br>'
            'Target: Blood pressure &lt;130/80 mmHg · Protein restriction if proteinuria present<br>'
            'Source: KDIGO 2022 Clinical Practice Guidelines'
        )
    elif 'diabetes' in disease:
        ref_html = (
            '<b style="color:#F0F6FF;">Patient Condition: Diabetes Mellitus</b><br>'
            'HbA1c: Normal &lt;5.7% · Pre-diabetic 5.7–6.4% · Diabetic ≥6.5%<br>'
            'Target HbA1c: &lt;7.0% (most adults) · &lt;8.0% (elderly/complex patients)<br>'
            'Fasting Glucose: Normal &lt;100 mg/dL · Diabetic ≥126 mg/dL<br>'
            'Source: ADA Standards of Medical Care in Diabetes 2024'
        )
    elif 'thyroid' in disease:
        ref_html = (
            '<b style="color:#F0F6FF;">Patient Condition: Thyroid Disorder</b><br>'
            'TSH: Normal 0.4–4.0 mIU/L · Subclinical Hypothyroid 4.0–10.0 · Overt &gt;10.0<br>'
            'Free T4: Normal 0.8–1.8 ng/dL · Low T4 = Hypothyroidism<br>'
            'Treatment: Levothyroxine therapy if TSH &gt;10 mIU/L or symptomatic<br>'
            'Source: ATA/AACE Guidelines for Thyroid Disease Management'
        )
    else:
        ref_html = (
            'HbA1c: Normal &lt;5.7% · Pre-diabetic 5.7–6.4% · Diabetic ≥6.5%<br>'
            'eGFR: G1 ≥90 · G2 60–89 · G3 30–59 · G4 15–29 · G5 &lt;15<br>'
            'TSH: Normal 0.4–4.0 mIU/L · Free T4: 0.8–1.8 ng/dL'
        )

    st.markdown(
        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
        'border-left:4px solid #4A9EFF;border-radius:10px;'
        'padding:14px 18px;margin-bottom:14px;">'
        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">'
        'Patient Reference Ranges & Guidelines</div>'
        '<div style="font-size:13px;color:#7A90A8;line-height:1.9;">'
        + ref_html + '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def render_ct_findings(row, sev, clr):
    cls  = row.get('ct_predicted_class', row.get('disease_type',''))
    conf = row.get('ct_confidence', 0)
    name = CT_NAMES.get(cls, cls)
    desc = CT_DESC.get(cls,'')

    st.markdown(
        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
        'border-left:5px solid ' + clr + ';border-radius:10px;'
        'padding:18px 22px;margin-bottom:14px;">'
        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">'
        'CT Brain Imaging</div>'
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;margin-bottom:6px;">'
        + name + '</div>'
        '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">' + desc + '</div>'
        '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
        + sev + '  ·  AI Confidence: ' + str(round(float(conf)*100,1)) + '%'
        '</div></div>',
        unsafe_allow_html=True
    )
    img = CT_IMAGE.get(str(cls),'')
    if img and os.path.exists(img):
        gc1,gc2 = st.columns(2)
        with gc1:
            st.image(img, caption='CT Scan', use_column_width=True)
        with gc2:
            st.image(img, caption='Grad-CAM Heatmap', use_column_width=True)
        st.markdown(
            '<div style="font-size:12px;color:#4A6080;margin-bottom:12px;">'
            'Highlighted regions indicate areas of diagnostic significance '
            'identified by the AI model.</div>',
            unsafe_allow_html=True
        )


def render_us_findings(row, sev, clr):
    cls  = row.get('predicted_class', row.get('disease_type',''))
    conf = row.get('confidence', 0)
    name = US_NAMES.get(cls, cls)
    desc = US_DESC.get(cls,'')

    st.markdown(
        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
        'border-left:5px solid ' + clr + ';border-radius:10px;'
        'padding:18px 22px;margin-bottom:14px;">'
        '<div style="font-size:12px;font-weight:600;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">'
        'Obstetric Ultrasound</div>'
        '<div style="font-size:18px;font-weight:700;color:#F0F6FF;margin-bottom:6px;">'
        + name + '</div>'
        '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">' + desc + '</div>'
        '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
        + sev + '  ·  AI Confidence: ' + str(round(float(conf)*100,1)) + '%'
        '</div></div>',
        unsafe_allow_html=True
    )
    img = US_IMAGE.get(str(cls),'')
    if img and os.path.exists(img):
        ug1,ug2 = st.columns(2)
        with ug1:
            st.image(img, caption='Ultrasound Scan', use_column_width=True)
        with ug2:
            st.image(img, caption='Grad-CAM Heatmap', use_column_width=True)


def render_combined_findings(row):
    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,key) in zip([c1,c2,c3,c4],[
        ('Lab','lab_score'),('CT','ct_score'),
        ('Ultrasound','us_score'),('Fusion','fusion_score')
    ]):
        val = row.get(key)
        try:
            v = SCORE_MAP.get(int(float(val)),'—') \
                if val is not None and str(val) not in ['None','nan'] else '—'
        except Exception:
            v = '—'
        vc = SEV_COLOR.get(v,'#4A6080')
        with col:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:14px;text-align:center;margin-bottom:12px;">'
                '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">'
                + lbl + '</div>'
                '<div style="font-size:22px;font-weight:800;color:' + vc + ';">'
                + v + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # Show CT and US details for combined patients
    ct_cls = row.get('ct_predicted_class','')
    us_cls = row.get('us_predicted_class', row.get('predicted_class',''))
    if ct_cls:
        st.markdown(
            '<div style="font-size:13px;color:#7A90A8;margin-bottom:6px;">'
            '🧠 CT: <b style="color:#F0F6FF;">' + CT_NAMES.get(ct_cls,ct_cls) + '</b>'
            '  ·  🔬 US: <b style="color:#F0F6FF;">' + US_NAMES.get(us_cls,us_cls) + '</b>'
            '</div>',
            unsafe_allow_html=True
        )


def render_rag_sections(parsed, citations):
    if parsed['clinical_summary']:
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #263A55;'
            'border-left:5px solid #7C3AED;border-radius:12px;'
            'padding:18px 22px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
            'Clinical Overview</div>'
            '<div style="font-size:15px;color:#E8EDF5;line-height:1.8;">'
            + parsed['clinical_summary'] + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    if parsed['key_findings']:
        fh = ''.join([
            '<div style="display:flex;gap:10px;padding:8px 0;'
            'border-bottom:1px solid #1E3250;">'
            '<span style="color:#7C3AED;font-weight:700;flex-shrink:0;">•</span>'
            '<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">'
            + f + '</span></div>'
            for f in parsed['key_findings']
        ])
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-radius:10px;padding:16px 20px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">'
            'Key Findings</div>' + fh + '</div>',
            unsafe_allow_html=True
        )

    if parsed['recommendations']:
        rh = ''.join([
            '<div style="display:flex;gap:12px;padding:10px 0;'
            'border-bottom:1px solid #1E3250;">'
            '<span style="background:#2563EB22;color:#4A9EFF;font-weight:700;'
            'font-size:13px;padding:2px 8px;border-radius:6px;flex-shrink:0;">'
            + str(i+1) + '</span>'
            '<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">'
            + r + '</span></div>'
            for i,r in enumerate(parsed['recommendations'])
        ])
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid #00C48C;border-radius:10px;'
            'padding:16px 20px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">'
            'Clinical Recommendations</div>' + rh + '</div>',
            unsafe_allow_html=True
        )

    fu_col,ug_col = st.columns(2)
    with fu_col:
        if parsed['followup']:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:14px 18px;margin-bottom:12px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                'Follow-up Plan</div>'
                '<div style="font-size:14px;color:#E8EDF5;font-weight:500;">'
                + parsed['followup'] + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
    with ug_col:
        if parsed['urgency']:
            uc = {'URGENT':'#FF3B3B','SEMI-URGENT':'#FF6B35',
                  'ROUTINE':'#00C48C'}.get(parsed['urgency'].upper(),'#8892A4')
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:14px 18px;margin-bottom:12px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                'Urgency</div>'
                '<div style="font-size:18px;font-weight:800;color:' + uc + ';">'
                + parsed['urgency'] + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    if citations:
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-radius:10px;padding:12px 18px;margin-bottom:14px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
            'Guideline References</div>'
            '<div style="font-size:13px;color:#64748B;font-family:monospace;">'
            + '  ·  '.join(citations) + '</div>'
            '</div>',
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    render_login()
else:
    render_dashboard()
