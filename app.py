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

# ── Global CSS ────────────────────────────────────────────────
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
    'Normal':  '#00C48C', 'Mild':    '#FFB800',
    'Moderate':'#FF6B35', 'Severe':  '#FF3B3B', 'Unknown':'#8892A4'
}
SEV_BG = {
    'Normal':  'rgba(0,196,140,0.12)',  'Mild':    'rgba(255,184,0,0.12)',
    'Moderate':'rgba(255,107,53,0.12)', 'Severe':  'rgba(255,59,59,0.12)',
    'Unknown': 'rgba(136,146,164,0.12)'
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
    'glioma':'images/ct_glioma.png','meningioma':'images/ct_meningioma.png',
    'pituitary':'images/ct_pituitary.png','notumor':'images/ct_notumor.png'
}
US_IMAGE = {
    'Fetal abdomen':'images/us_abdomen.png','Fetal brain':'images/us_brain.png',
    'Fetal femur':'images/us_femur.png','Fetal thorax':'images/us_thorax.png'
}

DOCTORS = {
    'DR001': {
        'name':     'Dr. Priya Sharma',
        'dept':     'Internal Medicine',
        'specialty':'Nephrology & Chronic Disease',
        'color':    '#4A9EFF',
        'password': '1234',
        'tab_label':'🧪  Internal Medicine — Dr. Priya Sharma'
    },
    'DR002': {
        'name':     'Dr. Arjun Mehta',
        'dept':     'Neurology',
        'specialty':'Neuro-Oncology',
        'color':    '#A78BFA',
        'password': '1234',
        'tab_label':'🧠  Neurology — Dr. Arjun Mehta'
    },
    'DR003': {
        'name':     'Dr. Kavitha Rajan',
        'dept':     'Obstetrics',
        'specialty':'Fetal Medicine',
        'color':    '#34D399',
        'password': '1234',
        'tab_label':'🔬  Obstetrics — Dr. Kavitha Rajan'
    },
    'DR004': {
        'name':     'Dr. Suresh Kumar',
        'dept':     'General Medicine',
        'specialty':'Multimodal Assessment',
        'color':    '#FBBF24',
        'password': '1234',
        'tab_label':'⚡  General Medicine — Dr. Suresh Kumar'
    },
}

PATIENT_MSG = {
    'Normal': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Good news — your results are within the normal healthy range. "
        "No immediate medical attention is required at this time.\n\n"
        "Please continue your current medication and maintain a healthy lifestyle. "
        "Your next routine check-up is recommended in 3 months.\n\n"
        "If you have any concerns, please do not hesitate to contact us.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Mild': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results show some mild findings that need to be monitored. "
        "There is no emergency at this time.\n\n"
        "Please follow your doctor's prescription carefully and schedule "
        "a follow-up appointment within 2 to 4 weeks.\n\n"
        "Contact your doctor if your symptoms worsen.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Moderate': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results indicate findings that need medical attention. "
        "Please follow your doctor's instructions carefully.\n\n"
        "Please book a follow-up appointment within the next 7 to 10 days. "
        "Bring this report to your appointment.\n\n"
        "Early treatment leads to better outcomes.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
    'Severe': (
        "Dear Patient,\n\n"
        "Your test results have been reviewed and approved by your doctor.\n\n"
        "Your results indicate findings that require prompt medical attention. "
        "Please do not delay in following your doctor's instructions.\n\n"
        "Please contact your doctor today or visit the hospital immediately "
        "if you feel unwell. Your doctor may contact you directly.\n\n"
        "Early treatment is critical for the best outcomes.\n\n"
        "Regards,\nMedAI Clinical System"
    ),
}


# ── Data loaders ──────────────────────────────────────────────
@st.cache_data
def load_all_data():
    """Load all CSV files and RAG summaries once."""
    # Find files — check data/ folder and root
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


