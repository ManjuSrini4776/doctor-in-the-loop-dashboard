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
    'glioma':    ('images/ct_glioma_original.jpg',    'images/ct_glioma_gradcam.png'),
    'meningioma':('images/ct_meningioma_original.jpg','images/ct_meningioma_gradcam.png'),
    'pituitary': ('images/ct_pituitary_original.jpg', 'images/ct_pituitary_gradcam.png'),
    'notumor':   ('images/ct_notumor_original.jpg',   'images/ct_notumor_gradcam.png'),
}
US_IMAGE = {
    'Fetal abdomen':('images/us_abdomen_original.png','images/us_abdomen_gradcam.png'),
    'Fetal brain':  ('images/us_brain_original.png',  'images/us_brain_gradcam.png'),
    'Fetal femur':  ('images/us_femur_original.png',  'images/us_femur_gradcam.png'),
    'Fetal thorax': ('images/us_thorax_original.png', 'images/us_thorax_gradcam.png'),
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

def get_patient_message(sev, mtype, row):
    """Generate condition-specific patient message."""
    # Extract condition details
    if mtype == 'Lab Report':
        disease = str(row.get('disease_type','')).lower()
        ckd = str(row.get('ckd_severity',''))
        dia = str(row.get('diabetes_severity_final',''))
        thy = str(row.get('thyroid_severity_final',''))

        if 'ckd' in disease or 'kidney' in disease:
            condition = f'Chronic Kidney Disease ({ckd})'
            if sev == 'Normal':
                detail = ('Your kidney function (eGFR) is within an acceptable range. '
                          'No immediate treatment is required at this stage.')
                action = 'Stay well-hydrated, avoid NSAIDs, and attend your '
                'next kidney function check in 3 months.'
            elif sev == 'Mild':
                detail = ('Your kidney function shows mild reduction. '
                          'This needs regular monitoring to prevent progression.')
                action = ('Follow a low-sodium, low-protein diet as advised. '
                          'Book a follow-up nephrology review in 4 weeks.')
            else:
                detail = ('Your kidney function is significantly reduced. '
                          'Specialist care is needed to prevent further decline.')
                action = ('Please contact your nephrologist immediately. '
                          'Avoid any medications that stress the kidneys.')

        elif 'diabetes' in disease:
            glucose = row.get('glucose','')
            gluc_str = f' (Glucose: {glucose} mg/dL)' \
                       if glucose and str(glucose) not in ['None','nan'] else ''
            condition = f'Diabetes Mellitus{gluc_str}'
            if sev == 'Normal':
                detail = ('Your blood glucose levels are within the target range. '
                          'Your diabetes management is working well.')
                action = ('Continue your current medication and diet plan. '
                          'Check your blood glucose daily and review in 3 months.')
            elif sev == 'Mild':
                detail = ('Your blood glucose is mildly elevated. '
                          'Small adjustments to your treatment may be needed.')
                action = ('Follow the low-sugar diet plan provided. '
                          'Please attend a follow-up in 2 to 4 weeks.')
            else:
                detail = ('Your blood glucose is significantly elevated. '
                          'This requires prompt medical attention.')
                action = ('Please contact your doctor today. '
                          'Do not skip your medication. Avoid sugary foods entirely.')

        elif 'thyroid' in disease:
            tsh = row.get('tsh','')
            tsh_str = f' (TSH: {tsh} mIU/L)' \
                      if tsh and str(tsh) not in ['None','nan'] else ''
            condition = f'Thyroid Disorder{tsh_str}'
            if sev == 'Normal':
                detail = ('Your thyroid hormone levels are within the normal range. '
                          'Your thyroid is functioning well.')
                action = ('Continue your current thyroid medication if prescribed. '
                          'Routine thyroid check in 6 months.')
            elif sev == 'Mild':
                detail = ('Your TSH is mildly elevated, suggesting subclinical '
                          'hypothyroidism. Your Free T4 is still normal.')
                action = ('Your doctor may recommend starting low-dose '
                          'Levothyroxine. Follow up in 4 to 6 weeks.')
            else:
                detail = ('Your thyroid levels indicate overt hypothyroidism '
                          'requiring treatment.')
                action = ('Please begin or adjust your Levothyroxine as prescribed. '
                          'Review in 6 to 8 weeks after starting treatment.')
        else:
            condition = 'Chronic Disease Assessment'
            detail    = 'Your lab results have been reviewed by your doctor.'
            action    = 'Please follow your doctor\'s prescription carefully.'

    elif mtype == 'CT Scan':
        cls      = row.get('ct_predicted_class','')
        conf     = row.get('ct_confidence', 0)
        conf_str = str(round(float(conf)*100,1)) + '%'
        names    = {'notumor':'No Brain Tumour', 'pituitary':'Pituitary Adenoma',
                    'meningioma':'Meningioma',   'glioma':'Glioma'}
        condition = names.get(cls, cls) + f' (AI confidence: {conf_str})'

        if cls == 'notumor':
            detail = ('Your brain CT scan shows no signs of any tumour or '
                      'suspicious lesion. Your scan appears normal.')
            action = 'No further imaging is needed at this time. '
            'Routine follow-up as advised by your neurologist.'
        elif cls == 'pituitary':
            detail = ('A small benign pituitary gland tumour has been identified. '
                      'This type of tumour is usually slow-growing and non-cancerous.')
            action = ('An endocrinology referral has been arranged. '
                      'Hormone level blood tests will be ordered.')
        elif cls == 'meningioma':
            detail = ('A meningioma has been identified. This is typically '
                      'a slow-growing tumour of the brain lining.')
            action = ('A neurosurgery consultation has been arranged. '
                      'Further MRI imaging will be required.')
        else:  # glioma
            detail = ('A glioma has been identified on your brain scan. '
                      'This requires urgent specialist attention.')
            action = ('An urgent oncology referral has been made. '
                      'Please attend the hospital as soon as possible.')

    elif mtype == 'Ultrasound':
        cls   = row.get('predicted_class','')
        conf  = row.get('confidence', 0)
        conf_str = str(round(float(conf)*100,1)) + '%'
        names = {
            'Fetal abdomen':'Fetal Abdomen Scan',
            'Fetal brain':  'Fetal Brain Scan',
            'Fetal femur':  'Fetal Femur Scan',
            'Fetal thorax': 'Fetal Thorax Scan'
        }
        condition = names.get(cls, cls) + f' (AI confidence: {conf_str})'

        if cls == 'Fetal abdomen':
            detail = ('Your fetal abdominal ultrasound shows measurements '
                      'within the normal expected range for gestational age.')
            action = ('Continue your routine antenatal care. '
                      'Next scan as per your scheduled appointment.')
        elif cls == 'Fetal femur':
            detail = ('Your baby\'s femur (thigh bone) length is within the '
                      'normal range, indicating healthy fetal growth.')
            action = ('No concerns at this stage. Continue your regular '
                      'antenatal check-ups.')
        elif cls == 'Fetal thorax':
            detail = ('The fetal thorax (chest) plane has been assessed. '
                      'A detailed cardiac and lung evaluation is recommended.')
            action = ('A fetal echocardiography has been recommended. '
                      'Please attend your specialist appointment within 7 days.')
        else:  # brain
            detail = ('The fetal brain scan requires further detailed evaluation. '
                      'An anomaly scan has been recommended by your doctor.')
            action = ('Please attend the fetal medicine unit within the next '
                      '3 to 5 days for a detailed neurosonography scan.')

    elif mtype == 'Combined Assessment':
        fusion_sev = row.get('fusion_label', sev)
        condition  = 'Multimodal Clinical Assessment (Lab + CT + Ultrasound)'
        detail     = (f'Your combined assessment across all three tests shows '
                      f'{fusion_sev.lower()} overall findings. '
                      f'Each test result has been reviewed individually.')
        action     = ('Please follow your doctor\'s specific instructions '
                      'for each component of your assessment.')
    else:
        condition = 'Medical Assessment'
        detail    = 'Your results have been reviewed by your doctor.'
        action    = 'Please follow your doctor\'s prescription carefully.'

    # Severity-specific urgency line
    urgency_line = {
        'Normal':   'No immediate hospital visit is required.',
        'Mild':     'No emergency — but please book your follow-up appointment soon.',
        'Moderate': 'Please do not delay your follow-up appointment.',
        'Severe':   'Please contact the hospital or your doctor today without delay.',
    }.get(sev, '')

    return (
        f"Dear Patient,\n\n"
        f"Your test results have been reviewed and approved by your doctor.\n\n"
        f"Condition: {condition}\n\n"
        f"{detail}\n\n"
        f"Next Steps: {action}\n\n"
        f"{urgency_line}\n\n"
        f"Regards,\nMedAI Clinical System"
    )


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
    for col,(lbl,clr,bg_clr) in zip([s1,s2,s3,s4],[
        ('Severe',   '#FF3B3B','rgba(255,59,59,0.08)'),
        ('Moderate', '#FF6B35','rgba(255,107,53,0.08)'),
        ('Mild',     '#FFB800','rgba(255,184,0,0.08)'),
        ('Normal',   '#00C48C','rgba(0,196,140,0.08)'),
    ]):
        cnt = int(sev_counts.get(lbl, 0))
        with col:
            st.markdown(
                '<div style="background:' + bg_clr + ';'
                'border:2px solid ' + clr + '44;'
                'border-top:4px solid ' + clr + ';border-radius:12px;'
                'padding:16px;text-align:center;margin-bottom:16px;">'
                '<div style="font-size:36px;font-weight:800;color:' + clr + ';'
                'line-height:1;">' + str(cnt) + '</div>'
                '<div style="font-size:13px;color:' + clr + ';margin-top:6px;'
                'font-weight:600;opacity:0.8;">' + lbl + '</div>'
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

        # Patient message — condition specific
        pat_msg = get_patient_message(sev, mtype, row)
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
    ckd     = str(row.get('ckd_severity','Not tested'))
    dia     = str(row.get('diabetes_severity_final','Not tested'))
    thy     = str(row.get('thyroid_severity_final','Not tested'))
    egfr    = row.get('egfr', None)
    hba1c   = row.get('hba1c', None)
    glucose = row.get('glucose', None)
    tsh     = row.get('tsh', None)
    free_t4 = row.get('free_t4', None)
    disease = str(row.get('disease_type','')).lower()

    # Clean None/nan
    def clean(v):
        return 'Not tested' if str(v) in ['None','nan','NaN','Unknown','Not tested',''] else str(v)
    ckd = clean(ckd)
    dia = clean(dia)
    thy = clean(thy)

    # ── Patient Values row ────────────────────────────────────
    c1,c2,c3 = st.columns(3)
    for col,(lbl,val) in zip([c1,c2,c3],[
        ('Kidney Function', ckd),
        ('Blood Sugar',     dia),
        ('Thyroid Function',thy)
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

    # ── Patient vs Guideline comparison table ─────────────────
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.08em;'
        'margin:4px 0 10px;">Patient Values vs Clinical Guidelines</div>',
        unsafe_allow_html=True
    )

    # Build comparison rows based on disease
    def status_badge(status):
        cfg = {
            'Normal':   ('#00C48C','rgba(0,196,140,0.12)','✓ Within range'),
            'Abnormal': ('#FF3B3B','rgba(255,59,59,0.12)', '✗ Out of range'),
            'Borderline':('#FFB800','rgba(255,184,0,0.12)','⚠ Borderline'),
            'N/A':      ('#4A6080','rgba(74,96,128,0.12)', '— Not tested'),
        }.get(status, ('#4A6080','rgba(74,96,128,0.12)','— N/A'))
        return (
            '<span style="background:' + cfg[1] + ';color:' + cfg[0] + ';'
            'font-size:12px;font-weight:600;padding:3px 10px;'
            'border-radius:20px;">' + cfg[2] + '</span>'
        )

    def fmt_val(v):
        if v is None or str(v) in ['None','nan','NaN']:
            return '—'
        try:
            return str(round(float(v), 2))
        except Exception:
            return str(v)

    # Determine comparison rows
    if 'ckd' in disease or 'kidney' in disease:
        egfr_val = fmt_val(egfr)

        # eGFR → KDIGO stage label + clinical interpretation
        try:
            egfr_f = float(egfr) if egfr is not None \
                     and str(egfr) not in ['None','nan'] else None
        except Exception:
            egfr_f = None

        if egfr_f is not None:
            if egfr_f >= 90:
                egfr_stage  = 'G1 (≥90) — Normal or High'
                egfr_status = 'Normal'
            elif egfr_f >= 60:
                egfr_stage  = 'G2 (60–89) — Mildly Reduced'
                egfr_status = 'Normal'      # G1+G2 = Normal clinically
            elif egfr_f >= 45:
                egfr_stage  = 'G3a (45–59) — Mildly-Moderately Reduced'
                egfr_status = 'Borderline'
            elif egfr_f >= 30:
                egfr_stage  = 'G3b (30–44) — Moderately-Severely Reduced'
                egfr_status = 'Abnormal'
            elif egfr_f >= 15:
                egfr_stage  = 'G4 (15–29) — Severely Reduced'
                egfr_status = 'Abnormal'
            else:
                egfr_stage  = 'G5 (<15) — Kidney Failure'
                egfr_status = 'Abnormal'
        else:
            egfr_stage  = 'Not measured'
            egfr_status = 'N/A'

        # Clinical severity from label
        sev_status = {
            'Normal':'Normal', 'Mild':'Borderline',
            'Moderate':'Abnormal', 'Severe':'Abnormal'
        }.get(sev, 'N/A')

        rows = [
            ('eGFR Value',
             egfr_val + ' mL/min/1.73m²' if egfr_val != '—' else '—',
             'G1: ≥90  ·  G2: 60–89  ·  G3a: 45–59  ·  G3b: 30–44  ·  G4: 15–29  ·  G5: <15',
             egfr_status),
            ('KDIGO Stage',
             egfr_stage,
             'G1–G2 = Normal clinically  ·  G3a = Mild  ·  G3b = Moderate  ·  G4–G5 = Severe',
             egfr_status),
            ('Clinical Severity',
             sev,
             'Based on eGFR + albuminuria + symptoms (KDIGO 2022)',
             sev_status),
            ('BP Target',
             '—',
             '<130/80 mmHg  ·  ACE inhibitor if proteinuria present',
             'N/A'),
        ]
        source = 'KDIGO 2022 Clinical Practice Guideline for CKD'

    elif 'diabetes' in disease:
        gluc_val = fmt_val(glucose)
        # Glucose status based on ADA thresholds
        try:
            gluc_f   = float(glucose) if glucose is not None \
                       and str(glucose) not in ['None','nan'] else None
            g_status = 'Normal'     if gluc_f and gluc_f < 100 \
                       else 'Borderline' if gluc_f and gluc_f < 126 \
                       else 'Abnormal'   if gluc_f else 'N/A'
        except Exception:
            gluc_f   = None
            g_status = 'N/A'

        # Severity status
        d_status = 'Normal'   if dia == 'Mild'   else \
                   'Abnormal' if dia == 'Severe'  else \
                   'Normal'   if dia == 'Normal'  else 'N/A'

        rows = [
            ('Glucose (Fasting)',
             gluc_val + ' mg/dL' if gluc_val != '—' else '—',
             'Normal: <100 mg/dL · Pre-diabetic: 100–125 · Diabetic: ≥126',
             g_status),
            ('Diabetes Severity',
             dia,
             'Normal: <100 mg/dL · Mild: 126–180 · Severe: >180 mg/dL',
             d_status),
            ('HbA1c Target',
             'Not available in MIMIC-IV',
             'Target: <7.0% (most adults) · <8.0% (elderly)',
             'N/A'),
            ('Monitoring',
             '—',
             'Self-monitoring blood glucose daily · HbA1c every 3 months',
             'N/A'),
        ]
        source = 'ADA Standards of Medical Care in Diabetes 2024'

    elif 'thyroid' in disease:
        tsh_val = fmt_val(tsh)
        t4_val  = fmt_val(free_t4)

        try:
            tsh_f = float(tsh) if tsh is not None \
                    and str(tsh) not in ['None','nan'] else None
            # 0.4-4.0 = Normal, 4.1-10.0 = Subclinical (Borderline), >10 = Overt (Abnormal)
            t_status = 'Normal'     if tsh_f and 0.4 <= tsh_f <= 4.0 \
                       else 'Borderline' if tsh_f and 4.0 < tsh_f <= 10.0 \
                       else 'Abnormal'   if tsh_f and tsh_f > 10.0 \
                       else 'N/A'
            tsh_interp = 'Normal (Euthyroid)'           if tsh_f and 0.4 <= tsh_f <= 4.0 \
                         else 'Subclinical Hypothyroid'  if tsh_f and 4.0 < tsh_f <= 10.0 \
                         else 'Overt Hypothyroid'        if tsh_f and tsh_f > 10.0 \
                         else '—'
        except Exception:
            tsh_f      = None
            t_status   = 'N/A'
            tsh_interp = '—'

        try:
            t4_f = float(free_t4) if free_t4 is not None \
                   and str(free_t4) not in ['None','nan'] else None
            # T4 within 0.8-1.8 = Normal
            t4_status = 'Normal'     if t4_f and 0.8 <= t4_f <= 1.8 \
                        else 'Abnormal' if t4_f else 'N/A'
            t4_interp = 'Normal'     if t4_f and 0.8 <= t4_f <= 1.8 \
                        else 'Low — Hypothyroid' if t4_f and t4_f < 0.8 \
                        else 'High — Hyperthyroid' if t4_f else '—'
        except Exception:
            t4_f      = None
            t4_status = 'N/A'
            t4_interp = '—'

        # Overall thyroid status
        # Subclinical (TSH high, T4 normal) = Mild = Borderline clinically
        if tsh_f and tsh_f > 10.0:
            thy_status = 'Abnormal'    # Overt hypothyroid
        elif tsh_f and tsh_f > 4.0:
            thy_status = 'Borderline'  # Subclinical = Mild
        elif tsh_f:
            thy_status = 'Normal'
        else:
            thy_status = 'N/A'

        rows = [
            ('TSH Level',
             tsh_val + ' mIU/L' if tsh_val != '—' else '—',
             'Normal: 0.4–4.0  ·  Subclinical: 4.1–10.0  ·  Overt Hypothyroid: >10.0',
             t_status),
            ('TSH Interpretation',
             tsh_interp,
             'Subclinical = TSH high but T4 still normal → monitor or treat if symptomatic',
             t_status),
            ('Free T4',
             t4_val + ' ng/dL (' + t4_interp + ')' if t4_val != '—' else 'Not measured',
             'Normal: 0.8–1.8 ng/dL  ·  Low T4 = Overt Hypothyroidism',
             t4_status),
            ('Clinical Severity',
             thy + ' — ' + ('Subclinical Hypothyroid' if thy=='Mild' and tsh_f and tsh_f<=10 else thy),
             'Mild = Subclinical (TSH↑, T4 normal)  ·  Severe = Overt (TSH↑↑, T4 low)',
             thy_status),
            ('Treatment Threshold',
             '—',
             'Treat if TSH >10 mIU/L  ·  Or if TSH 4–10 with symptoms',
             'N/A'),
        ]
        source = 'ATA/AACE Clinical Practice Guidelines for Hypothyroidism 2023'

    else:
        rows = [
            ('HbA1c',  '—', 'Normal <5.7% · Pre-diabetic 5.7–6.4% · Diabetic ≥6.5%', 'N/A'),
            ('eGFR',   '—', 'G1 ≥90 · G2 60–89 · G3 30–59 · G4 15–29 · G5 <15',     'N/A'),
            ('TSH',    '—', 'Normal 0.4–4.0 mIU/L · Free T4: 0.8–1.8 ng/dL',          'N/A'),
        ]
        source = 'WHO / Standard Clinical Guidelines'

    # Render table
    header = (
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;border-bottom:2px solid #263A55;padding-bottom:8px;margin-bottom:4px;">'
        '<div style="font-size:11px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;">Parameter</div>'
        '<div style="font-size:11px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;">Patient Value</div>'
        '<div style="font-size:11px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;">Guideline Range</div>'
        '<div style="font-size:11px;font-weight:700;color:#4A6080;'
        'text-transform:uppercase;letter-spacing:0.06em;">Status</div>'
        '</div>'
    )
    body = ''
    for param, pat_val, guide_range, status in rows:
        pv_clr = {
            'Normal':'#00C48C','Abnormal':'#FF3B3B',
            'Borderline':'#FFB800','N/A':'#4A6080'
        }.get(status,'#4A6080')
        body += (
            '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
            'gap:0;padding:10px 0;border-bottom:1px solid #1E3250;align-items:center;">'
            '<div style="font-size:13px;font-weight:600;color:#E8EDF5;">'
            + param + '</div>'
            '<div style="font-size:13px;font-weight:700;color:' + pv_clr + ';">'
            + pat_val + '</div>'
            '<div style="font-size:12px;color:#7A90A8;line-height:1.5;">'
            + guide_range + '</div>'
            '<div>' + status_badge(status) + '</div>'
            '</div>'
        )

    st.markdown(
        '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
        'border-left:4px solid #4A9EFF;border-radius:12px;'
        'padding:16px 20px;margin-bottom:14px;">'
        + header + body +
        '<div style="font-size:11px;color:#334155;margin-top:10px;'
        'font-style:italic;">Source: ' + source + '</div>'
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
    img_tuple = CT_IMAGE.get(str(cls),('',''))
    orig_path = img_tuple[0] if isinstance(img_tuple,tuple) else ''
    grad_path = img_tuple[1] if isinstance(img_tuple,tuple) else ''
    if orig_path and os.path.exists(orig_path):
        gc1,gc2 = st.columns(2)
        with gc1:
            st.markdown('<div style="font-size:11px;font-weight:600;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original CT Scan</div>',unsafe_allow_html=True)
            st.image(orig_path, use_column_width=True)
        with gc2:
            st.markdown('<div style="font-size:11px;font-weight:600;color:#A78BFA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if grad_path and os.path.exists(grad_path):
                st.image(grad_path, use_column_width=True)
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
    img_tuple = US_IMAGE.get(str(cls),('',''))
    orig_path = img_tuple[0] if isinstance(img_tuple,tuple) else ''
    grad_path = img_tuple[1] if isinstance(img_tuple,tuple) else ''
    if orig_path and os.path.exists(orig_path):
        ug1,ug2 = st.columns(2)
        with ug1:
            st.markdown('<div style="font-size:11px;font-weight:600;color:#34D399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original Ultrasound</div>',unsafe_allow_html=True)
            st.image(orig_path, use_column_width=True)
        with ug2:
            st.markdown('<div style="font-size:11px;font-weight:600;color:#A78BFA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if grad_path and os.path.exists(grad_path):
                st.image(grad_path, use_column_width=True)


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
