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

# ── BRIGHT COLORFUL THEME ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#060E1A!important;color:#E8EDF5!important;}
.stApp{background:#060E1A!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stTextInput>div>div>input{background:#0F1E33!important;color:#F0F6FF!important;border:2px solid #1E3A5F!important;border-radius:10px!important;font-size:16px!important;padding:10px 16px!important;}
.stSelectbox>div>div{background:#0F1E33!important;color:#F0F6FF!important;border:2px solid #1E3A5F!important;border-radius:10px!important;font-size:15px!important;}
.stTextArea textarea{background:#0F1E33!important;color:#F0F6FF!important;border:2px solid #1E3A5F!important;border-radius:10px!important;font-size:14px!important;}
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:700!important;font-size:15px!important;border-radius:10px!important;padding:11px 22px!important;transition:all 0.2s!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2563EB,#1D4ED8)!important;border:none!important;color:white!important;box-shadow:0 4px 15px rgba(37,99,235,0.4)!important;}
.stButton>button[kind="secondary"]{background:#0F1E33!important;border:2px solid #1E3A5F!important;color:#94A3B8!important;}
.stButton>button[kind="secondary"]:hover{border-color:#2563EB!important;color:#60A5FA!important;}
.stTabs [data-baseweb="tab-list"]{background:#080F1C!important;border-bottom:2px solid #1E3A5F!important;padding:0 8px!important;}
.stTabs [data-baseweb="tab"]{font-size:15px!important;font-weight:600!important;color:#4A6080!important;padding:14px 22px!important;}
.stTabs [aria-selected="true"]{color:#60A5FA!important;border-bottom:3px solid #2563EB!important;background:transparent!important;}
hr{border-color:#1E3A5F!important;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
SEV_COLOR = {
    'Normal':  '#00E5A0', 'Mild':    '#FFD000',
    'Moderate':'#FF7A35', 'Severe':  '#FF3B5C', 'Unknown':'#6B7A99'
}
SEV_BG = {
    'Normal':  'rgba(0,229,160,0.1)',  'Mild':    'rgba(255,208,0,0.1)',
    'Moderate':'rgba(255,122,53,0.1)', 'Severe':  'rgba(255,59,92,0.1)',
    'Unknown': 'rgba(107,122,153,0.1)'
}
SEV_GRAD = {
    'Normal':  'linear-gradient(135deg,rgba(0,229,160,0.2),rgba(0,229,160,0.05))',
    'Mild':    'linear-gradient(135deg,rgba(255,208,0,0.2),rgba(255,208,0,0.05))',
    'Moderate':'linear-gradient(135deg,rgba(255,122,53,0.2),rgba(255,122,53,0.05))',
    'Severe':  'linear-gradient(135deg,rgba(255,59,92,0.2),rgba(255,59,92,0.05))',
    'Unknown': 'linear-gradient(135deg,rgba(107,122,153,0.15),rgba(107,122,153,0.05))',
}
SCORE_MAP = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
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
    'Fetal abdomen':'Fetal Abdomen — Normal','Fetal brain':'Fetal Brain Plane',
    'Fetal femur':'Fetal Femur — Normal Growth','Fetal thorax':'Fetal Thorax Plane'
}
US_DESC = {
    'Fetal abdomen':'Abdominal measurements within expected range for gestational age.',
    'Fetal brain':  'Neurosonography plane. Detailed anomaly scan recommended.',
    'Fetal femur':  'Femur length within normal range. Fetal growth on track.',
    'Fetal thorax': 'Thoracic plane. Cardiac and pulmonary assessment indicated.'
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
DOCTORS = {
    'DR001':{'name':'Dr. Priya Sharma', 'dept':'Internal Medicine','specialty':'Nephrology & Chronic Disease','color':'#60A5FA','password':'1234','mtype':'Lab Report'},
    'DR002':{'name':'Dr. Arjun Mehta',  'dept':'Neurology',        'specialty':'Neuro-Oncology',             'color':'#C084FC','password':'1234','mtype':'CT Scan'},
    'DR003':{'name':'Dr. Kavitha Rajan','dept':'Obstetrics',        'specialty':'Fetal Medicine',             'color':'#34D399','password':'1234','mtype':'Ultrasound'},
    'DR004':{'name':'Dr. Suresh Kumar', 'dept':'General Medicine',  'specialty':'Multimodal Assessment',      'color':'#FBBF24','password':'1234','mtype':'Combined Assessment'},
}


# ── DATA LOADING ──────────────────────────────────────────────
def load_all():
    def find(name):
        for p in [f'data/{name}', name]:
            if os.path.exists(p): return p
        return None

    def load_csv(name):
        p = find(name)
        if not p: return None
        df = pd.read_csv(p)
        # Force numeric columns
        for col in ['egfr','hba1c','glucose','tsh','free_t4',
                    'ct_confidence','confidence','lab_score',
                    'ct_score','us_score','fusion_score']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        # Replace ALL NaN with None so row.to_dict() gives Python None not numpy nan
        df = df.where(pd.notnull(df), None)
        return df

    lab=ct=us=fus=None; rag={}
    lab=load_csv('lab_data.csv')
    if lab is not None:
        lab['final_severity_label']=lab['final_severity_label'].replace('Stable','Normal')
    ct =load_csv('ct_data.csv')
    us =load_csv('us_data.csv')
    fus=load_csv('fusion_data.csv')

    p=find('rag_summaries.json')
    if p:
        with open(p) as f: rag=json.load(f)
    return lab,ct,us,fus,rag

lab_df,ct_df,us_df,fus_df,rag_data = load_all()


# ── SESSION STATE ─────────────────────────────────────────────
for k,v in {'logged_in':False,'active_doctor':None,'selected':{},'decisions':{}}.items():
    if k not in st.session_state: st.session_state[k]=v


# ── HELPERS ───────────────────────────────────────────────────
def get_num(row, key):
    """Safely extract numeric value from row dict, returns None for NaN/null."""
    v = row.get(key)
    # None check
    if v is None:
        return None
    # String nan check
    if str(v).strip().lower() in ('nan', 'none', 'null', '', 'na'):
        return None
    # Numeric conversion
    try:
        f = float(v)
        # NaN check using comparison (works for all float NaN types)
        if f != f:
            return None
        return f
    except (TypeError, ValueError):
        return None

def fmt(v, unit=''):
    if v is None: return '—'
    return str(round(v,2)) + (' '+unit if unit else '')

def sev_badge(status):
    cfg = {
        'Normal':    ('#00E5A0','rgba(0,229,160,0.15)',   '✓ Normal'),
        'Abnormal':  ('#FF3B5C','rgba(255,59,92,0.15)',   '✗ Abnormal'),
        'Borderline':('#FFD000','rgba(255,208,0,0.15)',   '⚠ Borderline'),
        'N/A':       ('#6B7A99','rgba(107,122,153,0.15)', '— Not tested'),
    }.get(status, ('#6B7A99','rgba(107,122,153,0.15)','—'))
    return (f'<span style="background:{cfg[1]};color:{cfg[0]};font-size:12px;'
            f'font-weight:700;padding:4px 12px;border-radius:20px;">{cfg[2]}</span>')

def parse_rag(raw_text):
    s={'clinical_summary':'','key_findings':[],'recommendations':[],'followup':'','urgency':''}
    cur=None
    for line in raw_text.split('\n'):
        line=line.strip()
        if not line: continue
        lu=line.upper()
        if 'CLINICAL SUMMARY' in lu: cur='s'
        elif 'KEY FINDINGS' in lu: cur='f'
        elif 'RECOMMENDATION' in lu: cur='r'
        elif 'FOLLOW' in lu and 'PLAN' in lu: cur='fu'
        elif lu.startswith('URGENCY'): s['urgency']=line.split(':')[-1].strip(); cur=None
        elif cur=='s' and not lu.startswith('CLINICAL'): s['clinical_summary']+=line+' '
        elif cur=='f' and line.startswith('•'): s['key_findings'].append(line[1:].strip())
        elif cur=='r' and line.startswith('•'): s['recommendations'].append(line[1:].strip())
        elif cur=='fu' and not lu.startswith('FOLLOW'): s['followup']+=line+' '
    return s


# ── MM RAG: build combined summary for all 3 modalities ───────
def get_mm_rag_summary(row):
    """Combine RAG summaries from all 3 modalities for MM patients."""
    SCORE_TO_SEV = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}

    # Get each modality's severity
    lab_s   = get_num(row,'lab_score')
    ct_s    = get_num(row,'ct_score')
    us_s    = get_num(row,'us_score')
    fus_sev = str(row.get('fusion_label', row.get('_sev','Normal')))

    lab_sev = SCORE_TO_SEV.get(int(lab_s),'Normal') if lab_s is not None else 'Unknown'
    ct_sev  = SCORE_TO_SEV.get(int(ct_s), 'Normal') if ct_s  is not None else 'Unknown'
    us_sev  = SCORE_TO_SEV.get(int(us_s), 'Normal') if us_s  is not None else 'Unknown'

    # Get keys for each modality
    ckd = str(row.get('ckd_severity',''))
    dia = str(row.get('diabetes_severity_final',''))
    thy = str(row.get('thyroid_severity_final',''))

    disease = 'ckd' if ckd and ckd not in ['Not tested','nan','None'] \
              else 'diabetes' if dia and dia not in ['Not tested','nan','None'] \
              else 'thyroid'
    lab_key = f'lab_{disease}_{lab_sev.lower()}'

    ct_cls  = str(row.get('ct_predicted_class','notumor'))
    ct_key  = f'ct_{ct_cls}'

    us_cls  = str(row.get('us_predicted_class', row.get('predicted_class','Fetal abdomen')))
    us_key  = 'us_brain'   if 'brain'   in us_cls.lower() else \
              'us_thorax'  if 'thorax'  in us_cls.lower() else \
              'us_femur'   if 'femur'   in us_cls.lower() else 'us_abdomen'

    # Pull each RAG entry
    def get_section(key, section):
        entry = rag_data.get(key,{})
        raw   = entry.get('raw_text','') if isinstance(entry,dict) else ''
        parsed= parse_rag(raw)
        return parsed.get(section,[]) if isinstance(parsed.get(section),list) \
               else [parsed.get(section,'')] if parsed.get(section) else []

    # Build unified summary
    lab_summary = rag_data.get(lab_key,{}).get('raw_text','') if lab_key in rag_data else ''
    ct_summary  = rag_data.get(ct_key,{}).get('raw_text','')  if ct_key  in rag_data else ''
    us_summary  = rag_data.get(us_key,{}).get('raw_text','')  if us_key  in rag_data else ''

    lab_parsed  = parse_rag(lab_summary) if lab_summary else {}
    ct_parsed   = parse_rag(ct_summary)  if ct_summary  else {}
    us_parsed   = parse_rag(us_summary)  if us_summary  else {}

    # Merge all findings and recommendations
    all_findings = []
    all_recs     = []
    citations    = []

    if lab_parsed.get('key_findings'):
        all_findings.append(f'[Lab — {lab_sev}]')
        all_findings.extend(lab_parsed['key_findings'][:2])
    if ct_parsed.get('key_findings'):
        all_findings.append(f'[CT — {CT_NAMES.get(ct_cls,ct_cls)} — {ct_sev}]')
        all_findings.extend(ct_parsed['key_findings'][:2])
    if us_parsed.get('key_findings'):
        all_findings.append(f'[Ultrasound — {US_NAMES.get(us_cls,us_cls)} — {us_sev}]')
        us_parsed['key_findings'][:2]
        all_findings.extend(us_parsed['key_findings'][:2])

    if lab_parsed.get('recommendations'):
        all_recs.extend(lab_parsed['recommendations'][:2])
    if ct_parsed.get('recommendations'):
        all_recs.extend(ct_parsed['recommendations'][:2])
    if us_parsed.get('recommendations'):
        all_recs.extend(us_parsed['recommendations'][:2])

    for key in [lab_key, ct_key, us_key]:
        entry = rag_data.get(key,{})
        if isinstance(entry,dict):
            citations.extend(entry.get('citations',[]))

    # Unified clinical summary
    urgency_map = {'Normal':'Routine','Mild':'Routine','Moderate':'Semi-urgent','Severe':'Urgent'}
    urgency     = urgency_map.get(fus_sev,'Routine')

    clinical_summary = (
        f"This patient has undergone a multimodal assessment covering laboratory tests "
        f"({lab_sev} severity), CT brain imaging ({CT_NAMES.get(ct_cls,ct_cls)} — {ct_sev}), "
        f"and obstetric ultrasound ({US_NAMES.get(us_cls,us_cls)} — {us_sev}). "
        f"The combined MAX-fusion severity is {fus_sev}, indicating {urgency.lower()} clinical priority."
    )

    followup_map = {
        'Normal':   'Routine review in 3 months for all modalities.',
        'Mild':     'Follow-up within 4 weeks. Monitor all three conditions.',
        'Moderate': 'Specialist review within 7 days for the most severe finding.',
        'Severe':   'Immediate specialist referral for the most critical finding.',
    }

    return {
        'clinical_summary': clinical_summary,
        'key_findings':     all_findings,
        'recommendations':  list(dict.fromkeys(all_recs)),  # deduplicate
        'followup':         followup_map.get(fus_sev,'Follow-up as clinically indicated.'),
        'urgency':          urgency,
        'citations':        list(dict.fromkeys(citations)),
    }


# ── PATIENT MESSAGE ───────────────────────────────────────────
def get_patient_message(sev, mtype, row):
    def safe_num(key):
        v=row.get(key)
        if v is None: return None
        try:
            import math
            f=float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        except (TypeError, ValueError):
            return None

    if mtype=='Lab Report':
        disease=str(row.get('disease_type','')).lower()
        ckd=str(row.get('ckd_severity',''))
        dia=str(row.get('diabetes_severity_final',''))
        thy=str(row.get('thyroid_severity_final',''))

        if 'ckd' in disease or 'kidney' in disease:
            egfr_v=safe_num('egfr')
            egfr_str=f' (eGFR: {round(egfr_v,1)} mL/min)' if egfr_v else ''
            condition=f'Chronic Kidney Disease — {ckd}{egfr_str}'
            if sev=='Normal':
                detail='Your kidney function is within an acceptable range. No treatment is needed at this stage.'
                action='Stay well-hydrated, avoid NSAIDs, and attend your kidney function check in 3 months.'
            elif sev=='Mild':
                detail='Your kidney function shows mild reduction and needs regular monitoring to prevent progression.'
                action='Follow a low-sodium, low-protein diet. Book a nephrology follow-up within 4 weeks.'
            else:
                detail='Your kidney function is significantly reduced and requires specialist attention.'
                action='Please contact your nephrologist immediately. Avoid all medications that stress the kidneys.'

        elif 'diabetes' in disease:
            gluc_v=safe_num('glucose')
            gluc_str=f' (Glucose: {round(gluc_v,1)} mg/dL)' if gluc_v else ''
            condition=f'Diabetes Mellitus{gluc_str}'
            if sev=='Normal':
                detail='Your blood glucose levels are well controlled and within the target range.'
                action='Continue your current medication and diet plan. Check blood glucose daily. Review in 3 months.'
            elif sev=='Mild':
                detail='Your blood glucose is mildly elevated and needs closer monitoring.'
                action='Follow the low-sugar diet plan. Please attend a follow-up appointment in 2 to 4 weeks.'
            else:
                gluc_display=f'{round(gluc_v,1)} mg/dL' if gluc_v else 'elevated'
                detail=f'Your blood glucose is significantly elevated ({gluc_display}) and requires prompt attention.'
                action='Please contact your doctor today. Do not skip your medication. Avoid all sugary foods.'

        elif 'thyroid' in disease:
            tsh_v=safe_num('tsh')
            tsh_str=f' (TSH: {round(tsh_v,2)} mIU/L)' if tsh_v else ''
            condition=f'Thyroid Disorder{tsh_str}'
            if sev=='Normal':
                detail='Your thyroid hormone levels are within the normal range. Your thyroid is functioning well.'
                action='Continue your current thyroid medication if prescribed. Routine thyroid check in 6 months.'
            elif sev=='Mild':
                detail='Your TSH is mildly elevated (subclinical hypothyroidism). Your Free T4 is still normal.'
                action='Your doctor may recommend low-dose Levothyroxine. Follow up in 4 to 6 weeks.'
            else:
                detail='Your thyroid levels indicate overt hypothyroidism requiring prompt treatment.'
                action='Please begin or adjust your Levothyroxine as prescribed. Review in 6 to 8 weeks.'
        else:
            condition='Chronic Disease Assessment'
            detail='Your lab results have been reviewed by your doctor.'
            action="Please follow your doctor's prescription carefully."

    elif mtype=='CT Scan':
        cls=row.get('ct_predicted_class','')
        conf=row.get('ct_confidence',0)
        names={'notumor':'No Brain Tumour','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}
        condition=names.get(cls,cls)+f' (AI confidence: {round(float(conf)*100,1)}%)'
        if cls=='notumor':
            detail='Your brain CT scan shows no signs of any tumour or suspicious lesion. Your scan is normal.'
            action='No further imaging is needed at this time. Routine follow-up as advised by your neurologist.'
        elif cls=='pituitary':
            detail='A small benign pituitary gland tumour has been identified. This type is usually slow-growing.'
            action='An endocrinology referral has been arranged. Hormone level blood tests will be ordered.'
        elif cls=='meningioma':
            detail='A meningioma has been identified — typically a slow-growing tumour of the brain lining.'
            action='A neurosurgery consultation has been arranged. Further MRI imaging will be required.'
        else:
            detail='A glioma has been identified on your brain scan. This requires urgent specialist attention.'
            action='An urgent oncology referral has been made. Please attend the hospital as soon as possible.'

    elif mtype=='Ultrasound':
        cls=row.get('predicted_class','')
        conf=row.get('confidence',0)
        names={'Fetal abdomen':'Fetal Abdomen Scan','Fetal brain':'Fetal Brain Scan','Fetal femur':'Fetal Femur Scan','Fetal thorax':'Fetal Thorax Scan'}
        condition=names.get(cls,cls)+f' (AI confidence: {round(float(conf)*100,1)}%)'
        if cls=='Fetal abdomen':
            detail='Your fetal abdominal measurements are within the normal expected range for gestational age.'
            action='Continue routine antenatal care. Next scan as per your scheduled appointment.'
        elif cls=='Fetal femur':
            detail="Your baby's femur length is within the normal range, indicating healthy fetal growth."
            action='No concerns at this stage. Continue your regular antenatal check-ups.'
        elif cls=='Fetal thorax':
            detail='The fetal thorax (chest) plane has been assessed. A detailed cardiac evaluation is recommended.'
            action='A fetal echocardiography has been recommended. Please attend within 7 days.'
        else:
            detail='The fetal brain scan requires further detailed evaluation. An anomaly scan has been recommended.'
            action='Please attend the fetal medicine unit within 3 to 5 days for a detailed neurosonography.'

    elif mtype=='Combined Assessment':
        fus_sev=row.get('fusion_label',sev)
        ct_cls=row.get('ct_predicted_class','')
        us_cls=row.get('us_predicted_class',row.get('predicted_class',''))
        condition=f'Multimodal Assessment — Lab + {CT_NAMES.get(ct_cls,"CT")} + {US_NAMES.get(us_cls,"Ultrasound")}'
        detail=(f'Your combined assessment shows {fus_sev.lower()} overall findings. '
                f'All three tests — laboratory, CT scan and ultrasound — have been individually reviewed.')
        action="Please follow your doctor's specific instructions for each component of your assessment."
    else:
        condition='Medical Assessment'
        detail='Your results have been reviewed by your doctor.'
        action="Please follow your doctor's prescription carefully."

    urgency_line={
        'Normal':  'No immediate hospital visit is required.',
        'Mild':    'No emergency — but please book your follow-up appointment soon.',
        'Moderate':'Please do not delay your follow-up appointment.',
        'Severe':  'Please contact the hospital or your doctor today without delay.',
    }.get(sev,'')

    return (
        f"Dear Patient,\n\n"
        f"Your test results have been reviewed and approved by your doctor.\n\n"
        f"Condition: {condition}\n\n"
        f"{detail}\n\n"
        f"Next Steps: {action}\n\n"
        f"{urgency_line}\n\n"
        f"Regards,\nMedAI Clinical System"
    )


# ── LOGIN ─────────────────────────────────────────────────────
def render_login():
    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown('<div style="margin-top:80px;">', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;margin-bottom:36px;">'
            '<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);'
            'width:64px;height:64px;border-radius:18px;display:flex;'
            'align-items:center;justify-content:center;font-size:32px;'
            'margin:0 auto 16px;box-shadow:0 8px 32px rgba(37,99,235,0.5);">🏥</div>'
            '<div style="font-size:30px;font-weight:800;color:#F0F6FF;'
            'letter-spacing:-0.5px;">MedAI Clinical System</div>'
            '<div style="font-size:15px;color:#4A6080;margin-top:6px;">Doctor Login Portal</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0F1E33,#0A1525);'
            'border:2px solid #1E3A5F;border-radius:18px;padding:36px;">',
            unsafe_allow_html=True
        )
        st.markdown('<div style="font-size:13px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Select Doctor</div>',unsafe_allow_html=True)
        doc_labels={f"{v['name']} — {v['dept']}":k for k,v in DOCTORS.items()}
        sel_label=st.selectbox('Doctor',list(doc_labels.keys()),label_visibility='collapsed',key='login_doc')
        sel_id=doc_labels[sel_label]
        st.markdown('<div style="font-size:13px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin:16px 0 8px;">Password</div>',unsafe_allow_html=True)
        pwd=st.text_input('Password',type='password',placeholder='Enter password...',label_visibility='collapsed',key='login_pwd')
        st.markdown('<br>',unsafe_allow_html=True)
        if st.button('Login →',use_container_width=True,type='primary'):
            if pwd==DOCTORS[sel_id]['password']:
                st.session_state.logged_in=True
                st.session_state.active_doctor=sel_id
                st.rerun()
            else:
                st.error('Incorrect password.')
        st.markdown('<div style="font-size:12px;color:#2A3A50;text-align:center;margin-top:14px;">Demo password: 1234</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)


# ── DASHBOARD ─────────────────────────────────────────────────
def render_dashboard():
    active_id=st.session_state.active_doctor
    active=DOCTORS[active_id]

    # Top bar
    st.markdown(
        '<div style="background:linear-gradient(90deg,#080F1C,#0D1B2E);'
        'border-bottom:2px solid #1E3A5F;padding:0 28px;height:64px;'
        'display:flex;align-items:center;justify-content:space-between;">'
        '<div style="display:flex;align-items:center;gap:12px;">'
        '<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);'
        'width:38px;height:38px;border-radius:10px;display:flex;'
        'align-items:center;justify-content:center;font-size:20px;">🏥</div>'
        '<div><div style="font-size:18px;font-weight:800;color:#F0F6FF;">MedAI</div>'
        '<div style="font-size:10px;color:#2A3A50;font-weight:600;'
        'letter-spacing:0.1em;text-transform:uppercase;">Clinical System</div>'
        '</div></div>'
        '<div style="display:flex;align-items:center;gap:16px;">'
        '<div><div style="font-size:14px;font-weight:700;color:#F0F6FF;">'
        + active['name'] + '</div>'
        '<div style="font-size:12px;color:#4A6080;">'
        + active['dept'] + '  ·  ' + active['specialty'] + '</div>'
        '</div>'
        '<div style="background:rgba(0,229,160,0.15);border:2px solid rgba(0,229,160,0.4);'
        'color:#00E5A0;font-size:12px;font-weight:700;padding:5px 14px;'
        'border-radius:20px;">● Active</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    c1,_,c2=st.columns([8,1,1])
    with c2:
        st.markdown('<div style="padding:10px 28px 0 0;">',unsafe_allow_html=True)
        if st.button('Logout',key='logout_btn'):
            st.session_state.logged_in=False
            st.session_state.active_doctor=None
            st.session_state.selected={}
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div style="padding:20px 28px;">',unsafe_allow_html=True)

    mtype=active['mtype']
    dept_icon={'Lab Report':'🧪','CT Scan':'🧠','Ultrasound':'🔬','Combined Assessment':'⚡'}.get(mtype,'📋')

    st.markdown(
        '<div style="margin-bottom:20px;">'
        '<div style="font-size:24px;font-weight:800;color:#F0F6FF;letter-spacing:-0.5px;">'
        + dept_icon + '  ' + active['dept'] + ' — Patient Reports</div>'
        '<div style="font-size:14px;color:#4A6080;margin-top:4px;">'
        'Showing reports assigned to ' + active['name'] + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    df_map={
        'Lab Report':          (lab_df, 'patient_id','final_severity_label'),
        'CT Scan':             (ct_df,  'patient_id','fusion_label'),
        'Ultrasound':          (us_df,  'patient_id','fusion_label'),
        'Combined Assessment': (fus_df, 'patient_id','fusion_label'),
    }
    df,id_col,sev_col=df_map.get(mtype,(None,None,None))
    if df is None: st.warning('No data.'); return

    render_dept(active_id,df,mtype,id_col,sev_col)
    st.markdown('</div>',unsafe_allow_html=True)


def render_dept(doc_id,df,mtype,id_col,sev_col):
    # Stat cards — colorful gradient
    sev_counts=df[sev_col].value_counts() if sev_col in df.columns else {}
    s1,s2,s3,s4=st.columns(4)
    for col,(lbl,clr,grad) in zip([s1,s2,s3,s4],[
        ('Severe',  '#FF3B5C','linear-gradient(135deg,rgba(255,59,92,0.25),rgba(255,59,92,0.05))'),
        ('Moderate','#FF7A35','linear-gradient(135deg,rgba(255,122,53,0.25),rgba(255,122,53,0.05))'),
        ('Mild',    '#FFD000','linear-gradient(135deg,rgba(255,208,0,0.25),rgba(255,208,0,0.05))'),
        ('Normal',  '#00E5A0','linear-gradient(135deg,rgba(0,229,160,0.25),rgba(0,229,160,0.05))'),
    ]):
        cnt=int(sev_counts.get(lbl,0))
        with col:
            st.markdown(
                f'<div style="background:{grad};border:2px solid {clr}55;'
                f'border-top:4px solid {clr};border-radius:14px;'
                f'padding:18px;text-align:center;margin-bottom:18px;">'
                f'<div style="font-size:40px;font-weight:800;color:{clr};line-height:1;">{cnt}</div>'
                f'<div style="font-size:13px;color:{clr};margin-top:8px;'
                f'font-weight:700;opacity:0.9;">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    left,right=st.columns([1,2.5],gap='large')
    with left:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Patient Queue</div>',unsafe_allow_html=True)
        sev_filter=st.selectbox('Filter',['All','Severe','Moderate','Mild','Normal'],key='filter_'+doc_id,label_visibility='collapsed')
        filt=df if sev_filter=='All' else df[df[sev_col]==sev_filter]
        sev_ord={'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        if sev_col in filt.columns:
            filt=filt.sort_values(sev_col,key=lambda x:x.map(sev_ord))

        for _,row in filt.iterrows():
            pid=str(row[id_col])
            sev=str(row.get(sev_col,'Unknown'))
            clr=SEV_COLOR.get(sev,'#6B7A99')
            is_sel=st.session_state.selected.get(doc_id)==pid
            dec=st.session_state.decisions.get(pid,{}).get('status','')
            icon={'APPROVED':'✓ ','REJECTED':'✗ '}.get(dec,'')
            if st.button(icon+pid+'  ·  '+sev,key='p_'+doc_id+'_'+pid,
                         use_container_width=True,
                         type='primary' if is_sel else 'secondary'):
                st.session_state.selected[doc_id]=pid
                st.rerun()

    with right:
        sel_pid=st.session_state.selected.get(doc_id)
        if not sel_pid:
            st.markdown(
                '<div style="background:linear-gradient(135deg,#0A1525,#0D1B2E);'
                'border:2px dashed #1E3A5F;border-radius:16px;padding:80px;text-align:center;">'
                '<div style="font-size:40px;margin-bottom:14px;">👈</div>'
                '<div style="font-size:16px;color:#4A6080;">Select a patient from the queue</div>'
                '</div>',
                unsafe_allow_html=True
            )
            return

        match=df[df[id_col]==sel_pid]
        if match.empty: return
        # Get the actual dataframe index for direct numeric access
        df_idx = match.index[0]
        row=match.iloc[0].to_dict()
        # Override numeric columns directly from df to avoid serialization NaN issues
        for num_col in ['egfr','hba1c','glucose','tsh','free_t4',
                        'ct_confidence','confidence','lab_score',
                        'ct_score','us_score','fusion_score',
                        'lab_hadm_id']:
            if num_col in df.columns:
                val = df.at[df_idx, num_col]
                row[num_col] = None if pd.isna(val) else val
        sev=str(row.get(sev_col,'Unknown'))
        clr=SEV_COLOR.get(sev,'#6B7A99')
        bg =SEV_BG.get(sev,'rgba(107,122,153,0.1)')
        grad=SEV_GRAD.get(sev,'')
        render_patient(row,sel_pid,sev,clr,bg,grad,mtype,doc_id)


def render_patient(row,pid,sev,clr,bg,grad,mtype,doc_id):
    doc=DOCTORS[doc_id]
    urgency={'Severe':'🚨 URGENT','Moderate':'⚠️ SEMI-URGENT','Mild':'📋 ROUTINE','Normal':'✅ ROUTINE'}.get(sev,'📋 REVIEW')
    urg_clr={'Severe':'#FF3B5C','Moderate':'#FF7A35','Mild':'#FFD000','Normal':'#00E5A0'}.get(sev,'#6B7A99')
    current_dec=st.session_state.decisions.get(pid,{}).get('status','')

    # Patient header — colorful gradient
    st.markdown(
        f'<div style="background:{grad};border:2px solid {clr}44;'
        f'border-radius:16px;padding:20px 24px;margin-bottom:20px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<div style="font-size:11px;font-weight:700;color:{clr};letter-spacing:0.12em;'
        f'text-transform:uppercase;margin-bottom:6px;">Patient ID</div>'
        f'<div style="font-size:24px;font-weight:800;color:#F0F6FF;font-family:monospace;">{pid}</div>'
        f'<div style="font-size:13px;color:#4A6080;margin-top:6px;">{mtype}  ·  {doc["name"]}</div>'
        f'</div>'
        f'<div style="background:{bg};border:2px solid {clr}66;border-radius:14px;'
        f'padding:14px 24px;text-align:center;">'
        f'<div style="font-size:13px;font-weight:700;color:{urg_clr};margin-bottom:6px;">{urgency}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{clr};">{sev}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True
    )

    # Test findings
    st.markdown(
        f'<div style="font-size:12px;font-weight:700;color:#4A9EFF;'
        f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">Test Findings</div>',
        unsafe_allow_html=True
    )
    if mtype=='Lab Report':         render_lab(row,sev,clr)
    elif mtype=='CT Scan':          render_ct(row,sev,clr)
    elif mtype=='Ultrasound':       render_us(row,sev,clr)
    elif mtype=='Combined Assessment': render_combined(row,sev,clr)

    # RAG Summary
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A9EFF;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 14px;">'
        'AI Clinical Summary</div>',
        unsafe_allow_html=True
    )

    if mtype=='Combined Assessment':
        parsed   = get_mm_rag_summary(row)
        citations= parsed.pop('citations',[])
    else:
        rag_key  = str(row.get('rag_class_key',''))
        rag_raw  = rag_data.get(rag_key,{})
        raw_text = rag_raw.get('raw_text','') if isinstance(rag_raw,dict) else ''
        citations= rag_raw.get('citations',[]) if isinstance(rag_raw,dict) else []
        parsed   = parse_rag(raw_text) if raw_text else {}

    render_rag(parsed,citations)

    # Doctor decision
    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#4A9EFF;'
        'text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 12px;">'
        'Doctor Review & Decision</div>',
        unsafe_allow_html=True
    )

    if current_dec=='APPROVED':
        ap=st.session_state.decisions[pid]
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(0,229,160,0.15),'
            'rgba(0,229,160,0.05));border:2px solid rgba(0,229,160,0.4);'
            'border-radius:14px;padding:20px 24px;">'
            '<div style="font-size:16px;font-weight:800;color:#00E5A0;margin-bottom:8px;">'
            '✅  Report Approved & Released</div>'
            '<div style="font-size:14px;color:#4A6080;line-height:1.7;">'
            'Approved by: <b style="color:#F0F6FF;">' + ap['doctor'] + '</b><br>'
            'Time: ' + ap['time'] + '<br>'
            '<span style="color:#00E5A0;font-weight:600;">Patient message sent successfully.</span>'
            '</div></div>',
            unsafe_allow_html=True
        )
        with st.expander('📱 View Patient Message Sent'):
            st.markdown(
                '<div style="background:#0A1525;border:2px solid #1E3A5F;'
                'border-radius:12px;padding:20px;font-size:14px;'
                'color:#C8D6E8;white-space:pre-wrap;line-height:1.8;">'
                + ap['message'] + '</div>',
                unsafe_allow_html=True
            )

    elif current_dec=='REJECTED':
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(255,59,92,0.15),'
            'rgba(255,59,92,0.05));border:2px solid rgba(255,59,92,0.4);'
            'border-radius:14px;padding:20px 24px;">'
            '<div style="font-size:16px;font-weight:800;color:#FF3B5C;margin-bottom:8px;">'
            '❌  Report Rejected</div>'
            '<div style="font-size:14px;color:#4A6080;">'
            'Patient has NOT been notified. No message sent.<br>'
            'Please review findings and resubmit or request further tests.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if st.button('↺  Reset Decision',key='reset_'+pid):
            del st.session_state.decisions[pid]
            st.rerun()

    else:
        notes=st.text_area(
            'Clinical notes / prescription',
            placeholder='Add prescription, clinical notes, or amendments...',
            height=100,key='notes_'+doc_id+'_'+pid,label_visibility='collapsed'
        )
        pat_msg=get_patient_message(sev,mtype,row)
        if notes: pat_msg+='\n\nDoctor\'s additional instructions:\n'+notes

        with st.expander('📱  Preview Patient Message'):
            st.markdown(
                '<div style="background:#0A1525;border:2px solid #1E3A5F;'
                'border-radius:12px;padding:20px 24px;">'
                '<div style="font-size:12px;font-weight:700;color:#00E5A0;'
                'margin-bottom:12px;letter-spacing:0.08em;">MESSAGE TO PATIENT</div>'
                '<div style="font-size:14px;color:#C8D6E8;line-height:1.8;'
                'white-space:pre-wrap;">' + pat_msg + '</div></div>',
                unsafe_allow_html=True
            )

        st.markdown('<br>',unsafe_allow_html=True)
        b1,b2,b3=st.columns(3)
        with b1:
            if st.button('✅  Approve & Send',key='app_'+doc_id+'_'+pid,
                         use_container_width=True,type='primary'):
                st.session_state.decisions[pid]={'status':'APPROVED','doctor':DOCTORS[doc_id]['name'],
                    'time':datetime.now().strftime('%Y-%m-%d %H:%M'),'notes':notes,'message':pat_msg}
                st.rerun()
        with b2:
            if st.button('✏️  Approve with Edits',key='edit_'+doc_id+'_'+pid,use_container_width=True):
                st.session_state.decisions[pid]={'status':'APPROVED','doctor':DOCTORS[doc_id]['name'],
                    'time':datetime.now().strftime('%Y-%m-%d %H:%M'),'notes':notes,'message':pat_msg}
                st.rerun()
        with b3:
            if st.button('❌  Reject',key='rej_'+doc_id+'_'+pid,use_container_width=True):
                st.session_state.decisions[pid]={'status':'REJECTED','doctor':DOCTORS[doc_id]['name'],
                    'time':datetime.now().strftime('%Y-%m-%d %H:%M')}
                st.rerun()


# ── FINDINGS RENDERERS ────────────────────────────────────────
def finding_card(title, value, color='#F0F6FF', border_color=None):
    border = f'border-left:4px solid {border_color};' if border_color else ''
    return (
        f'<div style="background:#0A1525;border:2px solid #1E3A5F;'
        f'{border}border-radius:12px;padding:16px;">'
        f'<div style="font-size:11px;font-weight:700;color:#4A6080;'
        f'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{title}</div>'
        f'<div style="font-size:17px;font-weight:700;color:{color};">{value}</div>'
        f'</div>'
    )

def ref_table(rows, source):
    header=(
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;border-bottom:2px solid #1E3A5F;padding-bottom:8px;margin-bottom:4px;">'
        +''.join([f'<div style="font-size:11px;font-weight:700;color:#4A9EFF;'
                  f'text-transform:uppercase;letter-spacing:0.06em;">{h}</div>'
                  for h in ['Parameter','Patient Value','Guideline Range','Status']])
        +'</div>'
    )
    body=''
    for param,pat_val,guide,status in rows:
        pv_clr={'Normal':'#00E5A0','Abnormal':'#FF3B5C','Borderline':'#FFD000','N/A':'#4A6080'}.get(status,'#4A6080')
        body+=(
            '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
            'gap:0;padding:10px 0;border-bottom:1px solid #1E3A5F;align-items:center;">'
            f'<div style="font-size:13px;font-weight:600;color:#E8EDF5;">{param}</div>'
            f'<div style="font-size:13px;font-weight:700;color:{pv_clr};">{pat_val}</div>'
            f'<div style="font-size:12px;color:#4A6080;line-height:1.5;">{guide}</div>'
            f'<div>{sev_badge(status)}</div>'
            '</div>'
        )
    return (
        '<div style="background:#0A1525;border:2px solid #1E3A5F;'
        'border-left:4px solid #4A9EFF;border-radius:14px;'
        'padding:16px 20px;margin-bottom:14px;">'
        + header + body +
        f'<div style="font-size:11px;color:#2A3A50;margin-top:10px;'
        f'font-style:italic;">Source: {source}</div>'
        '</div>'
    )

def render_lab(row,sev,clr):
    ckd=str(row.get('ckd_severity','Not tested'))
    dia=str(row.get('diabetes_severity_final','Not tested'))
    thy=str(row.get('thyroid_severity_final','Not tested'))
    for f in ['ckd_severity','diabetes_severity_final','thyroid_severity_final']:
        if str(row.get(f,'')) in ['None','nan','NaN','']:
            if f=='ckd_severity': ckd='Not tested'
            elif f=='diabetes_severity_final': dia='Not tested'
            else: thy='Not tested'

    egfr=get_num(row,'egfr')
    glucose=get_num(row,'glucose')
    tsh=get_num(row,'tsh')
    free_t4=get_num(row,'free_t4')
    disease=str(row.get('disease_type','')).lower()

    c1,c2,c3=st.columns(3)
    for col,(lbl,val) in zip([c1,c2,c3],[
        ('Kidney Function',ckd),('Blood Sugar',dia),('Thyroid Function',thy)
    ]):
        v=val if val not in ['Not tested','None','nan','NaN','Unknown'] else 'Not tested'
        vc=clr if v!='Not tested' else '#2A3A50'
        with col:
            st.markdown(finding_card(lbl,v,vc),unsafe_allow_html=True)

    # Build reference table
    rows=[]
    if 'ckd' in disease or 'kidney' in disease:
        if egfr is not None:
            st_='Normal' if egfr>=60 else 'Borderline' if egfr>=30 else 'Abnormal'
            stage='G1(≥90)' if egfr>=90 else 'G2(60-89)' if egfr>=60 else 'G3a(45-59)' if egfr>=45 else 'G3b(30-44)' if egfr>=30 else 'G4(15-29)' if egfr>=15 else 'G5(<15)'
            rows.append(('eGFR',fmt(egfr,'mL/min'),'≥90:G1(Normal) · 60-89:G2(Normal) · 45-59:G3a · 30-44:G3b · <30:G4-G5',st_))
            rows.append(('KDIGO Stage',stage+' — '+ckd,'G1-G2=Normal · G3=Moderate · G4-G5=Severe','Normal' if egfr>=60 else 'Borderline' if egfr>=45 else 'Abnormal'))
        else:
            # No eGFR — show CKD severity from clinical diagnosis
            ckd_st='Normal' if 'G1' in ckd or 'G2' in ckd else 'Borderline' if 'G3' in ckd else 'Abnormal' if ckd not in ['Not tested',''] else 'N/A'
            rows.append(('CKD Stage',ckd if ckd not in ['Not tested',''] else 'Not recorded','G1:>=90 · G2:60-89 · G3a:45-59 · G3b:30-44 · G4:15-29 · G5:<15',ckd_st))
            rows.append(('eGFR','Not measured','eGFR not available — severity from clinical diagnosis','N/A'))
        rows.append(('Clinical Severity',sev,'KDIGO 2022: based on eGFR + albuminuria','Normal' if sev=='Normal' else 'Borderline' if sev=='Mild' else 'Abnormal'))
        rows.append(('BP Target','—','<130/80 mmHg · ACE inhibitor if proteinuria','N/A'))
        src='KDIGO 2022 Clinical Practice Guideline for CKD'

    elif 'diabetes' in disease:
        dia_st='Normal' if dia=='Normal' else 'Borderline' if dia=='Mild' else 'Abnormal' if dia=='Severe' else 'N/A'
        if glucose is not None:
            gs='Normal' if glucose<100 else 'Borderline' if glucose<126 else 'Abnormal'
            rows.append(('Glucose (Fasting)',fmt(glucose,'mg/dL'),'Normal:<100 · Pre-diabetic:100-125 · Diabetic:>=126',gs))
        else:
            rows.append(('Glucose','Not measured this visit','Normal:<100 · Pre-diabetic:100-125 · Diabetic:>=126','N/A'))
        rows.append(('Diabetes Severity',dia,'Normal · Mild:borderline control · Severe:poor control',dia_st))
        rows.append(('HbA1c Target','—','<7.0% (most patients) · <8.0% (elderly/complex)','N/A'))
        rows.append(('Monitoring','—','Self-monitor glucose daily · HbA1c every 3 months','N/A'))
        src='ADA Standards of Medical Care in Diabetes 2024'

    elif 'thyroid' in disease:
        thy_st='Normal' if thy in ['Normal','Mild'] else 'Abnormal' if thy=='Severe' else 'N/A'
        if tsh is not None:
            ts='Normal' if 0.4<=tsh<=4.0 else 'Borderline' if tsh<=10 else 'Abnormal'
            interp='Euthyroid (Normal)' if 0.4<=tsh<=4.0 else 'Subclinical Hypothyroid' if tsh<=10 else 'Overt Hypothyroid'
            rows.append(('TSH Level',fmt(tsh,'mIU/L'),'Normal:0.4-4.0 · Subclinical:4.1-10.0 · Overt Hypothyroid:>10.0',ts))
            rows.append(('TSH Interpretation',interp,'Subclinical=TSH high but T4 still normal · Overt=TSH very high + T4 low',ts))
        else:
            rows.append(('TSH Level','Not measured','Normal:0.4-4.0 mIU/L · Subclinical:4.1-10.0 · Overt:>10.0','N/A'))
        if free_t4 is not None:
            t4s='Normal' if 0.8<=free_t4<=1.8 else 'Abnormal'
            rows.append(('Free T4',fmt(free_t4,'ng/dL'),'Normal:0.8-1.8 ng/dL · Low T4=Hypothyroid',t4s))
        else:
            rows.append(('Free T4','Not measured','Normal:0.8-1.8 ng/dL','N/A'))
        rows.append(('Thyroid Status',thy,'Normal · Mild=Subclinical Hypothyroid · Severe=Overt Hypothyroid',thy_st))
        rows.append(('Treatment Threshold','—','Levothyroxine if TSH>10 mIU/L or symptomatic at TSH 4-10','N/A'))
        src='ATA/AACE Clinical Practice Guidelines for Hypothyroidism 2023'
    else:
        src='WHO / Standard Clinical Guidelines'

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 10px;">Patient Values vs Clinical Guidelines</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,src),unsafe_allow_html=True)


def render_ct(row,sev,clr):
    cls=row.get('ct_predicted_class',row.get('disease_type',''))
    conf=row.get('ct_confidence',0)
    name=CT_NAMES.get(cls,cls); desc=CT_DESC.get(cls,'')
    st.markdown(
        f'<div style="background:#0A1525;border:2px solid #1E3A5F;'
        f'border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
        f'<div style="font-size:11px;font-weight:700;color:#4A9EFF;text-transform:uppercase;'
        f'letter-spacing:0.08em;margin-bottom:10px;">CT Brain Imaging</div>'
        f'<div style="font-size:20px;font-weight:800;color:#F0F6FF;margin-bottom:6px;">{name}</div>'
        f'<div style="font-size:14px;color:#4A6080;margin-bottom:10px;">{desc}</div>'
        f'<div style="display:flex;gap:16px;">'
        f'<span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;'
        f'color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
        f'<span style="color:#4A6080;font-size:13px;">AI Confidence: '
        f'<b style="color:#F0F6FF;">{round(float(conf)*100,1)}%</b></span>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    t=CT_IMAGE.get(str(cls),('',''))
    orig=t[0]; grad=t[1]
    if orig and os.path.exists(orig):
        st.markdown('<div style="font-size:13px;font-weight:700;color:#F0F6FF;margin-bottom:10px;">Scan Images & AI Attention Map</div>',unsafe_allow_html=True)
        gc1,gc2=st.columns(2)
        with gc1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original CT Scan</div>',unsafe_allow_html=True)
            st.image(orig,use_column_width=True)
        with gc2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if grad and os.path.exists(grad): st.image(grad,use_column_width=True)
        st.markdown('<div style="background:#0A1525;border:2px solid #1E3A5F;border-left:4px solid #7C3AED;border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:#4A6080;">🔍 <b style="color:#F0F6FF;">Grad-CAM:</b> Warm colours (red/yellow) = high AI attention. Cool colours (blue) = low attention areas.</div>',unsafe_allow_html=True)


def render_us(row,sev,clr):
    cls=row.get('predicted_class',row.get('disease_type',''))
    conf=row.get('confidence',0)
    name=US_NAMES.get(cls,cls); desc=US_DESC.get(cls,'')
    st.markdown(
        f'<div style="background:#0A1525;border:2px solid #1E3A5F;'
        f'border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
        f'<div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;'
        f'letter-spacing:0.08em;margin-bottom:10px;">Obstetric Ultrasound</div>'
        f'<div style="font-size:20px;font-weight:800;color:#F0F6FF;margin-bottom:6px;">{name}</div>'
        f'<div style="font-size:14px;color:#4A6080;margin-bottom:10px;">{desc}</div>'
        f'<div style="display:flex;gap:16px;">'
        f'<span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;'
        f'color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
        f'<span style="color:#4A6080;font-size:13px;">AI Confidence: '
        f'<b style="color:#F0F6FF;">{round(float(conf)*100,1)}%</b></span>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    t=US_IMAGE.get(str(cls),('',''))
    orig=t[0]; grad=t[1]
    if orig and os.path.exists(orig):
        st.markdown('<div style="font-size:13px;font-weight:700;color:#F0F6FF;margin-bottom:10px;">Scan Images & AI Attention Map</div>',unsafe_allow_html=True)
        ug1,ug2=st.columns(2)
        with ug1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original Ultrasound</div>',unsafe_allow_html=True)
            st.image(orig,use_column_width=True)
        with ug2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if grad and os.path.exists(grad): st.image(grad,use_column_width=True)
        st.markdown('<div style="background:#0A1525;border:2px solid #1E3A5F;border-left:4px solid #7C3AED;border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:#4A6080;">🔍 <b style="color:#F0F6FF;">Grad-CAM:</b> Highlighted regions show where the AI focused during fetal plane classification.</div>',unsafe_allow_html=True)


def render_combined(row,sev,clr):
    # Score cards
    c1,c2,c3,c4=st.columns(4)
    for col,(lbl,key) in zip([c1,c2,c3,c4],[('Lab','lab_score'),('CT','ct_score'),('Ultrasound','us_score'),('Fusion','fusion_score')]):
        val=row.get(key)
        try: v=SCORE_MAP.get(int(float(val)),'—') if val is not None and str(val) not in ['None','nan'] else '—'
        except: v='—'
        vc=SEV_COLOR.get(v,'#4A6080')
        with col:
            st.markdown(
                f'<div style="background:{SEV_BG.get(v,"rgba(74,96,128,0.1)")};'
                f'border:2px solid {vc}55;border-radius:12px;padding:14px;'
                f'text-align:center;margin-bottom:12px;">'
                f'<div style="font-size:11px;font-weight:700;color:{vc};text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                f'<div style="font-size:24px;font-weight:800;color:{vc};">{v}</div>'
                f'</div>',unsafe_allow_html=True
            )

    ct_cls=row.get('ct_predicted_class',''); us_cls=row.get('us_predicted_class',row.get('predicted_class',''))
    if ct_cls or us_cls:
        parts=[]
        if ct_cls: parts.append('🧠 CT: <b style="color:#F0F6FF;">'+CT_NAMES.get(ct_cls,ct_cls)+'</b>')
        if us_cls: parts.append('🔬 US: <b style="color:#F0F6FF;">'+US_NAMES.get(us_cls,us_cls)+'</b>')
        st.markdown('<div style="font-size:13px;color:#4A6080;margin-bottom:14px;">'+' &nbsp;·&nbsp; '.join(parts)+'</div>',unsafe_allow_html=True)

    # Lab values for combined patients
    ckd=str(row.get('ckd_severity','Not tested')); dia=str(row.get('diabetes_severity_final','Not tested')); thy=str(row.get('thyroid_severity_final','Not tested'))
    egfr=get_num(row,'egfr'); glucose=get_num(row,'glucose'); tsh=get_num(row,'tsh'); free_t4=get_num(row,'free_t4')

    rows=[]
    if egfr is not None:
        st_='Normal' if egfr>=60 else 'Borderline' if egfr>=30 else 'Abnormal'
        rows.append(('eGFR',fmt(egfr,'mL/min'),'≥90:Normal · 60–89:G2 · 45–59:G3a · <30:G4-G5',st_))
    if ckd not in ['Not tested','None','nan','NaN','']:
        rows.append(('CKD Stage',ckd,'G1–G2=Normal · G3a–G3b=Moderate · G4–G5=Severe','Normal' if 'G1' in ckd or 'G2' in ckd else 'Borderline' if 'G3' in ckd else 'Abnormal'))
    if glucose is not None:
        gs='Normal' if glucose<100 else 'Borderline' if glucose<126 else 'Abnormal'
        rows.append(('Glucose',fmt(glucose,'mg/dL'),'Normal:<100 · Pre-diabetic:100–125 · Diabetic:≥126',gs))
    if dia not in ['Not tested','None','nan','NaN','']:
        rows.append(('Diabetes',dia,'Normal:<100 · Mild:126–180 · Severe:>180','Normal' if dia=='Normal' else 'Borderline' if dia=='Mild' else 'Abnormal' if dia=='Severe' else 'N/A'))
    if tsh is not None:
        ts='Normal' if 0.4<=tsh<=4.0 else 'Borderline' if tsh<=10 else 'Abnormal'
        rows.append(('TSH',fmt(tsh,'mIU/L'),'Normal:0.4–4.0 · Subclinical:4.1–10 · Overt:>10',ts))
    if free_t4 is not None:
        rows.append(('Free T4',fmt(free_t4,'ng/dL'),'Normal:0.8–1.8 ng/dL',('Normal' if 0.8<=free_t4<=1.8 else 'Abnormal')))
    if thy not in ['Not tested','None','nan','NaN','']:
        rows.append(('Thyroid',thy,'Normal · Mild:Subclinical · Severe:Overt','Normal' if thy in ['Normal','Mild'] else 'Abnormal'))

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin:8px 0 10px;">Lab Values vs Reference Ranges</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,'KDIGO 2022 · ADA 2024 · ATA/AACE 2023'),unsafe_allow_html=True)


def render_rag(parsed,citations):
    if not parsed: st.markdown('<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:10px;padding:14px 18px;color:#4A6080;">RAG summary not available.</div>',unsafe_allow_html=True); return

    if parsed.get('clinical_summary'):
        st.markdown(
            '<div style="background:linear-gradient(135deg,#130A2E,#0D1B2E);'
            'border:2px solid #3B1FA8;border-left:5px solid #7C3AED;'
            'border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
            '<div style="font-size:11px;font-weight:700;color:#A78BFA;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:10px;">Clinical Overview</div>'
            '<div style="font-size:15px;color:#E8EDF5;line-height:1.85;">'
            + parsed['clinical_summary'] + '</div></div>',
            unsafe_allow_html=True
        )

    if parsed.get('key_findings'):
        fh=''.join([
            f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1E3A5F;">'
            f'<span style="color:#C084FC;font-weight:700;font-size:16px;flex-shrink:0;">•</span>'
            f'<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">{f}</span></div>'
            for f in parsed['key_findings']
        ])
        st.markdown(
            '<div style="background:#0A1525;border:2px solid #1E3A5F;'
            'border-radius:12px;padding:16px 20px;margin-bottom:14px;">'
            '<div style="font-size:11px;font-weight:700;color:#A78BFA;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:10px;">Key Findings</div>'
            + fh + '</div>',
            unsafe_allow_html=True
        )

    if parsed.get('recommendations'):
        rh=''.join([
            f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1E3A5F;">'
            f'<span style="background:linear-gradient(135deg,#2563EB,#1D4ED8);color:white;'
            f'font-weight:800;font-size:13px;padding:3px 10px;border-radius:8px;flex-shrink:0;'
            f'min-width:28px;text-align:center;">{i+1}</span>'
            f'<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">{r}</span></div>'
            for i,r in enumerate(parsed['recommendations'])
        ])
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(0,229,160,0.08),rgba(0,229,160,0.02));'
            'border:2px solid rgba(0,229,160,0.3);border-left:5px solid #00E5A0;'
            'border-radius:14px;padding:16px 20px;margin-bottom:14px;">'
            '<div style="font-size:11px;font-weight:700;color:#00E5A0;text-transform:uppercase;'
            'letter-spacing:0.1em;margin-bottom:10px;">Clinical Recommendations</div>'
            + rh + '</div>',
            unsafe_allow_html=True
        )

    fu_col,ug_col=st.columns(2)
    with fu_col:
        if parsed.get('followup'):
            st.markdown(
                '<div style="background:#0A1525;border:2px solid #1E3A5F;'
                'border-radius:12px;padding:14px 18px;margin-bottom:12px;">'
                '<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;'
                'letter-spacing:0.08em;margin-bottom:6px;">Follow-up Plan</div>'
                '<div style="font-size:14px;color:#F0F6FF;font-weight:600;">'
                + parsed['followup'] + '</div></div>',
                unsafe_allow_html=True
            )
    with ug_col:
        if parsed.get('urgency'):
            uc={'URGENT':'#FF3B5C','SEMI-URGENT':'#FF7A35','ROUTINE':'#00E5A0'}.get(parsed['urgency'].upper(),'#6B7A99')
            st.markdown(
                f'<div style="background:{SEV_BG.get({"URGENT":"Severe","SEMI-URGENT":"Moderate","ROUTINE":"Normal"}.get(parsed["urgency"].upper(),"Unknown"),"")};'
                f'border:2px solid {uc}55;border-radius:12px;padding:14px 18px;margin-bottom:12px;">'
                f'<div style="font-size:11px;font-weight:700;color:{uc};text-transform:uppercase;'
                f'letter-spacing:0.08em;margin-bottom:6px;">Urgency</div>'
                f'<div style="font-size:20px;font-weight:800;color:{uc};">{parsed["urgency"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    if citations:
        st.markdown(
            '<div style="background:#0A1525;border:2px solid #1E3A5F;'
            'border-radius:10px;padding:12px 18px;margin-bottom:14px;">'
            '<div style="font-size:11px;font-weight:700;color:#4A9EFF;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:6px;">Guideline References</div>'
            '<div style="font-size:13px;color:#2A3A50;font-family:monospace;">'
            + '  ·  '.join(list(dict.fromkeys(citations))) + '</div></div>',
            unsafe_allow_html=True
        )


# ── ENTRY POINT ───────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    render_dashboard()
