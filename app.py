import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="MedAI — Doctor Dashboard", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")

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
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:700!important;font-size:15px!important;border-radius:10px!important;padding:11px 22px!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2563EB,#1D4ED8)!important;border:none!important;color:white!important;box-shadow:0 4px 15px rgba(37,99,235,0.4)!important;}
.stButton>button[kind="secondary"]{background:#0F1E33!important;border:2px solid #1E3A5F!important;color:#94A3B8!important;}
.stTabs [data-baseweb="tab-list"]{background:#080F1C!important;border-bottom:2px solid #1E3A5F!important;padding:0 8px!important;}
.stTabs [data-baseweb="tab"]{font-size:15px!important;font-weight:600!important;color:#4A6080!important;padding:14px 22px!important;}
.stTabs [aria-selected="true"]{color:#60A5FA!important;border-bottom:3px solid #2563EB!important;background:transparent!important;}
hr{border-color:#1E3A5F!important;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
SEV_COLOR = {'Normal':'#00E5A0','Mild':'#FFD000','Moderate':'#FF7A35','Severe':'#FF3B5C','Unknown':'#6B7A99'}
SEV_BG    = {'Normal':'rgba(0,229,160,0.1)','Mild':'rgba(255,208,0,0.1)','Moderate':'rgba(255,122,53,0.1)','Severe':'rgba(255,59,92,0.1)','Unknown':'rgba(107,122,153,0.1)'}
SEV_GRAD  = {'Normal':'linear-gradient(135deg,rgba(0,229,160,0.2),rgba(0,229,160,0.05))','Mild':'linear-gradient(135deg,rgba(255,208,0,0.2),rgba(255,208,0,0.05))','Moderate':'linear-gradient(135deg,rgba(255,122,53,0.2),rgba(255,122,53,0.05))','Severe':'linear-gradient(135deg,rgba(255,59,92,0.2),rgba(255,59,92,0.05))','Unknown':'linear-gradient(135deg,rgba(107,122,153,0.15),rgba(107,122,153,0.05))'}
SCORE_MAP = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
CT_NAMES  = {'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}
CT_DESC   = {'notumor':'Normal brain parenchyma. No suspicious mass or lesion identified.','pituitary':'Benign pituitary gland tumour. Endocrinology review recommended.','meningioma':'Slow-growing meningeal tumour. Neurosurgery referral advised.','glioma':'Malignant brain tumour. Urgent oncology referral required.'}
US_NAMES  = {'Fetal abdomen':'Fetal Abdomen — Normal','Fetal brain':'Fetal Brain Plane','Fetal femur':'Fetal Femur — Normal Growth','Fetal thorax':'Fetal Thorax Plane'}
US_DESC   = {'Fetal abdomen':'Abdominal measurements within expected range for gestational age.','Fetal brain':'Neurosonography plane. Detailed anomaly scan recommended.','Fetal femur':'Femur length within normal range. Fetal growth on track.','Fetal thorax':'Thoracic plane. Cardiac and pulmonary assessment indicated.'}
CT_IMAGE  = {'glioma':('images/ct_glioma_original.jpg','images/ct_glioma_gradcam.png'),'meningioma':('images/ct_meningioma_original.jpg','images/ct_meningioma_gradcam.png'),'pituitary':('images/ct_pituitary_original.jpg','images/ct_pituitary_gradcam.png'),'notumor':('images/ct_notumor_original.jpg','images/ct_notumor_gradcam.png')}
US_IMAGE  = {'Fetal abdomen':('images/us_abdomen_original.png','images/us_abdomen_gradcam.png'),'Fetal brain':('images/us_brain_original.png','images/us_brain_gradcam.png'),'Fetal femur':('images/us_femur_original.png','images/us_femur_gradcam.png'),'Fetal thorax':('images/us_thorax_original.png','images/us_thorax_gradcam.png')}
DOCTORS   = {
    'DR001':{'name':'Dr. Priya Sharma', 'dept':'Internal Medicine','specialty':'Nephrology & Chronic Disease','color':'#60A5FA','password':'1234','mtype':'Lab Report'},
    'DR002':{'name':'Dr. Arjun Mehta',  'dept':'Neurology',        'specialty':'Neuro-Oncology',             'color':'#C084FC','password':'1234','mtype':'CT Scan'},
    'DR003':{'name':'Dr. Kavitha Rajan','dept':'Obstetrics',        'specialty':'Fetal Medicine',             'color':'#34D399','password':'1234','mtype':'Ultrasound'},
    'DR004':{'name':'Dr. Suresh Kumar', 'dept':'General Medicine',  'specialty':'Multimodal Assessment',      'color':'#FBBF24','password':'1234','mtype':'Combined Assessment'},
}


# ── LOAD DATA — from JSON, no NaN issues ──────────────────────
@st.cache_data
def load_patients():
    for p in ['data/patients.json','patients.json']:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return {}

@st.cache_data
def load_rag():
    for p in ['data/rag_summaries.json','rag_summaries.json']:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return {}

ALL_PATIENTS = load_patients()
RAG_DATA     = load_rag()


# ── SESSION STATE ─────────────────────────────────────────────
for k,v in {'logged_in':False,'active_doctor':None,'selected':{},'decisions':{}}.items():
    if k not in st.session_state: st.session_state[k]=v


# ── HELPERS ───────────────────────────────────────────────────
def n(v):
    """Safe float — returns None for null/nan, float otherwise."""
    if v is None: return None
    try:
        f = float(v)
        return None if f!=f else f
    except: return None

def fmt(v, unit=''):
    if v is None: return '—'
    return f"{round(float(v),2)}{' '+unit if unit else ''}"

def sev_badge(status):
    cfg = {
        'Normal':    ('#00E5A0','rgba(0,229,160,0.15)','✓ Normal'),
        'Abnormal':  ('#FF3B5C','rgba(255,59,92,0.15)', '✗ Abnormal'),
        'Borderline':('#FFD000','rgba(255,208,0,0.15)', '⚠ Borderline'),
        'N/A':       ('#6B7A99','rgba(107,122,153,0.15)','— Not tested'),
    }.get(status,('#6B7A99','rgba(107,122,153,0.15)','—'))
    return f'<span style="background:{cfg[1]};color:{cfg[0]};font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;">{cfg[2]}</span>'

def parse_rag(raw):
    s={'clinical_summary':'','key_findings':[],'recommendations':[],'followup':'','urgency':''}
    cur=None
    for line in raw.split('\n'):
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

def ref_row(param, pat_val, guide, status):
    pv_clr={'Normal':'#00E5A0','Abnormal':'#FF3B5C','Borderline':'#FFD000','N/A':'#6B7A99'}.get(status,'#6B7A99')
    return (
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;padding:10px 0;border-bottom:1px solid #1E3A5F;align-items:center;">'
        f'<div style="font-size:13px;font-weight:600;color:#E8EDF5;">{param}</div>'
        f'<div style="font-size:13px;font-weight:700;color:{pv_clr};">{pat_val}</div>'
        f'<div style="font-size:12px;color:#4A6080;line-height:1.5;">{guide}</div>'
        f'<div>{sev_badge(status)}</div>'
        '</div>'
    )

def ref_table(rows, source):
    header=(
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;border-bottom:2px solid #1E3A5F;padding-bottom:8px;margin-bottom:4px;">'
        +''.join([f'<div style="font-size:11px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.06em;">{h}</div>'
                  for h in ['Parameter','Patient Value','Guideline Range','Status']])
        +'</div>'
    )
    return (
        '<div style="background:#0A1525;border:2px solid #1E3A5F;'
        'border-left:4px solid #4A9EFF;border-radius:14px;padding:16px 20px;margin-bottom:14px;">'
        +header+''.join(rows)+
        f'<div style="font-size:11px;color:#2A3A50;margin-top:10px;font-style:italic;">Source: {source}</div>'
        '</div>'
    )


# ── PATIENT MESSAGE ───────────────────────────────────────────
def get_msg(p):
    sev   = p.get('_sev','Normal')
    mtype = p.get('modality_type','')
    disease = str(p.get('disease_type','')).lower()

    if mtype == 'Lab Report':
        egfr_v = n(p.get('egfr')); glucose_v = n(p.get('glucose')); tsh_v = n(p.get('tsh'))
        ckd = p.get('ckd_severity') or ''; dia = p.get('diabetes_severity_final') or ''; thy = p.get('thyroid_severity_final') or ''

        if 'ckd' in disease or 'kidney' in disease:
            egfr_str = f' (eGFR: {round(egfr_v,1)} mL/min)' if egfr_v else ''
            cond  = f'Chronic Kidney Disease — {ckd}{egfr_str}'
            if sev=='Normal':   detail,action = 'Your kidney function is within an acceptable range. No treatment needed at this stage.','Stay well-hydrated, avoid NSAIDs. Next kidney function check in 3 months.'
            elif sev=='Mild':   detail,action = 'Your kidney function shows mild reduction and needs regular monitoring.','Follow low-sodium, low-protein diet. Nephrology follow-up within 4 weeks.'
            else:               detail,action = 'Your kidney function is significantly reduced and requires specialist attention.','Please contact your nephrologist immediately. Avoid all medications that stress the kidneys.'
        elif 'diabetes' in disease:
            gluc_str = f' (Glucose: {round(glucose_v,1)} mg/dL)' if glucose_v else ''
            cond  = f'Diabetes Mellitus{gluc_str}'
            if sev=='Normal':   detail,action = 'Your blood glucose levels are well controlled and within target range.','Continue current medication and diet. Check blood glucose daily. Review in 3 months.'
            elif sev=='Mild':   detail,action = 'Your blood glucose is mildly elevated and needs closer monitoring.','Follow the low-sugar diet plan. Follow-up appointment in 2 to 4 weeks.'
            else:
                gd = f'{round(glucose_v,1)} mg/dL' if glucose_v else 'significantly elevated'
                detail,action = f'Your blood glucose is significantly elevated ({gd}) and requires prompt attention.','Please contact your doctor today. Do not skip medication. Avoid all sugary foods.'
        elif 'thyroid' in disease:
            tsh_str = f' (TSH: {round(tsh_v,2)} mIU/L)' if tsh_v else ''
            cond  = f'Thyroid Disorder{tsh_str}'
            if sev=='Normal':   detail,action = 'Your thyroid hormone levels are within the normal range.','Continue current thyroid medication if prescribed. Routine check in 6 months.'
            elif sev=='Mild':   detail,action = 'Your TSH is mildly elevated (subclinical hypothyroidism). Free T4 is still normal.','Your doctor may recommend low-dose Levothyroxine. Follow up in 4 to 6 weeks.'
            else:               detail,action = 'Your thyroid levels indicate overt hypothyroidism requiring prompt treatment.','Please begin or adjust Levothyroxine as prescribed. Review in 6 to 8 weeks.'
        else:
            cond,detail,action = 'Chronic Disease Assessment','Your lab results have been reviewed by your doctor.','Please follow your doctor\'s prescription carefully.'

    elif mtype == 'CT Scan':
        cls  = p.get('ct_predicted_class','')
        conf = n(p.get('ct_confidence')) or 0
        names= {'notumor':'No Brain Tumour','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}
        cond = names.get(cls,cls)+f' (AI confidence: {round(conf*100,1)}%)'
        if cls=='notumor':     detail,action = 'Your brain CT scan shows no signs of any tumour. Your scan is normal.','No further imaging needed. Routine follow-up as advised by your neurologist.'
        elif cls=='pituitary': detail,action = 'A small benign pituitary gland tumour has been identified. Usually slow-growing.','An endocrinology referral has been arranged. Hormone blood tests will be ordered.'
        elif cls=='meningioma':detail,action = 'A meningioma has been identified — typically a slow-growing tumour of the brain lining.','A neurosurgery consultation has been arranged. Further MRI imaging will be required.'
        else:                  detail,action = 'A glioma has been identified on your brain scan. This requires urgent specialist attention.','An urgent oncology referral has been made. Please attend the hospital as soon as possible.'

    elif mtype == 'Ultrasound':
        cls  = p.get('predicted_class','')
        conf = n(p.get('confidence')) or 0
        names= {'Fetal abdomen':'Fetal Abdomen Scan','Fetal brain':'Fetal Brain Scan','Fetal femur':'Fetal Femur Scan','Fetal thorax':'Fetal Thorax Scan'}
        cond = names.get(cls,cls)+f' (AI confidence: {round(conf*100,1)}%)'
        if cls=='Fetal abdomen': detail,action = 'Your fetal abdominal measurements are within the normal expected range.','Continue routine antenatal care. Next scan as per scheduled appointment.'
        elif cls=='Fetal femur': detail,action = 'Your baby\'s femur length is within the normal range. Growth on track.','No concerns at this stage. Continue regular antenatal check-ups.'
        elif cls=='Fetal thorax':detail,action = 'The fetal thorax has been assessed. A detailed cardiac evaluation is recommended.','Fetal echocardiography recommended. Please attend within 7 days.'
        else:                    detail,action = 'The fetal brain scan requires further detailed evaluation. An anomaly scan is recommended.','Please attend the fetal medicine unit within 3 to 5 days.'

    elif mtype == 'Combined Assessment':
        ct_cls = p.get('ct_predicted_class','')
        us_cls = p.get('us_predicted_class','')
        cond   = f'Multimodal Assessment — Lab + {CT_NAMES.get(ct_cls,"CT")} + {US_NAMES.get(us_cls,"Ultrasound")}'
        detail = f'Your combined assessment shows {sev.lower()} overall findings. All three tests have been individually reviewed.'
        action = 'Please follow your doctor\'s specific instructions for each component of your assessment.'
    else:
        cond,detail,action = 'Medical Assessment','Your results have been reviewed by your doctor.','Please follow your doctor\'s prescription carefully.'

    urgency = {'Normal':'No immediate hospital visit is required.','Mild':'No emergency — but please book your follow-up appointment soon.','Moderate':'Please do not delay your follow-up appointment.','Severe':'Please contact the hospital or your doctor today without delay.'}.get(sev,'')
    return f"Dear Patient,\n\nYour test results have been reviewed and approved by your doctor.\n\nCondition: {cond}\n\n{detail}\n\nNext Steps: {action}\n\n{urgency}\n\nRegards,\nMedAI Clinical System"


# ── MM RAG SUMMARY ────────────────────────────────────────────
def get_mm_rag(p):
    fus_sev = p.get('fusion_label','Normal')
    SCORE_TO_SEV = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}
    lab_sev = SCORE_TO_SEV.get(int(p.get('lab_score') or 0),'Normal')
    ct_sev  = SCORE_TO_SEV.get(int(p.get('ct_score')  or 0),'Normal')
    us_sev  = SCORE_TO_SEV.get(int(p.get('us_score')  or 0),'Normal')
    ct_cls  = p.get('ct_predicted_class','notumor')
    us_cls  = p.get('us_predicted_class','Fetal abdomen')

    disease = 'ckd' if p.get('ckd_severity') and p['ckd_severity'] not in ['Not tested',None] \
              else 'diabetes' if p.get('diabetes_severity_final') and p['diabetes_severity_final'] not in ['Not tested',None] \
              else 'thyroid'
    lab_key = f'lab_{disease}_{lab_sev.lower()}'
    ct_key  = f'ct_{ct_cls}'
    us_key  = 'us_brain' if 'brain' in us_cls.lower() else 'us_thorax' if 'thorax' in us_cls.lower() else 'us_femur' if 'femur' in us_cls.lower() else 'us_abdomen'

    def get_p(key, section):
        e = RAG_DATA.get(key,{})
        raw = e.get('raw_text','') if isinstance(e,dict) else ''
        parsed = parse_rag(raw)
        v = parsed.get(section,[])
        return v if isinstance(v,list) else [v] if v else []

    findings = []
    recs     = []
    cites    = []

    if lab_key in RAG_DATA:
        findings.append(f'[Lab — {lab_sev}]')
        findings.extend(get_p(lab_key,'key_findings')[:2])
        recs.extend(get_p(lab_key,'recommendations')[:2])
        cites.extend(RAG_DATA[lab_key].get('citations',[]))

    if ct_key in RAG_DATA:
        findings.append(f'[CT — {CT_NAMES.get(ct_cls,ct_cls)} — {ct_sev}]')
        findings.extend(get_p(ct_key,'key_findings')[:2])
        recs.extend(get_p(ct_key,'recommendations')[:2])
        cites.extend(RAG_DATA[ct_key].get('citations',[]))

    if us_key in RAG_DATA:
        findings.append(f'[Ultrasound — {US_NAMES.get(us_cls,us_cls)} — {us_sev}]')
        findings.extend(get_p(us_key,'key_findings')[:2])
        recs.extend(get_p(us_key,'recommendations')[:2])
        cites.extend(RAG_DATA[us_key].get('citations',[]))

    urgency_map = {'Normal':'Routine','Mild':'Routine','Moderate':'Semi-urgent','Severe':'Urgent'}
    summary = (f"This patient underwent multimodal assessment covering laboratory tests "
               f"({lab_sev} severity), CT brain imaging ({CT_NAMES.get(ct_cls,ct_cls)} — {ct_sev}), "
               f"and obstetric ultrasound ({US_NAMES.get(us_cls,us_cls)} — {us_sev}). "
               f"Combined MAX-fusion severity is {fus_sev}, indicating {urgency_map.get(fus_sev,'routine').lower()} clinical priority.")
    followup = {'Normal':'Routine review in 3 months for all modalities.','Mild':'Follow-up within 4 weeks.','Moderate':'Specialist review within 7 days for the most severe finding.','Severe':'Immediate specialist referral for the most critical finding.'}.get(fus_sev,'Follow-up as clinically indicated.')

    return {'clinical_summary':summary,'key_findings':findings,'recommendations':list(dict.fromkeys(recs)),'followup':followup,'urgency':urgency_map.get(fus_sev,'Routine'),'citations':list(dict.fromkeys(cites))}


# ── LOGIN ─────────────────────────────────────────────────────
def render_login():
    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown('<div style="margin-top:80px;">',unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;margin-bottom:36px;">'
            '<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);width:64px;height:64px;'
            'border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:32px;'
            'margin:0 auto 16px;box-shadow:0 8px 32px rgba(37,99,235,0.5);">🏥</div>'
            '<div style="font-size:30px;font-weight:800;color:#F0F6FF;letter-spacing:-0.5px;">MedAI Clinical System</div>'
            '<div style="font-size:15px;color:#4A6080;margin-top:6px;">Doctor Login Portal</div>'
            '</div>',unsafe_allow_html=True)
        st.markdown('<div style="background:linear-gradient(135deg,#0F1E33,#0A1525);border:2px solid #1E3A5F;border-radius:18px;padding:36px;">',unsafe_allow_html=True)
        st.markdown('<div style="font-size:13px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">Select Doctor</div>',unsafe_allow_html=True)
        doc_labels={f"{v['name']} — {v['dept']}":k for k,v in DOCTORS.items()}
        sel_id=doc_labels[st.selectbox('Doctor',list(doc_labels.keys()),label_visibility='collapsed',key='login_doc')]
        st.markdown('<div style="font-size:13px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin:16px 0 8px;">Password</div>',unsafe_allow_html=True)
        pwd=st.text_input('Password',type='password',placeholder='Enter password...',label_visibility='collapsed',key='login_pwd')
        st.markdown('<br>',unsafe_allow_html=True)
        if st.button('Login →',use_container_width=True,type='primary'):
            if pwd==DOCTORS[sel_id]['password']:
                st.session_state.logged_in=True; st.session_state.active_doctor=sel_id; st.rerun()
            else: st.error('Incorrect password.')
        st.markdown('<div style="font-size:12px;color:#2A3A50;text-align:center;margin-top:14px;">Demo password: 1234</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)


# ── DASHBOARD ─────────────────────────────────────────────────
def render_dashboard():
    active_id=st.session_state.active_doctor; active=DOCTORS[active_id]
    mtype=active['mtype']

    # Filter patients for this doctor
    my_patients = {pid:p for pid,p in ALL_PATIENTS.items() if p.get('doctor_id')==active_id}

    # Top bar
    st.markdown(
        f'<div style="background:linear-gradient(90deg,#080F1C,#0D1B2E);border-bottom:2px solid #1E3A5F;'
        f'padding:0 28px;height:64px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);width:38px;height:38px;'
        f'border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;">🏥</div>'
        f'<div><div style="font-size:18px;font-weight:800;color:#F0F6FF;">MedAI</div>'
        f'<div style="font-size:10px;color:#2A3A50;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;">Clinical System</div></div></div>'
        f'<div style="display:flex;align-items:center;gap:16px;">'
        f'<div><div style="font-size:14px;font-weight:700;color:#F0F6FF;">{active["name"]}</div>'
        f'<div style="font-size:12px;color:#4A6080;">{active["dept"]}  ·  {active["specialty"]}</div></div>'
        f'<div style="background:rgba(0,229,160,0.15);border:2px solid rgba(0,229,160,0.4);'
        f'color:#00E5A0;font-size:12px;font-weight:700;padding:5px 14px;border-radius:20px;">● Active</div>'
        f'</div></div>',unsafe_allow_html=True)

    c1,_,c2=st.columns([8,1,1])
    with c2:
        st.markdown('<div style="padding:10px 28px 0 0;">',unsafe_allow_html=True)
        if st.button('Logout',key='logout_btn'):
            st.session_state.logged_in=False; st.session_state.active_doctor=None; st.session_state.selected={}; st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div style="padding:20px 28px;">',unsafe_allow_html=True)
    icons={'Lab Report':'🧪','CT Scan':'🧠','Ultrasound':'🔬','Combined Assessment':'⚡'}
    st.markdown(f'<div style="font-size:24px;font-weight:800;color:#F0F6FF;margin-bottom:6px;">{icons.get(mtype,"📋")}  {active["dept"]} — Patient Reports</div>'
                f'<div style="font-size:14px;color:#4A6080;margin-bottom:20px;">Assigned to {active["name"]}</div>',unsafe_allow_html=True)

    # Stat cards
    sev_counts={s:sum(1 for p in my_patients.values() if p.get('_sev')==s) for s in ['Severe','Moderate','Mild','Normal']}
    s1,s2,s3,s4=st.columns(4)
    for col,(lbl,clr,g) in zip([s1,s2,s3,s4],[
        ('Severe','#FF3B5C','linear-gradient(135deg,rgba(255,59,92,0.25),rgba(255,59,92,0.05))'),
        ('Moderate','#FF7A35','linear-gradient(135deg,rgba(255,122,53,0.25),rgba(255,122,53,0.05))'),
        ('Mild','#FFD000','linear-gradient(135deg,rgba(255,208,0,0.25),rgba(255,208,0,0.05))'),
        ('Normal','#00E5A0','linear-gradient(135deg,rgba(0,229,160,0.25),rgba(0,229,160,0.05))'),
    ]):
        with col:
            st.markdown(f'<div style="background:{g};border:2px solid {clr}55;border-top:4px solid {clr};'
                        f'border-radius:14px;padding:18px;text-align:center;margin-bottom:18px;">'
                        f'<div style="font-size:40px;font-weight:800;color:{clr};line-height:1;">{sev_counts[lbl]}</div>'
                        f'<div style="font-size:13px;color:{clr};margin-top:8px;font-weight:700;">{lbl}</div>'
                        f'</div>',unsafe_allow_html=True)

    left,right=st.columns([1,2.5],gap='large')
    with left:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Patient Queue</div>',unsafe_allow_html=True)
        sev_filter=st.selectbox('Filter',['All','Severe','Moderate','Mild','Normal'],key='filter_'+active_id,label_visibility='collapsed')
        sev_ord={'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        sorted_pats=sorted(my_patients.items(),key=lambda x: sev_ord.get(x[1].get('_sev','Unknown'),4))
        for pid,p in sorted_pats:
            sev=p.get('_sev','Unknown')
            if sev_filter!='All' and sev!=sev_filter: continue
            clr=SEV_COLOR.get(sev,'#6B7A99')
            is_sel=st.session_state.selected.get(active_id)==pid
            dec=st.session_state.decisions.get(pid,{}).get('status','')
            icon={'APPROVED':'✓ ','REJECTED':'✗ '}.get(dec,'')
            if st.button(icon+pid+'  ·  '+sev,key='p_'+active_id+'_'+pid,use_container_width=True,type='primary' if is_sel else 'secondary'):
                st.session_state.selected[active_id]=pid; st.rerun()

    with right:
        sel_pid=st.session_state.selected.get(active_id)
        if not sel_pid or sel_pid not in my_patients:
            st.markdown('<div style="background:linear-gradient(135deg,#0A1525,#0D1B2E);border:2px dashed #1E3A5F;border-radius:16px;padding:80px;text-align:center;"><div style="font-size:40px;margin-bottom:14px;">👈</div><div style="font-size:16px;color:#4A6080;">Select a patient from the queue</div></div>',unsafe_allow_html=True)
        else:
            render_patient(my_patients[sel_pid], sel_pid, active_id)

    st.markdown('</div>',unsafe_allow_html=True)


def render_patient(p, pid, doc_id):
    doc=DOCTORS[doc_id]
    sev=p.get('_sev','Unknown'); clr=SEV_COLOR.get(sev,'#6B7A99'); bg=SEV_BG.get(sev,''); grad=SEV_GRAD.get(sev,'')
    mtype=p.get('modality_type','')
    urg={'Severe':'🚨 URGENT','Moderate':'⚠️ SEMI-URGENT','Mild':'📋 ROUTINE','Normal':'✅ ROUTINE'}.get(sev,'📋 REVIEW')
    urg_clr={'Severe':'#FF3B5C','Moderate':'#FF7A35','Mild':'#FFD000','Normal':'#00E5A0'}.get(sev,'#6B7A99')
    cur_dec=st.session_state.decisions.get(pid,{}).get('status','')

    # Patient header
    st.markdown(
        f'<div style="background:{grad};border:2px solid {clr}44;border-radius:16px;padding:20px 24px;margin-bottom:20px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="font-size:11px;font-weight:700;color:{clr};letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px;">Patient ID</div>'
        f'<div style="font-size:24px;font-weight:800;color:#F0F6FF;font-family:monospace;">{pid}</div>'
        f'<div style="font-size:13px;color:#4A6080;margin-top:6px;">{mtype}  ·  {doc["name"]}</div></div>'
        f'<div style="background:{bg};border:2px solid {urg_clr}66;border-radius:14px;padding:14px 24px;text-align:center;">'
        f'<div style="font-size:13px;font-weight:700;color:{urg_clr};margin-bottom:6px;">{urg}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{clr};">{sev}</div>'
        f'</div></div></div>',unsafe_allow_html=True)

    # Findings
    st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">Test Findings</div>',unsafe_allow_html=True)
    if mtype=='Lab Report':          render_lab(p,sev,clr)
    elif mtype=='CT Scan':           render_ct(p,sev,clr)
    elif mtype=='Ultrasound':        render_us(p,sev,clr)
    elif mtype=='Combined Assessment': render_combined(p,sev,clr)

    # RAG
    st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 14px;">AI Clinical Summary</div>',unsafe_allow_html=True)
    # ── RAG (FIXED) ─────────────────────────────────────────────
if mtype=='Combined Assessment':
    parsed = get_mm_rag(p)
    cites = parsed.pop('citations', [])
else:
    # 🔥 FIX: Use patient_id instead of rag_class_key
    pid = p.get('patient_id')

    raw = RAG_DATA.get(pid, "")

    # Your RAG file is plain text → parse directly
    parsed = parse_rag(raw) if raw else {}

    cites = []
    render_rag(parsed,cites)

    # Decision
    st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 12px;">Doctor Review & Decision</div>',unsafe_allow_html=True)
    if cur_dec=='APPROVED':
        ap=st.session_state.decisions[pid]
        st.markdown(f'<div style="background:linear-gradient(135deg,rgba(0,229,160,0.15),rgba(0,229,160,0.05));border:2px solid rgba(0,229,160,0.4);border-radius:14px;padding:20px 24px;">'
                    f'<div style="font-size:16px;font-weight:800;color:#00E5A0;margin-bottom:8px;">✅  Report Approved & Released</div>'
                    f'<div style="font-size:14px;color:#4A6080;">Approved by: <b style="color:#F0F6FF;">{ap["doctor"]}</b><br>Time: {ap["time"]}<br><span style="color:#00E5A0;font-weight:600;">Patient message sent successfully.</span></div></div>',unsafe_allow_html=True)
        with st.expander('📱 View Patient Message Sent'):
            st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:12px;padding:20px;font-size:14px;color:#C8D6E8;white-space:pre-wrap;line-height:1.8;">{ap["message"]}</div>',unsafe_allow_html=True)
    elif cur_dec=='REJECTED':
        st.markdown('<div style="background:linear-gradient(135deg,rgba(255,59,92,0.15),rgba(255,59,92,0.05));border:2px solid rgba(255,59,92,0.4);border-radius:14px;padding:20px 24px;">'
                    '<div style="font-size:16px;font-weight:800;color:#FF3B5C;margin-bottom:8px;">❌  Report Rejected</div>'
                    '<div style="font-size:14px;color:#4A6080;">Patient has NOT been notified. No message sent.</div></div>',unsafe_allow_html=True)
        if st.button('↺  Reset Decision',key='reset_'+pid):
            del st.session_state.decisions[pid]; st.rerun()
    else:
        notes=st.text_area('Clinical notes / prescription',placeholder='Add prescription, amendments, or clinical instructions...',height=100,key='notes_'+doc_id+'_'+pid,label_visibility='collapsed')
        pat_msg=get_msg(p)
        if notes: pat_msg+='\n\nDoctor\'s additional instructions:\n'+notes
        with st.expander('📱  Preview Patient Message'):
            st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:12px;padding:18px 22px;">'
                        f'<div style="font-size:12px;font-weight:700;color:#00E5A0;margin-bottom:10px;letter-spacing:0.08em;">MESSAGE TO PATIENT</div>'
                        f'<div style="font-size:14px;color:#C8D6E8;line-height:1.8;white-space:pre-wrap;">{pat_msg}</div></div>',unsafe_allow_html=True)
        st.markdown('<br>',unsafe_allow_html=True)
        b1,b2,b3=st.columns(3)
        with b1:
            if st.button('✅  Approve & Send',key='app_'+doc_id+'_'+pid,use_container_width=True,type='primary'):
                st.session_state.decisions[pid]={'status':'APPROVED','doctor':doc['name'],'time':datetime.now().strftime('%Y-%m-%d %H:%M'),'message':pat_msg}; st.rerun()
        with b2:
            if st.button('✏️  Approve with Edits',key='edit_'+doc_id+'_'+pid,use_container_width=True):
                st.session_state.decisions[pid]={'status':'APPROVED','doctor':doc['name'],'time':datetime.now().strftime('%Y-%m-%d %H:%M'),'message':pat_msg}; st.rerun()
        with b3:
            if st.button('❌  Reject',key='rej_'+doc_id+'_'+pid,use_container_width=True):
                st.session_state.decisions[pid]={'status':'REJECTED','doctor':doc['name'],'time':datetime.now().strftime('%Y-%m-%d %H:%M')}; st.rerun()


# ── FINDINGS ──────────────────────────────────────────────────
def render_lab(p,sev,clr):
    ckd = p.get('ckd_severity') or 'Not tested'
    dia = p.get('diabetes_severity_final') or 'Not tested'
    thy = p.get('thyroid_severity_final') or 'Not tested'
    # These come from JSON — already clean Python floats or None
    egfr    = n(p.get('egfr'))
    glucose = n(p.get('glucose'))
    tsh     = n(p.get('tsh'))
    free_t4 = n(p.get('free_t4'))
    disease = str(p.get('disease_type','')).lower()

    c1,c2,c3=st.columns(3)
    for col,(lbl,val) in zip([c1,c2,c3],[('Kidney Function',ckd),('Blood Sugar',dia),('Thyroid Function',thy)]):
        v=val if val and val not in ['Not tested','None','nan','Unknown'] else 'Not tested'
        vc=clr if v!='Not tested' else '#2A3A50'
        with col:
            st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:12px;padding:16px;margin-bottom:12px;">'
                        f'<div style="font-size:11px;font-weight:700;color:#4A6080;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{lbl}</div>'
                        f'<div style="font-size:17px;font-weight:700;color:{vc};">{v}</div></div>',unsafe_allow_html=True)

    rows=[]
    if 'ckd' in disease or 'kidney' in disease:
        if egfr is not None:
            st_='Normal' if egfr>=60 else 'Borderline' if egfr>=30 else 'Abnormal'
            stage='G1(≥90)' if egfr>=90 else 'G2(60-89)' if egfr>=60 else 'G3a(45-59)' if egfr>=45 else 'G3b(30-44)' if egfr>=30 else 'G4(15-29)' if egfr>=15 else 'G5(<15)'
            rows.append(ref_row('eGFR',fmt(egfr,'mL/min'),'≥90:G1(Normal) · 60-89:G2(Normal) · 45-59:G3a · 30-44:G3b · <30:G4-G5',st_))
            rows.append(ref_row('KDIGO Stage',stage+' — '+ckd,'G1-G2=Normal · G3=Moderate · G4-G5=Severe','Normal' if egfr>=60 else 'Borderline' if egfr>=45 else 'Abnormal'))
        else:
            ckd_st='Normal' if 'G1' in ckd or 'G2' in ckd else 'Borderline' if 'G3' in ckd else 'Abnormal' if ckd!='Not tested' else 'N/A'
            rows.append(ref_row('CKD Stage',ckd,'G1:≥90 · G2:60-89 · G3a:45-59 · G3b:30-44 · G4:15-29 · G5:<15',ckd_st))
            rows.append(ref_row('eGFR','Not measured this visit','eGFR not available — severity from clinical diagnosis','N/A'))
        rows.append(ref_row('Clinical Severity',sev,'KDIGO 2022: based on eGFR + albuminuria + symptoms','Normal' if sev=='Normal' else 'Borderline' if sev=='Mild' else 'Abnormal'))
        rows.append(ref_row('BP Target','—','<130/80 mmHg · ACE inhibitor if proteinuria','N/A'))
        src='KDIGO 2022 Clinical Practice Guideline for CKD'

    elif 'diabetes' in disease:
        dia_st='Normal' if dia=='Normal' else 'Borderline' if dia=='Mild' else 'Abnormal' if dia=='Severe' else 'N/A'
        if glucose is not None:
            gs='Normal' if glucose<100 else 'Borderline' if glucose<126 else 'Abnormal'
            rows.append(ref_row('Glucose (Fasting)',fmt(glucose,'mg/dL'),'Normal:<100 · Pre-diabetic:100-125 · Diabetic:≥126',gs))
        else:
            rows.append(ref_row('Glucose','Not measured','Normal:<100 · Pre-diabetic:100-125 · Diabetic:≥126','N/A'))
        rows.append(ref_row('Diabetes Severity',dia,'Normal · Mild:borderline control · Severe:poor control',dia_st))
        rows.append(ref_row('HbA1c Target','—','<7.0% (most patients) · <8.0% (elderly)','N/A'))
        rows.append(ref_row('Monitoring','—','Self-monitor glucose daily · HbA1c every 3 months','N/A'))
        src='ADA Standards of Medical Care in Diabetes 2024'

    elif 'thyroid' in disease:
        thy_st='Normal' if thy in ['Normal','Mild'] else 'Abnormal' if thy=='Severe' else 'N/A'
        if tsh is not None:
            ts='Normal' if 0.4<=tsh<=4.0 else 'Borderline' if tsh<=10 else 'Abnormal'
            interp='Euthyroid (Normal)' if 0.4<=tsh<=4.0 else 'Subclinical Hypothyroid' if tsh<=10 else 'Overt Hypothyroid'
            rows.append(ref_row('TSH Level',fmt(tsh,'mIU/L'),'Normal:0.4-4.0 · Subclinical:4.1-10.0 · Overt:>10.0',ts))
            rows.append(ref_row('TSH Interpretation',interp,'Subclinical=TSH↑ T4 normal · Overt=TSH↑↑ T4 low',ts))
        else:
            rows.append(ref_row('TSH Level','Not measured','Normal:0.4-4.0 mIU/L · Subclinical:4.1-10.0 · Overt:>10.0','N/A'))
        if free_t4 is not None:
            t4s='Normal' if 0.8<=free_t4<=1.8 else 'Abnormal'
            rows.append(ref_row('Free T4',fmt(free_t4,'ng/dL'),'Normal:0.8-1.8 ng/dL · Low=Hypothyroid',t4s))
        else:
            rows.append(ref_row('Free T4','Not measured','Normal:0.8-1.8 ng/dL','N/A'))
        rows.append(ref_row('Thyroid Status',thy,'Normal · Mild=Subclinical · Severe=Overt Hypothyroid',thy_st))
        rows.append(ref_row('Treatment Threshold','—','Levothyroxine if TSH>10 mIU/L or symptomatic at 4-10','N/A'))
        src='ATA/AACE Guidelines for Hypothyroidism 2023'
    else:
        src='WHO / Standard Clinical Guidelines'

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 10px;">Patient Values vs Clinical Guidelines</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,src),unsafe_allow_html=True)


def render_ct(p,sev,clr):
    cls=p.get('ct_predicted_class',''); conf=n(p.get('ct_confidence')) or 0
    name=CT_NAMES.get(cls,cls); desc=CT_DESC.get(cls,'')
    st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">CT Brain Imaging</div>'
                f'<div style="font-size:20px;font-weight:800;color:#F0F6FF;margin-bottom:6px;">{name}</div>'
                f'<div style="font-size:14px;color:#4A6080;margin-bottom:10px;">{desc}</div>'
                f'<div style="display:flex;gap:16px;"><span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
                f'<span style="color:#4A6080;font-size:13px;">AI Confidence: <b style="color:#F0F6FF;">{round(conf*100,1)}%</b></span></div></div>',unsafe_allow_html=True)
    t=CT_IMAGE.get(str(cls),('',''))
    if t[0] and os.path.exists(t[0]):
        st.markdown('<div style="font-size:13px;font-weight:700;color:#F0F6FF;margin-bottom:10px;">Scan Images & AI Attention Map</div>',unsafe_allow_html=True)
        gc1,gc2=st.columns(2)
        with gc1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original CT Scan</div>',unsafe_allow_html=True)
            st.image(t[0],use_column_width=True)
        with gc2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if t[1] and os.path.exists(t[1]): st.image(t[1],use_column_width=True)
        st.markdown('<div style="background:#0A1525;border:2px solid #1E3A5F;border-left:4px solid #7C3AED;border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:#4A6080;">🔍 <b style="color:#F0F6FF;">Grad-CAM:</b> Warm colours (red/yellow) = high AI attention regions.</div>',unsafe_allow_html=True)


def render_us(p,sev,clr):
    cls=p.get('predicted_class',''); conf=n(p.get('confidence')) or 0
    name=US_NAMES.get(cls,cls); desc=US_DESC.get(cls,'')
    st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Obstetric Ultrasound</div>'
                f'<div style="font-size:20px;font-weight:800;color:#F0F6FF;margin-bottom:6px;">{name}</div>'
                f'<div style="font-size:14px;color:#4A6080;margin-bottom:10px;">{desc}</div>'
                f'<div style="display:flex;gap:16px;"><span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
                f'<span style="color:#4A6080;font-size:13px;">AI Confidence: <b style="color:#F0F6FF;">{round(conf*100,1)}%</b></span></div></div>',unsafe_allow_html=True)
    t=US_IMAGE.get(str(cls),('',''))
    if t[0] and os.path.exists(t[0]):
        ug1,ug2=st.columns(2)
        with ug1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original Ultrasound</div>',unsafe_allow_html=True)
            st.image(t[0],use_column_width=True)
        with ug2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if t[1] and os.path.exists(t[1]): st.image(t[1],use_column_width=True)


def render_combined(p,sev,clr):
    c1,c2,c3,c4=st.columns(4)
    for col,(lbl,key) in zip([c1,c2,c3,c4],[('Lab','lab_score'),('CT','ct_score'),('Ultrasound','us_score'),('Fusion','fusion_score')]):
        val=n(p.get(key)); v=SCORE_MAP.get(int(val),'—') if val is not None else '—'; vc=SEV_COLOR.get(v,'#4A6080')
        with col:
            st.markdown(f'<div style="background:{SEV_BG.get(v,"rgba(74,96,128,0.1)")};border:2px solid {vc}55;border-radius:12px;padding:14px;text-align:center;margin-bottom:12px;">'
                        f'<div style="font-size:11px;font-weight:700;color:{vc};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                        f'<div style="font-size:24px;font-weight:800;color:{vc};">{v}</div></div>',unsafe_allow_html=True)

    ct_cls=p.get('ct_predicted_class',''); us_cls=p.get('us_predicted_class','')
    if ct_cls or us_cls:
        parts=[]
        if ct_cls: parts.append('🧠 CT: <b style="color:#F0F6FF;">'+CT_NAMES.get(ct_cls,ct_cls)+'</b>')
        if us_cls: parts.append('🔬 US: <b style="color:#F0F6FF;">'+US_NAMES.get(us_cls,us_cls)+'</b>')
        st.markdown('<div style="font-size:13px;color:#4A6080;margin-bottom:14px;">'+'  ·  '.join(parts)+'</div>',unsafe_allow_html=True)

    # Lab values for combined patients
    rows=[]
    egfr=n(p.get('egfr')); glucose=n(p.get('glucose')); tsh=n(p.get('tsh')); free_t4=n(p.get('free_t4'))
    ckd=p.get('ckd_severity') or ''; dia=p.get('diabetes_severity_final') or ''; thy=p.get('thyroid_severity_final') or ''

    if egfr is not None:
        st_='Normal' if egfr>=60 else 'Borderline' if egfr>=30 else 'Abnormal'
        rows.append(ref_row('eGFR',fmt(egfr,'mL/min'),'≥90:Normal · 60-89:G2 · 45-59:G3a · <30:G4-G5',st_))
    if ckd and ckd not in ['Not tested','']:
        rows.append(ref_row('CKD Stage',ckd,'G1-G2=Normal · G3=Moderate · G4-G5=Severe','Normal' if 'G1' in ckd or 'G2' in ckd else 'Borderline' if 'G3' in ckd else 'Abnormal'))
    if glucose is not None:
        gs='Normal' if glucose<100 else 'Borderline' if glucose<126 else 'Abnormal'
        rows.append(ref_row('Glucose',fmt(glucose,'mg/dL'),'Normal:<100 · Pre-diabetic:100-125 · Diabetic:≥126',gs))
    if dia and dia not in ['Not tested','']:
        rows.append(ref_row('Diabetes',dia,'Normal · Mild:borderline · Severe:poor control','Normal' if dia=='Normal' else 'Borderline' if dia=='Mild' else 'Abnormal'))
    if tsh is not None:
        ts='Normal' if 0.4<=tsh<=4.0 else 'Borderline' if tsh<=10 else 'Abnormal'
        rows.append(ref_row('TSH',fmt(tsh,'mIU/L'),'Normal:0.4-4.0 · Subclinical:4.1-10 · Overt:>10',ts))
    if free_t4 is not None:
        rows.append(ref_row('Free T4',fmt(free_t4,'ng/dL'),'Normal:0.8-1.8 ng/dL',('Normal' if 0.8<=free_t4<=1.8 else 'Abnormal')))
    if thy and thy not in ['Not tested','']:
        rows.append(ref_row('Thyroid',thy,'Normal · Mild=Subclinical · Severe=Overt','Normal' if thy in ['Normal','Mild'] else 'Abnormal'))

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin:8px 0 10px;">Lab Values vs Reference Ranges</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,'KDIGO 2022 · ADA 2024 · ATA/AACE 2023'),unsafe_allow_html=True)


def render_rag(parsed,citations):
    if not parsed or not parsed.get('clinical_summary'):
        st.markdown('<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:10px;padding:14px 18px;color:#4A6080;">RAG summary not available for this patient class.</div>',unsafe_allow_html=True)
        return

    st.markdown(f'<div style="background:linear-gradient(135deg,#130A2E,#0D1B2E);border:2px solid #3B1FA8;border-left:5px solid #7C3AED;border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#A78BFA;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Clinical Overview</div>'
                f'<div style="font-size:15px;color:#E8EDF5;line-height:1.85;">{parsed["clinical_summary"]}</div></div>',unsafe_allow_html=True)

    if parsed.get('key_findings'):
        fh=''.join([f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1E3A5F;"><span style="color:#C084FC;font-weight:700;font-size:16px;flex-shrink:0;">•</span><span style="font-size:14px;color:#C8D6E8;line-height:1.6;">{f}</span></div>' for f in parsed['key_findings']])
        st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:12px;padding:16px 20px;margin-bottom:14px;"><div style="font-size:11px;font-weight:700;color:#A78BFA;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Key Findings</div>{fh}</div>',unsafe_allow_html=True)

    if parsed.get('recommendations'):
        rh=''.join([f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #1E3A5F;"><span style="background:linear-gradient(135deg,#2563EB,#1D4ED8);color:white;font-weight:800;font-size:13px;padding:3px 10px;border-radius:8px;flex-shrink:0;min-width:28px;text-align:center;">{i+1}</span><span style="font-size:14px;color:#C8D6E8;line-height:1.6;">{r}</span></div>' for i,r in enumerate(parsed['recommendations'])])
        st.markdown(f'<div style="background:linear-gradient(135deg,rgba(0,229,160,0.08),rgba(0,229,160,0.02));border:2px solid rgba(0,229,160,0.3);border-left:5px solid #00E5A0;border-radius:14px;padding:16px 20px;margin-bottom:14px;"><div style="font-size:11px;font-weight:700;color:#00E5A0;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Clinical Recommendations</div>{rh}</div>',unsafe_allow_html=True)

    fu_col,ug_col=st.columns(2)
    with fu_col:
        if parsed.get('followup'):
            st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:12px;padding:14px 18px;margin-bottom:12px;"><div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Follow-up Plan</div><div style="font-size:14px;color:#F0F6FF;font-weight:600;">{parsed["followup"]}</div></div>',unsafe_allow_html=True)
    with ug_col:
        if parsed.get('urgency'):
            uc={'URGENT':'#FF3B5C','SEMI-URGENT':'#FF7A35','ROUTINE':'#00E5A0'}.get(parsed['urgency'].upper(),'#6B7A99')
            st.markdown(f'<div style="background:{SEV_BG.get({"URGENT":"Severe","SEMI-URGENT":"Moderate","ROUTINE":"Normal"}.get(parsed["urgency"].upper(),"Unknown"),"")};border:2px solid {uc}55;border-radius:12px;padding:14px 18px;margin-bottom:12px;"><div style="font-size:11px;font-weight:700;color:{uc};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Urgency</div><div style="font-size:20px;font-weight:800;color:{uc};">{parsed["urgency"]}</div></div>',unsafe_allow_html=True)

    if citations:
        st.markdown(f'<div style="background:#0A1525;border:2px solid #1E3A5F;border-radius:10px;padding:12px 18px;margin-bottom:14px;"><div style="font-size:11px;font-weight:700;color:#4A9EFF;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Guideline References</div><div style="font-size:13px;color:#2A3A50;font-family:monospace;">{"  ·  ".join(list(dict.fromkeys(citations)))}</div></div>',unsafe_allow_html=True)


# ── ENTRY POINT ───────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    render_dashboard()
