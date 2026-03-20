import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="MedAI — Doctor Dashboard", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#050B18!important;color:#E8EDF5!important;}
.stApp{background:#050B18!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stTextInput>div>div>input{background:#0D1A2E!important;color:#FFFFFF!important;border:2px solid #2563EB!important;border-radius:10px!important;font-size:16px!important;padding:10px 16px!important;}
.stSelectbox>div>div{background:#0D1A2E!important;color:#FFFFFF!important;border:2px solid #2563EB!important;border-radius:10px!important;font-size:15px!important;}
.stTextArea textarea{background:#0D1A2E!important;color:#FFFFFF!important;border:2px solid #2563EB!important;border-radius:10px!important;font-size:14px!important;}
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:700!important;font-size:15px!important;border-radius:10px!important;padding:11px 22px!important;transition:all 0.2s!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2563EB,#7C3AED)!important;border:none!important;color:white!important;box-shadow:0 4px 20px rgba(37,99,235,0.5)!important;}
.stButton>button[kind="primary"]:hover{transform:translateY(-1px)!important;box-shadow:0 6px 25px rgba(37,99,235,0.7)!important;}
.stButton>button[kind="secondary"]{background:#0D1A2E!important;border:2px solid #2563EB!important;color:#60A5FA!important;}
.stButton>button[kind="secondary"]:hover{background:#1E3A5F!important;color:#FFFFFF!important;}
.stTabs [data-baseweb="tab-list"]{background:#080F1C!important;border-bottom:2px solid #2563EB!important;padding:0 8px!important;}
.stTabs [data-baseweb="tab"]{font-size:15px!important;font-weight:600!important;color:#60A5FA!important;padding:14px 22px!important;}
.stTabs [aria-selected="true"]{color:#FFFFFF!important;border-bottom:3px solid #7C3AED!important;background:transparent!important;}
.stExpander{background:#0D1A2E!important;border:2px solid #2563EB!important;border-radius:12px!important;}
.stExpander summary{color:#60A5FA!important;font-weight:700!important;}
hr{border-color:#2563EB!important;}
div[data-testid="stSelectbox"] label{color:#60A5FA!important;font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────
SEV_COLOR = {'Normal':'#00E5A0','Mild':'#FFD000','Moderate':'#FF7A35','Severe':'#FF3B5C','Unknown':'#6B7A99'}
SEV_BG    = {'Normal':'rgba(0,229,160,0.12)','Mild':'rgba(255,208,0,0.12)','Moderate':'rgba(255,122,53,0.12)','Severe':'rgba(255,59,92,0.12)','Unknown':'rgba(107,122,153,0.1)'}
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

# ── PROFESSIONAL HERO IMAGES (Unsplash free-use URLs) ────────
HERO_IMG        = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1200&q=80"  # doctor + technology
HERO_IMG_LOGIN  = "https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=900&q=80"   # medical lab
DEPT_IMGS = {
    'Lab Report':          "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=600&q=80",
    'CT Scan':             "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&q=80",
    'Ultrasound':          "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&q=80",
    'Combined Assessment': "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=600&q=80",
}

# ── LOAD DATA ─────────────────────────────────────────────────
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
for k,v in {'logged_in':False,'active_doctor':None,'selected':{},'decisions':{},'reject_resubmit':{}}.items():
    if k not in st.session_state: st.session_state[k]=v

# ── HELPERS ───────────────────────────────────────────────────
def n(v):
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
    """
    Robust parser for GPT-4o-mini RAG output.
    Handles multiple bullet styles: •  -  *  1.  1)
    Handles section headers with or without trailing colon.
    Handles FOLLOW-UP / FOLLOW UP / FOLLOW-UP PLAN variants.
    Works whether raw is a plain string or a dict with 'raw_text'.
    """
    if isinstance(raw, dict):
        raw = raw.get('raw_text', '') or ''
    if not raw or raw == 'Summary unavailable':
        return {'clinical_summary':'','key_findings':[],'recommendations':[],'followup':'','urgency':''}

    import re
    s = {'clinical_summary':'','key_findings':[],'recommendations':[],'followup':'','urgency':''}

    # Section header detection — order matters (most specific first)
    SECTION_RE = [
        (re.compile(r'CLINICAL\s+SUMMARY',        re.I), 'summary'),
        (re.compile(r'KEY\s+FINDINGS?',            re.I), 'findings'),
        (re.compile(r'RECOMMENDATIONS?',           re.I), 'recommendations'),
        (re.compile(r'FOLLOW[\s\-]*UP(\s+PLAN)?',  re.I), 'followup'),
        (re.compile(r'URGENCY',                    re.I), 'urgency'),
    ]

    # Bullet prefix — strip •, -, *, digits+dot, digits+paren
    BULLET_RE = re.compile(r'^[\•\-\*]\s*|^\d+[\.\)]\s*')

    cur = None
    lines = raw.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is a section header
        matched_section = None
        for pattern, section_name in SECTION_RE:
            if pattern.search(stripped):
                # Make sure it's actually a header line (short, ends with colon or IS just the keyword)
                clean_line = re.sub(r'[:\*\_\#]+', '', stripped).strip()
                if len(clean_line) < 60:          # headers are short
                    matched_section = section_name
                    # Inline urgency: "URGENCY: ROUTINE"
                    if section_name == 'urgency':
                        after_colon = stripped.split(':', 1)[-1].strip()
                        if after_colon and after_colon.upper() != stripped.upper():
                            s['urgency'] = after_colon
                            cur = None
                        else:
                            cur = 'urgency'
                    else:
                        cur = section_name
                    break

        if matched_section:
            continue  # header line consumed, move to next line

        # Content lines — route to current section
        if cur == 'summary':
            s['clinical_summary'] += stripped + ' '

        elif cur == 'findings':
            clean = BULLET_RE.sub('', stripped).strip()
            if clean:
                s['key_findings'].append(clean)

        elif cur == 'recommendations':
            clean = BULLET_RE.sub('', stripped).strip()
            if clean:
                s['recommendations'].append(clean)

        elif cur == 'followup':
            clean = BULLET_RE.sub('', stripped).strip()
            if clean:
                s['followup'] += clean + ' '

        elif cur == 'urgency':
            clean = BULLET_RE.sub('', stripped).strip()
            if clean and not s['urgency']:
                s['urgency'] = clean

    # Tidy up
    s['clinical_summary'] = s['clinical_summary'].strip()
    s['followup']         = s['followup'].strip()

    # Normalise urgency to one of the known tokens
    urg_raw = s['urgency'].upper()
    if 'URGENT' in urg_raw and 'SEMI' not in urg_raw:
        s['urgency'] = 'URGENT'
    elif 'SEMI' in urg_raw or 'MODERATE' in urg_raw:
        s['urgency'] = 'SEMI-URGENT'
    elif 'ROUTINE' in urg_raw or 'NORMAL' in urg_raw or 'MILD' in urg_raw:
        s['urgency'] = 'ROUTINE'

    return s

def ref_row(param, pat_val, guide, status):
    pv_clr={'Normal':'#00E5A0','Abnormal':'#FF3B5C','Borderline':'#FFD000','N/A':'#6B7A99'}.get(status,'#6B7A99')
    return (
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;padding:10px 0;border-bottom:1px solid #1E3A5F;align-items:center;">'
        f'<div style="font-size:13px;font-weight:600;color:#FFFFFF;">{param}</div>'
        f'<div style="font-size:13px;font-weight:700;color:{pv_clr};">{pat_val}</div>'
        f'<div style="font-size:12px;color:#94A3B8;line-height:1.5;">{guide}</div>'
        f'<div>{sev_badge(status)}</div>'
        '</div>'
    )

def ref_table(rows, source):
    header=(
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;border-bottom:2px solid #2563EB;padding-bottom:8px;margin-bottom:4px;">'
        +''.join([f'<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.06em;">{h}</div>'
                  for h in ['Parameter','Patient Value','Guideline Range','Status']])
        +'</div>'
    )
    return (
        '<div style="background:#0D1A2E;border:2px solid #2563EB;'
        'border-left:4px solid #60A5FA;border-radius:14px;padding:16px 20px;margin-bottom:14px;">'
        +header+''.join(rows)+
        f'<div style="font-size:11px;color:#4A6080;margin-top:10px;font-style:italic;">Source: {source}</div>'
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
            if sev=='Normal':   detail,action = 'Your kidney function is within an acceptable range.','Stay well-hydrated, avoid NSAIDs. Next kidney function check in 3 months.'
            elif sev=='Mild':   detail,action = 'Your kidney function shows mild reduction.','Follow low-sodium, low-protein diet. Nephrology follow-up within 4 weeks.'
            else:               detail,action = 'Your kidney function is significantly reduced.','Please contact your nephrologist immediately.'
        elif 'diabetes' in disease:
            gluc_str = f' (Glucose: {round(glucose_v,1)} mg/dL)' if glucose_v else ''
            cond  = f'Diabetes Mellitus{gluc_str}'
            if sev=='Normal':   detail,action = 'Your blood glucose levels are well controlled.','Continue current medication and diet. Review in 3 months.'
            elif sev=='Mild':   detail,action = 'Your blood glucose is mildly elevated.','Follow low-sugar diet. Follow-up in 2 to 4 weeks.'
            else:
                gd = f'{round(glucose_v,1)} mg/dL' if glucose_v else 'significantly elevated'
                detail,action = f'Your blood glucose is significantly elevated ({gd}).','Please contact your doctor today. Do not skip medication.'
        elif 'thyroid' in disease:
            tsh_str = f' (TSH: {round(tsh_v,2)} mIU/L)' if tsh_v else ''
            cond  = f'Thyroid Disorder{tsh_str}'
            if sev=='Normal':   detail,action = 'Your thyroid hormone levels are within normal range.','Continue current thyroid medication. Routine check in 6 months.'
            elif sev=='Mild':   detail,action = 'Your TSH is mildly elevated (subclinical hypothyroidism).','Follow-up in 4 to 6 weeks.'
            else:               detail,action = 'Your thyroid levels indicate overt hypothyroidism.','Begin or adjust Levothyroxine as prescribed. Review in 6 to 8 weeks.'
        else:
            cond,detail,action = 'Chronic Disease Assessment','Your lab results have been reviewed.','Follow your doctor\'s prescription carefully.'

    elif mtype == 'CT Scan':
        cls  = p.get('ct_predicted_class','')
        conf = n(p.get('ct_confidence')) or 0
        names= {'notumor':'No Brain Tumour','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}
        cond = names.get(cls,cls)+f' (AI confidence: {round(conf*100,1)}%)'
        if cls=='notumor':     detail,action = 'Your brain CT scan shows no signs of any tumour.','Routine follow-up as advised by your neurologist.'
        elif cls=='pituitary': detail,action = 'A small benign pituitary gland tumour has been identified.','An endocrinology referral has been arranged.'
        elif cls=='meningioma':detail,action = 'A meningioma has been identified — typically slow-growing.','A neurosurgery consultation has been arranged.'
        else:                  detail,action = 'A glioma has been identified on your brain scan.','An urgent oncology referral has been made. Attend the hospital soon.'

    elif mtype == 'Ultrasound':
        cls  = p.get('predicted_class','')
        conf = n(p.get('confidence')) or 0
        names= {'Fetal abdomen':'Fetal Abdomen Scan','Fetal brain':'Fetal Brain Scan','Fetal femur':'Fetal Femur Scan','Fetal thorax':'Fetal Thorax Scan'}
        cond = names.get(cls,cls)+f' (AI confidence: {round(conf*100,1)}%)'
        if cls=='Fetal abdomen': detail,action = 'Your fetal abdominal measurements are within the normal range.','Continue routine antenatal care.'
        elif cls=='Fetal femur': detail,action = 'Your baby\'s femur length is within normal range.','Continue regular antenatal check-ups.'
        elif cls=='Fetal thorax':detail,action = 'The fetal thorax has been assessed. Cardiac evaluation recommended.','Fetal echocardiography recommended within 7 days.'
        else:                    detail,action = 'The fetal brain scan requires further evaluation.','Please attend the fetal medicine unit within 3 to 5 days.'

    elif mtype == 'Combined Assessment':
        ct_cls = p.get('ct_predicted_class','')
        us_cls = p.get('us_predicted_class','')
        cond   = f'Multimodal Assessment — Lab + {CT_NAMES.get(ct_cls,"CT")} + {US_NAMES.get(us_cls,"Ultrasound")}'
        detail = f'Your combined assessment shows {sev.lower()} overall findings.'
        action = 'Please follow your doctor\'s specific instructions for each component.'
    else:
        cond,detail,action = 'Medical Assessment','Your results have been reviewed by your doctor.','Follow your doctor\'s prescription carefully.'

    urgency = {'Normal':'No immediate hospital visit is required.','Mild':'No emergency — please book your follow-up appointment soon.','Moderate':'Please do not delay your follow-up appointment.','Severe':'Please contact the hospital or your doctor today without delay.'}.get(sev,'')
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

    findings=[]; recs=[]; cites=[]
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
    summary = (f"This patient underwent multimodal assessment covering laboratory tests ({lab_sev} severity), "
               f"CT brain imaging ({CT_NAMES.get(ct_cls,ct_cls)} — {ct_sev}), and obstetric ultrasound "
               f"({US_NAMES.get(us_cls,us_cls)} — {us_sev}). Combined MAX-fusion severity is {fus_sev}.")
    followup = {'Normal':'Routine review in 3 months.','Mild':'Follow-up within 4 weeks.','Moderate':'Specialist review within 7 days.','Severe':'Immediate specialist referral required.'}.get(fus_sev,'Follow-up as clinically indicated.')
    return {'clinical_summary':summary,'key_findings':findings,'recommendations':list(dict.fromkeys(recs)),'followup':followup,'urgency':urgency_map.get(fus_sev,'Routine'),'citations':list(dict.fromkeys(cites))}


# ── LOGIN PAGE ────────────────────────────────────────────────
def render_login():
    # Full-page hero background
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #050B18 0%, #0D1A2E 50%, #050B18 100%) !important;
    }}
    </style>
    <div style="position:relative;width:100%;height:220px;overflow:hidden;border-radius:0 0 24px 24px;margin-bottom:0;">
        <img src="{HERO_IMG_LOGIN}" style="width:100%;height:100%;object-fit:cover;opacity:0.25;"/>
        <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent,#050B18);"></div>
        <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;">
            <div style="font-size:52px;margin-bottom:10px;filter:drop-shadow(0 0 20px rgba(37,99,235,0.8));">🏥</div>
            <div style="font-size:36px;font-weight:800;color:#FFFFFF;letter-spacing:-1px;text-shadow:0 2px 20px rgba(37,99,235,0.8);">MedAI Clinical System</div>
            <div style="font-size:15px;color:#60A5FA;margin-top:6px;font-weight:500;">AI-Powered · Doctor-in-the-Loop · Medical Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _,col,_=st.columns([1,1.8,1])
    with col:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0D1A2E,#0A1525);border:2px solid #2563EB;border-radius:20px;padding:36px;box-shadow:0 20px 60px rgba(37,99,235,0.3);margin-top:24px;">
            <div style="text-align:center;margin-bottom:28px;">
                <div style="font-size:14px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.15em;">Secure Doctor Portal</div>
                <div style="font-size:13px;color:#4A6080;margin-top:4px;">Please sign in to access patient reports</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:13px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">👨‍⚕️ Select Doctor</div>', unsafe_allow_html=True)
        doc_labels={f"{v['name']} — {v['dept']}":k for k,v in DOCTORS.items()}
        sel_id=doc_labels[st.selectbox('Doctor',list(doc_labels.keys()),label_visibility='collapsed',key='login_doc')]

        st.markdown('<div style="font-size:13px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin:16px 0 8px;">🔐 Password</div>', unsafe_allow_html=True)
        pwd=st.text_input('Password',type='password',placeholder='Enter password...',label_visibility='collapsed',key='login_pwd')

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('🔓  Sign In →',use_container_width=True,type='primary'):
            if pwd==DOCTORS[sel_id]['password']:
                st.session_state.logged_in=True; st.session_state.active_doctor=sel_id; st.rerun()
            else:
                st.error('❌ Incorrect password. Please try again.')

        st.markdown("""
            <div style="text-align:center;margin-top:20px;padding-top:16px;border-top:1px solid #1E3A5F;">
                <div style="font-size:12px;color:#2A3A50;">Demo password: <span style="color:#60A5FA;font-weight:700;">1234</span></div>
                <div style="font-size:11px;color:#1E3A5F;margin-top:6px;">🔒 All sessions are encrypted and logged</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Feature badges below login
        st.markdown("""
        <div style="display:flex;gap:10px;justify-content:center;margin-top:20px;flex-wrap:wrap;">
            <span style="background:rgba(37,99,235,0.15);border:1px solid #2563EB;color:#60A5FA;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">🧠 AI Diagnostics</span>
            <span style="background:rgba(124,58,237,0.15);border:1px solid #7C3AED;color:#C084FC;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">🔬 Lab Analysis</span>
            <span style="background:rgba(0,229,160,0.12);border:1px solid #00E5A0;color:#00E5A0;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">✅ Doctor Review</span>
            <span style="background:rgba(255,122,53,0.12);border:1px solid #FF7A35;color:#FF7A35;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">📱 Patient Alerts</span>
        </div>
        """, unsafe_allow_html=True)


# ── DASHBOARD ─────────────────────────────────────────────────
def render_dashboard():
    active_id=st.session_state.active_doctor; active=DOCTORS[active_id]
    mtype=active['mtype']
    my_patients = {pid:p for pid,p in ALL_PATIENTS.items() if p.get('doctor_id')==active_id}

    # ── Top navigation bar ────────────────────────────────────
    st.markdown(
        f'<div style="background:linear-gradient(90deg,#080F1C,#0D1A2E);border-bottom:2px solid #2563EB;'
        f'padding:0 28px;height:68px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);width:42px;height:42px;'
        f'border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;'
        f'box-shadow:0 4px 15px rgba(37,99,235,0.5);">🏥</div>'
        f'<div><div style="font-size:20px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;">MedAI</div>'
        f'<div style="font-size:10px;color:#4A6080;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;">Clinical Intelligence System</div></div></div>'
        f'<div style="display:flex;align-items:center;gap:16px;">'
        f'<div style="background:rgba(37,99,235,0.15);border:1px solid #2563EB;border-radius:10px;padding:8px 16px;">'
        f'<div style="font-size:14px;font-weight:700;color:#FFFFFF;">{active["name"]}</div>'
        f'<div style="font-size:11px;color:#60A5FA;">{active["dept"]}  ·  {active["specialty"]}</div></div>'
        f'<div style="background:rgba(0,229,160,0.15);border:2px solid rgba(0,229,160,0.5);'
        f'color:#00E5A0;font-size:12px;font-weight:700;padding:6px 16px;border-radius:20px;">● Online</div>'
        f'</div></div>',unsafe_allow_html=True)

    # Logout button row
    _,_,logout_col = st.columns([8,1,1])
    with logout_col:
        st.markdown('<div style="padding:8px 28px 0 0;">', unsafe_allow_html=True)
        if st.button('🚪 Logout', key='logout_btn'):
            st.session_state.logged_in=False; st.session_state.active_doctor=None; st.session_state.selected={}; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:20px 28px;">', unsafe_allow_html=True)

    # ── Department hero banner ────────────────────────────────
    dept_img = DEPT_IMGS.get(mtype, HERO_IMG)
    icons={'Lab Report':'🧪','CT Scan':'🧠','Ultrasound':'🔬','Combined Assessment':'⚡'}
    icon = icons.get(mtype,'📋')
    st.markdown(f"""
    <div style="position:relative;width:100%;height:140px;overflow:hidden;border-radius:16px;margin-bottom:20px;">
        <img src="{dept_img}" style="width:100%;height:100%;object-fit:cover;opacity:0.2;"/>
        <div style="position:absolute;inset:0;background:linear-gradient(90deg,#0D1A2E,transparent 60%,#0D1A2E);"></div>
        <div style="position:absolute;inset:0;display:flex;align-items:center;padding:0 28px;gap:18px;">
            <div style="font-size:48px;filter:drop-shadow(0 0 12px rgba(255,255,255,0.3));">{icon}</div>
            <div>
                <div style="font-size:26px;font-weight:800;color:#FFFFFF;text-shadow:0 2px 10px rgba(0,0,0,0.5);">{active["dept"]} — Patient Reports</div>
                <div style="font-size:14px;color:#60A5FA;margin-top:4px;font-weight:500;">Assigned to {active["name"]}  ·  {active["specialty"]}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stat cards ────────────────────────────────────────────
    sev_counts={s:sum(1 for p in my_patients.values() if p.get('_sev')==s) for s in ['Severe','Moderate','Mild','Normal']}
    approved_count = sum(1 for pid in my_patients if st.session_state.decisions.get(pid,{}).get('status')=='APPROVED')
    pending_count  = len(my_patients) - sum(1 for pid in my_patients if st.session_state.decisions.get(pid,{}))

    s1,s2,s3,s4,s5,s6=st.columns(6)
    stat_data = [
        (s1,'Severe',     sev_counts['Severe'],  '#FF3B5C','linear-gradient(135deg,rgba(255,59,92,0.25),rgba(255,59,92,0.05))','🚨'),
        (s2,'Moderate',   sev_counts['Moderate'],'#FF7A35','linear-gradient(135deg,rgba(255,122,53,0.25),rgba(255,122,53,0.05))','⚠️'),
        (s3,'Mild',       sev_counts['Mild'],     '#FFD000','linear-gradient(135deg,rgba(255,208,0,0.25),rgba(255,208,0,0.05))','📋'),
        (s4,'Normal',     sev_counts['Normal'],   '#00E5A0','linear-gradient(135deg,rgba(0,229,160,0.25),rgba(0,229,160,0.05))','✅'),
        (s5,'Approved',   approved_count,         '#60A5FA','linear-gradient(135deg,rgba(96,165,250,0.25),rgba(96,165,250,0.05))','✔️'),
        (s6,'Pending',    pending_count,          '#C084FC','linear-gradient(135deg,rgba(192,132,252,0.25),rgba(192,132,252,0.05))','⏳'),
    ]
    for col,lbl,val,clr,g,ico in stat_data:
        with col:
            st.markdown(f'<div style="background:{g};border:2px solid {clr}55;border-top:4px solid {clr};'
                        f'border-radius:14px;padding:16px;text-align:center;margin-bottom:18px;">'
                        f'<div style="font-size:22px;margin-bottom:4px;">{ico}</div>'
                        f'<div style="font-size:36px;font-weight:800;color:{clr};line-height:1;">{val}</div>'
                        f'<div style="font-size:12px;color:{clr};margin-top:6px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">{lbl}</div>'
                        f'</div>', unsafe_allow_html=True)

    # ── Patient queue + detail ────────────────────────────────
    left,right=st.columns([1,2.5],gap='large')
    with left:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">👥 Patient Queue</div>', unsafe_allow_html=True)
        sev_filter=st.selectbox('Filter',['All','Severe','Moderate','Mild','Normal'],key='filter_'+active_id,label_visibility='collapsed')
        sev_ord={'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        sorted_pats=sorted(my_patients.items(),key=lambda x: sev_ord.get(x[1].get('_sev','Unknown'),4))
        for pid,p in sorted_pats:
            sev=p.get('_sev','Unknown')
            if sev_filter!='All' and sev!=sev_filter: continue
            clr=SEV_COLOR.get(sev,'#6B7A99')
            is_sel=st.session_state.selected.get(active_id)==pid
            dec=st.session_state.decisions.get(pid,{}).get('status','')
            icon_map={'APPROVED':'✅ ','REJECTED':'❌ ','REVOKED':'🔄 '}
            icon_pre=icon_map.get(dec,'')
            if st.button(icon_pre+pid+'  ·  '+sev,key='p_'+active_id+'_'+pid,use_container_width=True,type='primary' if is_sel else 'secondary'):
                st.session_state.selected[active_id]=pid; st.rerun()

    with right:
        sel_pid=st.session_state.selected.get(active_id)
        if not sel_pid or sel_pid not in my_patients:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0A1525,#0D1A2E);border:2px dashed #2563EB;border-radius:16px;padding:60px;text-align:center;">
                <div style="font-size:50px;margin-bottom:16px;">👈</div>
                <div style="font-size:18px;color:#60A5FA;font-weight:600;">Select a Patient</div>
                <div style="font-size:14px;color:#4A6080;margin-top:8px;">Choose a patient from the queue to view their report</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            render_patient(my_patients[sel_pid], sel_pid, active_id)

    st.markdown('</div>', unsafe_allow_html=True)


# ── PATIENT DETAIL ─────────────────────────────────────────────
def render_patient(p, pid, doc_id):
    doc=DOCTORS[doc_id]
    sev=p.get('_sev','Unknown'); clr=SEV_COLOR.get(sev,'#6B7A99'); bg=SEV_BG.get(sev,''); grad=SEV_GRAD.get(sev,'')
    mtype=p.get('modality_type','')
    urg={'Severe':'🚨 URGENT','Moderate':'⚠️ SEMI-URGENT','Mild':'📋 ROUTINE','Normal':'✅ ROUTINE'}.get(sev,'📋 REVIEW')
    urg_clr={'Severe':'#FF3B5C','Moderate':'#FF7A35','Mild':'#FFD000','Normal':'#00E5A0'}.get(sev,'#6B7A99')
    cur_dec=st.session_state.decisions.get(pid,{}).get('status','')

    # ── Patient header card ────────────────────────────────────
    st.markdown(
        f'<div style="background:{grad};border:2px solid {clr}55;border-radius:16px;padding:20px 24px;margin-bottom:20px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="font-size:11px;font-weight:700;color:{clr};letter-spacing:0.12em;text-transform:uppercase;margin-bottom:6px;">Patient ID</div>'
        f'<div style="font-size:26px;font-weight:800;color:#FFFFFF;font-family:monospace;">{pid}</div>'
        f'<div style="font-size:13px;color:#94A3B8;margin-top:6px;">{mtype}  ·  {doc["name"]}</div></div>'
        f'<div style="background:{bg};border:2px solid {urg_clr}66;border-radius:14px;padding:14px 24px;text-align:center;">'
        f'<div style="font-size:13px;font-weight:700;color:{urg_clr};margin-bottom:6px;">{urg}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{clr};">{sev}</div>'
        f'</div></div></div>',unsafe_allow_html=True)

    # ── Test Findings ──────────────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;">🔬 Test Findings</div>', unsafe_allow_html=True)
    if mtype=='Lab Report':          render_lab(p,sev,clr)
    elif mtype=='CT Scan':           render_ct(p,sev,clr)
    elif mtype=='Ultrasound':        render_us(p,sev,clr)
    elif mtype=='Combined Assessment': render_combined(p,sev,clr)

    # ── AI Clinical Summary ────────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 14px;">🤖 AI Clinical Summary</div>', unsafe_allow_html=True)
    if mtype == 'Combined Assessment':
        parsed = get_mm_rag(p)
        cites = parsed.pop('citations', [])
    else:
        raw = RAG_DATA.get(pid, "")
        parsed = parse_rag(raw) if raw else {}
        cites = []
    render_rag(parsed, cites)

    # ── Doctor Decision Section ────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.1em;margin:24px 0 12px;">👨‍⚕️ Doctor Review & Decision</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # CASE 1: APPROVED
    # ══════════════════════════════════════════════════════════
    if cur_dec == 'APPROVED':
        ap = st.session_state.decisions[pid]
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(0,229,160,0.15),rgba(0,229,160,0.05));'
            f'border:2px solid rgba(0,229,160,0.5);border-radius:14px;padding:20px 24px;margin-bottom:16px;">'
            f'<div style="font-size:16px;font-weight:800;color:#00E5A0;margin-bottom:10px;">✅ Report Approved & Released to Patient</div>'
            f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
            f'<div style="font-size:13px;color:#94A3B8;">👨‍⚕️ Approved by: <b style="color:#FFFFFF;">{ap["doctor"]}</b></div>'
            f'<div style="font-size:13px;color:#94A3B8;">🕐 Time: <b style="color:#FFFFFF;">{ap["time"]}</b></div>'
            f'<div style="font-size:13px;color:#00E5A0;font-weight:600;">📱 Patient message sent successfully</div>'
            f'</div></div>',unsafe_allow_html=True)

        # Show doctor's additional notes if any
        if ap.get('notes'):
            st.markdown(
                f'<div style="background:rgba(96,165,250,0.1);border:2px solid rgba(96,165,250,0.4);border-left:4px solid #60A5FA;border-radius:12px;padding:16px 20px;margin-bottom:16px;">'
                f'<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">📝 Doctor\'s Prescription / Notes Added</div>'
                f'<div style="font-size:14px;color:#FFFFFF;line-height:1.7;white-space:pre-wrap;">{ap["notes"]}</div>'
                f'</div>', unsafe_allow_html=True)

        with st.expander('📱 View Patient Message Sent'):
            st.markdown(f'<div style="background:#0D1A2E;border:2px solid #2563EB;border-radius:12px;padding:20px;font-size:14px;color:#E8EDF5;white-space:pre-wrap;line-height:1.8;">{ap["message"]}</div>', unsafe_allow_html=True)

        # ── REVOKE APPROVAL ───────────────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(255,122,53,0.1),rgba(255,59,92,0.05));
        border:2px solid rgba(255,122,53,0.4);border-radius:14px;padding:18px 22px;margin-top:16px;">
            <div style="font-size:14px;font-weight:800;color:#FF7A35;margin-bottom:6px;">⚠️ Revoke Approval</div>
            <div style="font-size:13px;color:#94A3B8;margin-bottom:12px;">
                If this approval was made in error, you can revoke it. The patient will be notified that the report
                is under further review and the original message will be retracted.
            </div>
        </div>
        """, unsafe_allow_html=True)
        revoke_reason = st.text_area(
            'Reason for revoking approval',
            placeholder='State the clinical reason for revoking this approval (e.g., incorrect dosage, updated test results, wrong patient)...',
            height=90,
            key='revoke_reason_' + pid
        )
        rev_col1, rev_col2 = st.columns([1,3])
        with rev_col1:
            if st.button('🔄 Revoke Approval', key='revoke_'+pid, use_container_width=True):
                if revoke_reason.strip():
                    st.session_state.decisions[pid] = {
                        'status': 'REVOKED',
                        'doctor': doc['name'],
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'revoke_reason': revoke_reason.strip(),
                        'original_message': ap.get('message','')
                    }
                    st.rerun()
                else:
                    st.warning('⚠️ Please provide a reason for revoking the approval.')

    # ══════════════════════════════════════════════════════════
    # CASE 2: REVOKED
    # ══════════════════════════════════════════════════════════
    elif cur_dec == 'REVOKED':
        rv = st.session_state.decisions[pid]
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,122,53,0.15),rgba(255,122,53,0.05));'
            f'border:2px solid rgba(255,122,53,0.5);border-radius:14px;padding:20px 24px;margin-bottom:16px;">'
            f'<div style="font-size:16px;font-weight:800;color:#FF7A35;margin-bottom:10px;">🔄 Approval Revoked — Under Review</div>'
            f'<div style="font-size:13px;color:#94A3B8;margin-bottom:10px;">Revoked by: <b style="color:#FFFFFF;">{rv["doctor"]}</b>  ·  Time: <b style="color:#FFFFFF;">{rv["time"]}</b></div>'
            f'<div style="background:rgba(255,122,53,0.1);border-left:4px solid #FF7A35;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
            f'<div style="font-size:12px;font-weight:700;color:#FF7A35;margin-bottom:4px;">REASON FOR REVOCATION</div>'
            f'<div style="font-size:14px;color:#FFFFFF;">{rv.get("revoke_reason","Not stated")}</div></div>'
            f'<div style="font-size:13px;color:#FFD000;font-weight:600;">📱 Patient has been notified that their report is under further review.</div>'
            f'</div>',unsafe_allow_html=True)

        # Revoked patient message
        revoked_patient_msg = (
            f"Dear Patient,\n\nYour previously approved report from {rv['doctor']} has been recalled for further review.\n\n"
            f"Reason: {rv.get('revoke_reason','Under clinical review')}\n\n"
            f"Your doctor is reviewing your case again and will send you an updated report shortly. "
            f"Please do not act on the previously sent message. If you have any urgent concerns, please contact the clinic.\n\n"
            f"We apologise for any inconvenience.\n\nRegards,\nMedAI Clinical System"
        )
        with st.expander('📱 View Revocation Message Sent to Patient'):
            st.markdown(f'<div style="background:#0D1A2E;border:2px solid #FF7A35;border-radius:12px;padding:20px;font-size:14px;color:#E8EDF5;white-space:pre-wrap;line-height:1.8;">{revoked_patient_msg}</div>', unsafe_allow_html=True)

        st.markdown('<div style="font-size:13px;font-weight:600;color:#60A5FA;margin:16px 0 8px;">🔁 Re-review this patient and issue a new decision:</div>', unsafe_allow_html=True)
        if st.button('↺ Re-open for Review', key='reopen_'+pid, use_container_width=False):
            del st.session_state.decisions[pid]
            st.rerun()

    # ══════════════════════════════════════════════════════════
    # CASE 3: REJECTED
    # ══════════════════════════════════════════════════════════
    elif cur_dec == 'REJECTED':
        rj = st.session_state.decisions[pid]
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(255,59,92,0.15),rgba(255,59,92,0.05));'
            f'border:2px solid rgba(255,59,92,0.5);border-radius:14px;padding:20px 24px;margin-bottom:16px;">'
            f'<div style="font-size:16px;font-weight:800;color:#FF3B5C;margin-bottom:10px;">❌ Report Rejected</div>'
            f'<div style="font-size:13px;color:#94A3B8;margin-bottom:10px;">Rejected by: <b style="color:#FFFFFF;">{rj.get("doctor","")}</b>  ·  Time: <b style="color:#FFFFFF;">{rj.get("time","")}</b></div>'
            + (f'<div style="background:rgba(255,59,92,0.1);border-left:4px solid #FF3B5C;border-radius:8px;padding:10px 14px;margin-bottom:12px;">'
               f'<div style="font-size:12px;font-weight:700;color:#FF3B5C;margin-bottom:4px;">REJECTION REASON</div>'
               f'<div style="font-size:14px;color:#FFFFFF;">{rj.get("reject_reason","Not stated")}</div></div>'
               if rj.get("reject_reason") else '') +
            f'</div>',unsafe_allow_html=True)

        # ── NEXT STEPS AFTER REJECTION ────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(96,165,250,0.1),rgba(124,58,237,0.05));
        border:2px solid rgba(96,165,250,0.4);border-radius:14px;padding:20px 24px;margin-bottom:16px;">
            <div style="font-size:14px;font-weight:800;color:#60A5FA;margin-bottom:14px;">📋 What Happens Next?</div>
            <div style="display:flex;flex-direction:column;gap:10px;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,59,92,0.2);color:#FF3B5C;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">1</span>
                    <span style="font-size:13px;color:#E8EDF5;line-height:1.6;">The patient has <b style="color:#FF3B5C;">NOT been notified</b> — no message has been sent. Their portal will show "Report Under Review".</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,122,53,0.2);color:#FF7A35;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">2</span>
                    <span style="font-size:13px;color:#E8EDF5;line-height:1.6;">The AI report is flagged for <b style="color:#FF7A35;">re-analysis</b>. Updated results will be queued for your review.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,208,0,0.2);color:#FFD000;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">3</span>
                    <span style="font-size:13px;color:#E8EDF5;line-height:1.6;">You can <b style="color:#FFD000;">reset and re-review</b> the current report, or request the patient resubmit samples/scans.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(0,229,160,0.2);color:#00E5A0;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">4</span>
                    <span style="font-size:13px;color:#E8EDF5;line-height:1.6;">Once you are satisfied with the updated report, <b style="color:#00E5A0;">approve and release</b> to notify the patient.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Buttons: Reset or Request Resubmission
        rj_col1, rj_col2 = st.columns(2)
        with rj_col1:
            if st.button('↺ Reset & Re-review', key='reset_'+pid, use_container_width=True):
                del st.session_state.decisions[pid]; st.rerun()
        with rj_col2:
            if st.button('📤 Request Patient Resubmission', key='resubmit_'+pid, use_container_width=True):
                st.session_state.reject_resubmit[pid] = True
                st.rerun()

        if st.session_state.reject_resubmit.get(pid):
            st.markdown("""
            <div style="background:rgba(192,132,252,0.1);border:2px solid rgba(192,132,252,0.4);border-radius:12px;padding:16px 20px;margin-top:12px;">
                <div style="font-size:13px;font-weight:700;color:#C084FC;margin-bottom:8px;">📱 Resubmission Request Sent to Patient:</div>
                <div style="font-size:13px;color:#E8EDF5;line-height:1.7;">
                    "Dear Patient, your recent report could not be approved at this time. Your doctor has requested that you resubmit your test samples / attend for a repeat scan at your earliest convenience. Please contact the clinic to schedule your appointment. — MedAI Clinical System"
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # CASE 4: PENDING — Doctor Action Required
    # ══════════════════════════════════════════════════════════
    else:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(96,165,250,0.08),rgba(124,58,237,0.05));
        border:2px solid #2563EB;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
            <div style="font-size:14px;font-weight:800;color:#60A5FA;margin-bottom:4px;">📝 Doctor's Prescription & Additional Notes</div>
            <div style="font-size:13px;color:#4A6080;margin-bottom:12px;">Add prescriptions, amendments, follow-up instructions, or referrals. These will be included in the patient's message.</div>
        </div>
        """, unsafe_allow_html=True)

        notes = st.text_area(
            'Prescription / Clinical Notes',
            placeholder='e.g. Prescribe Tab. Metformin 500mg BD × 30 days. Avoid NSAIDs. Follow-up in 4 weeks. Refer to Nephrology if eGFR drops below 45...',
            height=120,
            key='notes_'+doc_id+'_'+pid,
            label_visibility='collapsed'
        )

        # Rejection reason (shown inline)
        reject_reason = st.text_input(
            'Rejection reason (required for Reject)',
            placeholder='State reason if rejecting — e.g. Insufficient data, wrong patient file, requires repeat scan...',
            key='reject_reason_'+doc_id+'_'+pid,
            label_visibility='collapsed'
        )

        pat_msg = get_msg(p)
        if notes.strip():
            pat_msg += '\n\n──────────────────────────\nDOCTOR\'S PRESCRIPTION & INSTRUCTIONS:\n' + notes.strip()

        with st.expander('📱 Preview Patient Message'):
            st.markdown(
                f'<div style="background:#0D1A2E;border:2px solid #2563EB;border-radius:12px;padding:18px 22px;">'
                f'<div style="font-size:12px;font-weight:700;color:#00E5A0;margin-bottom:10px;letter-spacing:0.08em;">📨 MESSAGE TO PATIENT</div>'
                f'<div style="font-size:14px;color:#E8EDF5;line-height:1.8;white-space:pre-wrap;">{pat_msg}</div></div>',
                unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)
        with b1:
            if st.button('✅ Approve & Send', key='app_'+doc_id+'_'+pid, use_container_width=True, type='primary'):
                st.session_state.decisions[pid] = {
                    'status': 'APPROVED',
                    'doctor': doc['name'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'message': pat_msg,
                    'notes': notes.strip()
                }
                st.rerun()
        with b2:
            if st.button('✏️ Approve with Edits', key='edit_'+doc_id+'_'+pid, use_container_width=True):
                st.session_state.decisions[pid] = {
                    'status': 'APPROVED',
                    'doctor': doc['name'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'message': pat_msg,
                    'notes': notes.strip()
                }
                st.rerun()
        with b3:
            if st.button('❌ Reject Report', key='rej_'+doc_id+'_'+pid, use_container_width=True):
                st.session_state.decisions[pid] = {
                    'status': 'REJECTED',
                    'doctor': doc['name'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'reject_reason': reject_reason.strip()
                }
                st.rerun()


# ── FINDINGS ──────────────────────────────────────────────────
def render_lab(p,sev,clr):
    ckd = p.get('ckd_severity') or 'Not tested'
    dia = p.get('diabetes_severity_final') or 'Not tested'
    thy = p.get('thyroid_severity_final') or 'Not tested'
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
            st.markdown(f'<div style="background:#0D1A2E;border:2px solid #2563EB;border-radius:12px;padding:16px;margin-bottom:12px;">'
                        f'<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{lbl}</div>'
                        f'<div style="font-size:17px;font-weight:700;color:{vc};">{v}</div></div>',unsafe_allow_html=True)

    rows=[]
    if 'ckd' in disease or 'kidney' in disease:
        if egfr is not None:
            st_='Normal' if egfr>=60 else 'Borderline' if egfr>=30 else 'Abnormal'
            stage='G1(≥90)' if egfr>=90 else 'G2(60-89)' if egfr>=60 else 'G3a(45-59)' if egfr>=45 else 'G3b(30-44)' if egfr>=30 else 'G4(15-29)' if egfr>=15 else 'G5(<15)'
            rows.append(ref_row('eGFR',fmt(egfr,'mL/min'),'≥90:G1(Normal) · 60-89:G2 · 45-59:G3a · 30-44:G3b · <30:G4-G5',st_))
            rows.append(ref_row('KDIGO Stage',stage+' — '+ckd,'G1-G2=Normal · G3=Moderate · G4-G5=Severe','Normal' if egfr>=60 else 'Borderline' if egfr>=45 else 'Abnormal'))
        else:
            ckd_st='Normal' if 'G1' in ckd or 'G2' in ckd else 'Borderline' if 'G3' in ckd else 'Abnormal' if ckd!='Not tested' else 'N/A'
            rows.append(ref_row('CKD Stage',ckd,'G1:≥90 · G2:60-89 · G3a:45-59 · G3b:30-44 · G4:15-29 · G5:<15',ckd_st))
            rows.append(ref_row('eGFR','Not measured','eGFR not available','N/A'))
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
        rows.append(ref_row('Diabetes Severity',dia,'Normal · Mild:borderline · Severe:poor control',dia_st))
        rows.append(ref_row('HbA1c Target','—','<7.0% (most) · <8.0% (elderly)','N/A'))
        src='ADA Standards of Medical Care in Diabetes 2024'
    elif 'thyroid' in disease:
        thy_st='Normal' if thy in ['Normal','Mild'] else 'Abnormal' if thy=='Severe' else 'N/A'
        if tsh is not None:
            ts='Normal' if 0.4<=tsh<=4.0 else 'Borderline' if tsh<=10 else 'Abnormal'
            interp='Euthyroid (Normal)' if 0.4<=tsh<=4.0 else 'Subclinical Hypothyroid' if tsh<=10 else 'Overt Hypothyroid'
            rows.append(ref_row('TSH Level',fmt(tsh,'mIU/L'),'Normal:0.4-4.0 · Subclinical:4.1-10.0 · Overt:>10.0',ts))
            rows.append(ref_row('TSH Interpretation',interp,'Subclinical=TSH↑ T4 normal · Overt=TSH↑↑ T4 low',ts))
        else:
            rows.append(ref_row('TSH Level','Not measured','Normal:0.4-4.0 mIU/L','N/A'))
        if free_t4 is not None:
            t4s='Normal' if 0.8<=free_t4<=1.8 else 'Abnormal'
            rows.append(ref_row('Free T4',fmt(free_t4,'ng/dL'),'Normal:0.8-1.8 ng/dL · Low=Hypothyroid',t4s))
        else:
            rows.append(ref_row('Free T4','Not measured','Normal:0.8-1.8 ng/dL','N/A'))
        rows.append(ref_row('Thyroid Status',thy,'Normal · Mild=Subclinical · Severe=Overt',thy_st))
        src='ATA/AACE Guidelines for Hypothyroidism 2023'
    else:
        src='WHO / Standard Clinical Guidelines'

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 10px;">Patient Values vs Clinical Guidelines</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,src),unsafe_allow_html=True)


def render_ct(p,sev,clr):
    cls=p.get('ct_predicted_class',''); conf=n(p.get('ct_confidence')) or 0
    name=CT_NAMES.get(cls,cls); desc=CT_DESC.get(cls,'')
    st.markdown(f'<div style="background:#0D1A2E;border:2px solid #2563EB;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">CT Brain Imaging</div>'
                f'<div style="font-size:20px;font-weight:800;color:#FFFFFF;margin-bottom:6px;">{name}</div>'
                f'<div style="font-size:14px;color:#94A3B8;margin-bottom:10px;">{desc}</div>'
                f'<div style="display:flex;gap:16px;"><span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
                f'<span style="color:#94A3B8;font-size:13px;">AI Confidence: <b style="color:#FFFFFF;">{round(conf*100,1)}%</b></span></div></div>',unsafe_allow_html=True)
    t=CT_IMAGE.get(str(cls),('',''))
    if t[0] and os.path.exists(t[0]):
        gc1,gc2=st.columns(2)
        with gc1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original CT Scan</div>',unsafe_allow_html=True)
            st.image(t[0],use_column_width=True)
        with gc2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if t[1] and os.path.exists(t[1]): st.image(t[1],use_column_width=True)
        st.markdown('<div style="background:#0D1A2E;border:2px solid #2563EB;border-left:4px solid #7C3AED;border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:#94A3B8;">🔍 <b style="color:#FFFFFF;">Grad-CAM:</b> Warm colours (red/yellow) = high AI attention regions.</div>',unsafe_allow_html=True)


def render_us(p,sev,clr):
    cls=p.get('predicted_class',''); conf=n(p.get('confidence')) or 0
    name=US_NAMES.get(cls,cls); desc=US_DESC.get(cls,'')
    st.markdown(f'<div style="background:#0D1A2E;border:2px solid #2563EB;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Obstetric Ultrasound</div>'
                f'<div style="font-size:20px;font-weight:800;color:#FFFFFF;margin-bottom:6px;">{name}</div>'
                f'<div style="font-size:14px;color:#94A3B8;margin-bottom:10px;">{desc}</div>'
                f'<div style="display:flex;gap:16px;"><span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
                f'<span style="color:#94A3B8;font-size:13px;">AI Confidence: <b style="color:#FFFFFF;">{round(conf*100,1)}%</b></span></div></div>',unsafe_allow_html=True)
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
        if ct_cls: parts.append('🧠 CT: <b style="color:#FFFFFF;">'+CT_NAMES.get(ct_cls,ct_cls)+'</b>')
        if us_cls: parts.append('🔬 US: <b style="color:#FFFFFF;">'+US_NAMES.get(us_cls,us_cls)+'</b>')
        st.markdown('<div style="font-size:13px;color:#94A3B8;margin-bottom:14px;">'+'  ·  '.join(parts)+'</div>',unsafe_allow_html=True)

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
        st.markdown('<div style="font-size:12px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;margin:8px 0 10px;">Lab Values vs Reference Ranges</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,'KDIGO 2022 · ADA 2024 · ATA/AACE 2023'),unsafe_allow_html=True)


def render_rag(parsed, citations):
    """Render all 5 RAG sections with rich clinical UI for the doctor."""

    if not parsed or not any([
        parsed.get('clinical_summary'),
        parsed.get('key_findings'),
        parsed.get('recommendations'),
        parsed.get('followup'),
        parsed.get('urgency'),
    ]):
        st.markdown(
            '<div style="background:#0D1A2E;border:2px dashed #2563EB;border-radius:12px;padding:20px 24px;">'
            '<div style="font-size:14px;color:#60A5FA;font-weight:600;">⚠️ RAG summary not available for this patient.</div>'
            '<div style="font-size:13px;color:#4A6080;margin-top:6px;">Ensure <code>rag_summaries.json</code> contains an entry for this patient ID '
            'and that the GPT output includes CLINICAL SUMMARY / KEY FINDINGS / RECOMMENDATIONS / FOLLOW-UP / URGENCY sections.</div>'
            '</div>',
            unsafe_allow_html=True)
        return

    # ── 1. CLINICAL SUMMARY ──────────────────────────────────
    if parsed.get('clinical_summary'):
        st.markdown(
            '<div style="background:linear-gradient(135deg,#130A2E,#0D1B2E);border:2px solid #3B1FA8;'
            'border-left:5px solid #7C3AED;border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
            '<span style="font-size:16px;">🧬</span>'
            '<span style="font-size:11px;font-weight:700;color:#A78BFA;text-transform:uppercase;letter-spacing:0.1em;">Clinical Summary</span>'
            '</div>'
            f'<div style="font-size:15px;color:#E8EDF5;line-height:1.9;">{parsed["clinical_summary"]}</div>'
            '</div>',
            unsafe_allow_html=True)

    # ── 2. KEY FINDINGS ──────────────────────────────────────
    if parsed.get('key_findings'):
        rows_html = ''.join([
            f'<div style="display:flex;gap:12px;padding:11px 0;border-bottom:1px solid #1E3A5F;align-items:flex-start;">'
            f'<span style="background:rgba(192,132,252,0.2);color:#C084FC;font-weight:800;font-size:13px;'
            f'padding:2px 9px;border-radius:6px;flex-shrink:0;margin-top:1px;">F{i+1}</span>'
            f'<span style="font-size:14px;color:#E8EDF5;line-height:1.65;">{f}</span></div>'
            for i, f in enumerate(parsed['key_findings'])
        ])
        st.markdown(
            '<div style="background:#0D1A2E;border:2px solid #7C3AED;border-radius:14px;'
            'padding:16px 20px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            '<span style="font-size:16px;">🔍</span>'
            '<span style="font-size:11px;font-weight:700;color:#C084FC;text-transform:uppercase;letter-spacing:0.1em;">Key Findings</span>'
            f'<span style="background:rgba(192,132,252,0.2);color:#C084FC;font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px;">{len(parsed["key_findings"])} items</span>'
            '</div>'
            f'{rows_html}</div>',
            unsafe_allow_html=True)

    # ── 3. CLINICAL RECOMMENDATIONS ─────────────────────────
    if parsed.get('recommendations'):
        recs_html = ''.join([
            f'<div style="display:flex;gap:12px;padding:11px 0;border-bottom:1px solid rgba(0,229,160,0.15);align-items:flex-start;">'
            f'<span style="background:linear-gradient(135deg,#059669,#00E5A0);color:#FFFFFF;font-weight:800;'
            f'font-size:13px;padding:3px 10px;border-radius:8px;flex-shrink:0;min-width:28px;text-align:center;">{i+1}</span>'
            f'<span style="font-size:14px;color:#E8EDF5;line-height:1.65;">{r}</span></div>'
            for i, r in enumerate(parsed['recommendations'])
        ])
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(0,229,160,0.08),rgba(0,229,160,0.02));'
            'border:2px solid rgba(0,229,160,0.4);border-left:5px solid #00E5A0;border-radius:14px;'
            'padding:16px 20px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            '<span style="font-size:16px;">💊</span>'
            '<span style="font-size:11px;font-weight:700;color:#00E5A0;text-transform:uppercase;letter-spacing:0.1em;">Clinical Recommendations</span>'
            f'<span style="background:rgba(0,229,160,0.2);color:#00E5A0;font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px;">{len(parsed["recommendations"])} actions</span>'
            '</div>'
            f'{recs_html}</div>',
            unsafe_allow_html=True)
    else:
        # Show a placeholder so the doctor knows the field exists but was empty
        st.markdown(
            '<div style="background:rgba(0,229,160,0.04);border:2px dashed rgba(0,229,160,0.25);'
            'border-radius:12px;padding:12px 18px;margin-bottom:14px;">'
            '<span style="font-size:13px;color:#4A6080;">💊 <b style="color:#00E5A0;">Recommendations</b> — '
            'Not generated for this entry. Check GPT prompt includes a RECOMMENDATIONS: section.</span>'
            '</div>',
            unsafe_allow_html=True)

    # ── 4. FOLLOW-UP + URGENCY side-by-side ─────────────────
    fu_col, ug_col = st.columns(2)
    with fu_col:
        fu = parsed.get('followup','')
        if fu:
            st.markdown(
                '<div style="background:#0D1A2E;border:2px solid #2563EB;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                '<span style="font-size:15px;">📅</span>'
                '<span style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;">Follow-up Plan</span>'
                '</div>'
                f'<div style="font-size:14px;color:#FFFFFF;font-weight:600;line-height:1.7;">{fu}</div>'
                '</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#0D1A2E;border:2px dashed #1E3A5F;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="font-size:13px;color:#4A6080;">📅 Follow-up not specified in summary.</div>'
                '</div>',
                unsafe_allow_html=True)

    with ug_col:
        urg = parsed.get('urgency','')
        if urg:
            uc = {'URGENT':'#FF3B5C','SEMI-URGENT':'#FF7A35','ROUTINE':'#00E5A0'}.get(urg.upper(),'#6B7A99')
            urg_icon = {'URGENT':'🚨','SEMI-URGENT':'⚠️','ROUTINE':'✅'}.get(urg.upper(),'📋')
            urg_sev_key = {'URGENT':'Severe','SEMI-URGENT':'Moderate','ROUTINE':'Normal'}.get(urg.upper(),'Unknown')
            st.markdown(
                f'<div style="background:{SEV_BG.get(urg_sev_key,"")};border:2px solid {uc}55;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                f'<span style="font-size:15px;">{urg_icon}</span>'
                f'<span style="font-size:11px;font-weight:700;color:{uc};text-transform:uppercase;letter-spacing:0.08em;">Clinical Urgency</span>'
                f'</div>'
                f'<div style="font-size:22px;font-weight:800;color:{uc};">{urg.upper()}</div>'
                f'</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#0D1A2E;border:2px dashed #1E3A5F;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="font-size:13px;color:#4A6080;">⚠️ Urgency not specified.</div>'
                '</div>',
                unsafe_allow_html=True)

    # ── 5. GUIDELINE CITATIONS ───────────────────────────────
    if citations:
        unique_cites = list(dict.fromkeys(citations))
        cite_html = '  ·  '.join([
            f'<span style="background:rgba(96,165,250,0.1);color:#60A5FA;padding:3px 10px;'
            f'border-radius:6px;font-size:12px;">{c}</span>'
            for c in unique_cites
        ])
        st.markdown(
            '<div style="background:#0D1A2E;border:2px solid #1E3A5F;border-radius:10px;'
            'padding:12px 18px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
            '<span style="font-size:14px;">📚</span>'
            '<span style="font-size:11px;font-weight:700;color:#60A5FA;text-transform:uppercase;letter-spacing:0.08em;">Guideline References</span>'
            '</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;">{cite_html}</div>'
            '</div>',
            unsafe_allow_html=True)


# ── ENTRY POINT ───────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    render_dashboard()