def parse_rag_summary(raw_text: str) -> dict:
    """Parse RAG summary text into structured sections."""
    sections = {
        'clinical_summary': '',
        'key_findings':     [],
        'recommendations':  [],
        'followup':         '',
        'urgency':          '',
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
        elif 'CLINICAL RECOMMENDATIONS' in lu or 'RECOMMENDATIONS' in lu:
            current = 'recommendations'
        elif 'FOLLOW' in lu and 'PLAN' in lu:
            current = 'followup'
        elif 'URGENCY' in lu:
            sections['urgency'] = line.split(':')[-1].strip()
            current = None
        elif current == 'clinical_summary':
            sections['clinical_summary'] += line + ' '
        elif current == 'key_findings' and line.startswith('•'):
            sections['key_findings'].append(line[1:].strip())
        elif current == 'recommendations' and line.startswith('•'):
            sections['recommendations'].append(line[1:].strip())
        elif current == 'followup':
            sections['followup'] += line + ' '
    return sections


# ── Session state ─────────────────────────────────────────────
for k, v in {
    'logged_in':        False,
    'active_doctor':    None,
    'selected_patient': None,
    'approved':         {},   # pid → {notes, timestamp}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load data
lab_df, ct_df, us_df, fus_df, rag_data = load_all_data()


# ══════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════
def render_login():
    st.markdown(
        '<div style="max-width:480px;margin:80px auto;">'
        '<div style="text-align:center;margin-bottom:40px;">'
        '<div style="background:#2563EB;width:56px;height:56px;border-radius:14px;'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:28px;margin:0 auto 16px;">🏥</div>'
        '<div style="font-size:28px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.5px;">MedAI Clinical System</div>'
        '<div style="font-size:15px;color:#7A90A8;margin-top:6px;">'
        'Doctor Login Portal</div>'
        '</div>',
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown(
            '<div style="background:#112033;border:1.5px solid #1E3250;'
            'border-radius:16px;padding:32px 36px;">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="font-size:14px;font-weight:600;color:#94A3B8;'
            'margin-bottom:6px;text-transform:uppercase;'
            'letter-spacing:0.08em;">Select Doctor</div>',
            unsafe_allow_html=True
        )
        doc_labels = {
            f"{v['name']} — {v['dept']}": k
            for k, v in DOCTORS.items()
        }
        sel_label = st.selectbox(
            'Doctor', list(doc_labels.keys()),
            label_visibility='collapsed',
            key='login_doc'
        )
        sel_id = doc_labels[sel_label]
        doc    = DOCTORS[sel_id]

        st.markdown(
            '<div style="font-size:14px;font-weight:600;color:#94A3B8;'
            'margin:16px 0 6px;text-transform:uppercase;'
            'letter-spacing:0.08em;">Password</div>',
            unsafe_allow_html=True
        )
        pwd = st.text_input(
            'Password', type='password',
            placeholder='Enter your password',
            label_visibility='collapsed',
            key='login_pwd'
        )

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('Login →', use_container_width=True, type='primary'):
            if pwd == doc['password']:
                st.session_state.logged_in     = True
                st.session_state.active_doctor = sel_id
                st.rerun()
            else:
                st.error('Incorrect password. Please try again.')

        st.markdown(
            '<div style="font-size:13px;color:#4A6080;text-align:center;'
            'margin-top:16px;">Demo password: 1234 for all doctors</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════
def render_dashboard():
    active_id = st.session_state.active_doctor
    active    = DOCTORS[active_id]

    # Top bar
    col_logo, col_doc, col_logout = st.columns([1, 4, 1])
    with col_logo:
        st.markdown(
            '<div style="padding:14px 0 0 28px;">'
            '<div style="font-size:20px;font-weight:800;color:#F0F6FF;">🏥 MedAI</div>'
            '</div>',
            unsafe_allow_html=True
        )
    with col_doc:
        st.markdown(
            '<div style="padding:12px 0;">'
            '<div style="font-size:15px;font-weight:600;color:#F0F6FF;">'
            + active['name'] +
            '</div>'
            '<div style="font-size:13px;color:#7A90A8;">'
            + active['dept'] + '  ·  ' + active['specialty'] +
            '</div></div>',
            unsafe_allow_html=True
        )
    with col_logout:
        st.markdown('<div style="padding:14px 28px 0 0;">', unsafe_allow_html=True)
        if st.button('Logout', key='logout'):
            st.session_state.logged_in     = False
            st.session_state.active_doctor = None
            st.session_state.selected_patient = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<hr style="border-color:#1E3250;margin:0 0 0 0;">',
        unsafe_allow_html=True
    )

    st.markdown('<div style="padding:20px 28px;">', unsafe_allow_html=True)

    # 4 department tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        '🧪  Internal Medicine',
        '🧠  Neurology',
        '🔬  Obstetrics',
        '⚡  General Medicine',
    ])

    dept_configs = [
        (tab1, 'DR001', lab_df,  'Lab Report',          'patient_id',  'final_severity_label'),
        (tab2, 'DR002', ct_df,   'CT Scan',              'patient_id',  'fusion_label'),
        (tab3, 'DR003', us_df,   'Ultrasound',           'patient_id',  'fusion_label'),
        (tab4, 'DR004', fus_df,  'Combined Assessment',  'patient_id',  'fusion_label'),
    ]

    for tab, doc_id, df, mtype, id_col, sev_col in dept_configs:
        with tab:
            if df is None:
                st.warning('No data loaded for this department.')
                continue
            render_dept_tab(doc_id, df, mtype, id_col, sev_col)

    st.markdown('</div>', unsafe_allow_html=True)


def render_dept_tab(doc_id, df, mtype, id_col, sev_col):
    doc = DOCTORS[doc_id]

    # Stats row
    sev_counts = df[sev_col].value_counts() if sev_col in df.columns else {}
    s1,s2,s3,s4 = st.columns(4)
    for col,(lbl,clr) in zip([s1,s2,s3,s4],[
        ('Severe','#FF3B3B'),('Moderate','#FF6B35'),
        ('Mild','#FFB800'),('Normal','#00C48C')
    ]):
        cnt = int(sev_counts.get(lbl, 0))
        with col:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-top:3px solid ' + clr + ';border-radius:10px;'
                'padding:14px;text-align:center;margin-bottom:16px;">'
                '<div style="font-size:28px;font-weight:800;color:' + clr + ';">'
                + str(cnt) + '</div>'
                '<div style="font-size:13px;color:#7A90A8;margin-top:4px;">'
                + lbl + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # Layout
    left, right = st.columns([1, 2.5], gap='large')

    with left:
        st.markdown(
            '<div style="font-size:12px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">'
            'Patient Queue</div>',
            unsafe_allow_html=True
        )
        sev_filter = st.selectbox(
            'Filter',
            ['All','Severe','Moderate','Mild','Normal'],
            key='filter_' + doc_id,
            label_visibility='collapsed'
        )
        filt = df if sev_filter == 'All' \
               else df[df[sev_col] == sev_filter]

        sev_ord = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        filt = filt.sort_values(
            sev_col,
            key=lambda x: x.map(sev_ord)
        ) if sev_col in filt.columns else filt

        for _, row in filt.iterrows():
            pid    = str(row[id_col])
            sev    = str(row.get(sev_col,'Unknown'))
            clr    = SEV_COLOR.get(sev,'#8892A4')
            is_sel = st.session_state.selected_patient == (doc_id, pid)
            is_app = pid in st.session_state.approved
            icon   = '✓ ' if is_app else ''

            if st.button(
                icon + pid + '  ·  ' + sev,
                key='pat_' + doc_id + '_' + pid,
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                st.session_state.selected_patient = (doc_id, pid)
                st.rerun()

    with right:
        sel = st.session_state.selected_patient
        if not sel or sel[0] != doc_id:
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

        sel_pid = sel[1]
        match   = df[df[id_col] == sel_pid]
        if match.empty:
            return

        row = match.iloc[0].to_dict()
        sev = str(row.get(sev_col,'Unknown'))
        clr = SEV_COLOR.get(sev,'#8892A4')
        bg  = SEV_BG.get(sev,'rgba(136,146,164,0.1)')

        render_patient_panel(row, sel_pid, sev, clr, bg, mtype, doc_id)


def render_patient_panel(row, pid, sev, clr, bg, mtype, doc_id):
    doc = DOCTORS[doc_id]

    # Patient header
    urgency = {'Severe':'URGENT','Moderate':'SEMI-URGENT',
               'Mild':'ROUTINE','Normal':'ROUTINE'}.get(sev,'REVIEW')
    urg_clr = {'Severe':'#FF3B3B','Moderate':'#FF6B35',
               'Mild':'#FFB800','Normal':'#00C48C'}.get(sev,'#8892A4')

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
        '<div style="font-size:13px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">'
        'Test Findings</div>',
        unsafe_allow_html=True
    )

    if mtype == 'Lab Report':
        ckd = row.get('ckd_severity','Not tested')
        dia = row.get('diabetes_severity_final','Not tested')
        thy = row.get('thyroid_severity_final','Not tested')
        disease = str(row.get('disease_type','')).lower()

        c1,c2,c3 = st.columns(3)
        for col,(lbl,val) in zip([c1,c2,c3],[
            ('Kidney Function', ckd),
            ('Blood Sugar', dia),
            ('Thyroid Function', thy)
        ]):
            v = str(val) if val and str(val) not in \
                ['None','nan','NaN','Unknown','Not tested'] else 'Not tested'
            with col:
                st.markdown(
                    '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                    'border-radius:10px;padding:14px;margin-bottom:12px;">'
                    '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                    'text-transform:uppercase;letter-spacing:0.06em;'
                    'margin-bottom:6px;">' + lbl + '</div>'
                    '<div style="font-size:16px;font-weight:700;color:#F0F6FF;">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

        # Lab reference ranges
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:4px solid #4A9EFF;border-radius:10px;'
            'padding:12px 18px;margin-bottom:14px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'margin-bottom:6px;text-transform:uppercase;letter-spacing:0.06em;">'
            'Reference Ranges</div>'
            '<div style="font-size:13px;color:#7A90A8;line-height:1.8;">'
            'HbA1c: Normal &lt;5.7%  ·  Pre-diabetic 5.7–6.4%  ·  Diabetic ≥6.5%<br>'
            'eGFR: G1 ≥90  ·  G2 60–89  ·  G3 30–59  ·  G4 15–29  ·  G5 &lt;15<br>'
            'TSH: Normal 0.4–4.0 mIU/L  ·  Free T4: 0.8–1.8 ng/dL'
            '</div></div>',
            unsafe_allow_html=True
        )

    elif mtype == 'CT Scan':
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
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '  ·  AI Confidence: ' + str(round(float(conf)*100,1)) + '%'
            '</div></div>',
            unsafe_allow_html=True
        )

        # GradCAM
        img = CT_IMAGE.get(cls,'')
        if img and os.path.exists(img):
            gc1, gc2 = st.columns(2)
            with gc1:
                st.image(img, caption='CT Scan', use_column_width=True)
            with gc2:
                st.image(img, caption='Grad-CAM Heatmap', use_column_width=True)
            st.markdown(
                '<div style="font-size:12px;color:#4A6080;margin-bottom:12px;">'
                'Highlighted regions show where the AI model focused during classification.'
                '</div>',
                unsafe_allow_html=True
            )

    elif mtype == 'Ultrasound':
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
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '  ·  AI Confidence: ' + str(round(float(conf)*100,1)) + '%'
            '</div></div>',
            unsafe_allow_html=True
        )

        img = US_IMAGE.get(cls,'')
        if img and os.path.exists(img):
            ug1, ug2 = st.columns(2)
            with ug1:
                st.image(img, caption='Ultrasound Scan', use_column_width=True)
            with ug2:
                st.image(img, caption='Grad-CAM Heatmap', use_column_width=True)

    elif mtype == 'Combined Assessment':
        c1,c2,c3,c4 = st.columns(4)
        SCORE_MAP = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
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
                    'border-radius:10px;padding:14px;text-align:center;'
                    'margin-bottom:12px;">'
                    '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                    'text-transform:uppercase;letter-spacing:0.06em;'
                    'margin-bottom:6px;">' + lbl + '</div>'
                    '<div style="font-size:22px;font-weight:800;color:' + vc + ';">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

    # ── RAG Clinical Summary ──────────────────────────────────
    st.markdown(
        '<div style="font-size:13px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:18px 0 12px;">'
        'AI Clinical Summary</div>',
        unsafe_allow_html=True
    )

    rag_key  = str(row.get('rag_class_key',''))
    rag_raw  = rag_data.get(rag_key,{})
    raw_text = rag_raw.get('raw_text','') if isinstance(rag_raw, dict) else str(rag_raw)
    citations= rag_raw.get('citations',[]) if isinstance(rag_raw, dict) else []

    if raw_text:
        parsed = parse_rag_summary(raw_text)

        # Clinical summary
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

        # Key findings
        if parsed['key_findings']:
            findings_html = ''.join([
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
                'Key Findings</div>'
                + findings_html + '</div>',
                unsafe_allow_html=True
            )

        # Recommendations
        if parsed['recommendations']:
            rec_html = ''.join([
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
                'Clinical Recommendations</div>'
                + rec_html + '</div>',
                unsafe_allow_html=True
            )

        # Follow-up + urgency
        fu_col, ug_col = st.columns(2)
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
                    '<div style="font-size:16px;font-weight:800;color:' + uc + ';">'
                    + parsed['urgency'] + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

        # Citations
        if citations:
            cite_html = '  ·  '.join(citations)
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:12px 18px;margin-bottom:16px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                'Guideline References</div>'
                '<div style="font-size:13px;color:#64748B;font-family:monospace;">'
                + cite_html + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
    else:
        st.info('RAG summary not available for this patient class.')

    # ── Doctor Approval ───────────────────────────────────────
    st.markdown(
        '<div style="font-size:13px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:18px 0 10px;">'
        'Doctor Review & Approval</div>',
        unsafe_allow_html=True
    )

    notes = st.text_area(
        'Clinical notes / prescription',
        placeholder='Add prescription, clinical notes, or amendments...',
        height=100,
        key='notes_' + doc_id + '_' + pid,
        label_visibility='collapsed'
    )

    # Patient message preview
    msg = PATIENT_MSG.get(sev, PATIENT_MSG['Normal'])
    if notes:
        msg += '\nDoctor\'s note: ' + notes

    with st.expander('📱  Preview Patient Message'):
        st.markdown(
            '<div style="background:#0A1628;border:1.5px solid #1E3250;'
            'border-radius:12px;padding:20px 24px;">'
            '<div style="font-size:12px;font-weight:600;color:#00C48C;'
            'margin-bottom:12px;letter-spacing:0.08em;">MESSAGE TO PATIENT</div>'
            '<div style="font-size:14px;color:#C8D6E8;line-height:1.8;'
            'white-space:pre-wrap;">' + msg + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown('<br>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button('✅  Approve & Send',
                     key='approve_' + doc_id + '_' + pid,
                     use_container_width=True,
                     type='primary'):
            st.session_state.approved[pid] = {
                'notes':    notes,
                'doctor':   DOCTORS[doc_id]['name'],
                'severity': sev,
                'time':     datetime.now().strftime('%Y-%m-%d %H:%M'),
                'message':  msg,
            }
            st.success('✅  Report approved! Patient message sent.')
            st.balloons()

    with b2:
        if st.button('✏️  Approve with Edits',
                     key='edit_' + doc_id + '_' + pid,
                     use_container_width=True):
            st.session_state.approved[pid] = {
                'notes':    notes,
                'doctor':   DOCTORS[doc_id]['name'],
                'severity': sev,
                'time':     datetime.now().strftime('%Y-%m-%d %H:%M'),
                'message':  msg,
            }
            st.info('Report approved with your amendments.')

    with b3:
        if st.button('❌  Reject',
                     key='reject_' + doc_id + '_' + pid,
                     use_container_width=True):
            st.warning('Report rejected. Patient will be notified.')

    if pid in st.session_state.approved:
        ap = st.session_state.approved[pid]
        st.markdown(
            '<div style="background:rgba(0,196,140,0.1);'
            'border:1.5px solid rgba(0,196,140,0.3);border-radius:10px;'
            'padding:14px 20px;margin-top:12px;">'
            '<div style="font-size:15px;font-weight:700;color:#00C48C;">'
            '✅  Approved by ' + ap['doctor'] + '  ·  ' + ap['time'] + '</div>'
            '<div style="font-size:13px;color:#7A90A8;margin-top:4px;">'
            'Report released and patient message sent successfully.</div>'
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
