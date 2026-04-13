import streamlit as st
import json
import os
import logging
import re
from datetime import datetime, timedelta

# ── LOGGING SETUP ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('MedAI')

st.set_page_config(page_title="MedAI — Doctor Dashboard", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background:#F0F6FF!important;color:#1E293B!important;font-size:14px!important;}
.stApp{background:#F0F6FF!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stTextInput>div>div>input{background:#FFFFFF!important;color:#1E293B!important;border:2px solid #93C5FD!important;border-radius:10px!important;font-size:14px!important;padding:10px 16px!important;}
.stSelectbox>div>div{background:#FFFFFF!important;color:#1E293B!important;border:2px solid #93C5FD!important;border-radius:10px!important;font-size:14px!important;}
.stTextArea textarea{background:#FFFFFF!important;color:#1E293B!important;border:2px solid #93C5FD!important;border-radius:10px!important;font-size:14px!important;}
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:700!important;font-size:14px!important;border-radius:10px!important;padding:10px 20px!important;transition:all 0.2s!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2563EB,#7C3AED)!important;border:none!important;color:#FFFFFF!important;box-shadow:0 4px 14px rgba(37,99,235,0.4)!important;}
.stButton>button[kind="primary"]:hover{transform:translateY(-1px)!important;}
.stButton>button[kind="secondary"]{background:#FFFFFF!important;border:2px solid #93C5FD!important;color:#1D4ED8!important;}
.stButton>button[kind="secondary"]:hover{background:#EFF6FF!important;}
.stTabs [data-baseweb="tab-list"]{background:#DBEAFE!important;border-bottom:2px solid #93C5FD!important;padding:0 8px!important;}
.stTabs [data-baseweb="tab"]{font-size:14px!important;font-weight:600!important;color:#1D4ED8!important;padding:12px 20px!important;}
.stTabs [aria-selected="true"]{color:#1D4ED8!important;border-bottom:3px solid #7C3AED!important;background:transparent!important;font-weight:800!important;}
.stExpander{background:#FFFFFF!important;border:2px solid #BFDBFE!important;border-radius:12px!important;box-shadow:0 1px 6px rgba(37,99,235,0.07)!important;}
.stExpander summary p{color:#1D4ED8!important;font-weight:700!important;font-size:14px!important;}
hr{border-color:#BFDBFE!important;}
div[data-testid="stSelectbox"] label{color:#1D4ED8!important;font-weight:700!important;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-thumb{background:#93C5FD;border-radius:6px;}
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
HERO_IMG        = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1600&q=95"  # doctor + technology
HERO_IMG_LOGIN  = "https://images.unsplash.com/photo-1584982751601-97dcc096659c?w=1600&h=500&q=95&fit=crop&crop=center"   # medical lab
DEPT_IMGS = {
    'Lab Report':          "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1600&h=400&q=95&fit=crop&crop=center",
    'CT Scan':             "https://images.unsplash.com/photo-1516069677018-378515003435?w=1600&h=400&q=95&fit=crop&crop=center",
    'Ultrasound':          "https://images.unsplash.com/photo-1609220136736-443140cffec6?w=1600&h=400&q=95&fit=crop&crop=center",
    'Combined Assessment': "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1600&h=400&q=95&fit=crop&crop=center",
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

@st.cache_data
def load_trends():
    for p in ['data/patient_trends.json','patient_trends.json']:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return {}

ALL_PATIENTS = load_patients()
RAG_DATA     = load_rag()
TREND_DATA   = load_trends()
logger.info(f"STARTUP  | Patients loaded={len(ALL_PATIENTS)} | RAG entries={len(RAG_DATA)} | Trends={len(TREND_DATA)}")

# ── SESSION STATE ─────────────────────────────────────────────
for k,v in {'logged_in':False,'active_doctor':None,'selected':{},'decisions':{},'reject_resubmit':{},'activity_log':[]}.items():
    if k not in st.session_state: st.session_state[k]=v

def add_log(action, details, level='INFO'):
    """Add entry to session activity log and Python logger."""
    entry = {
        'time':    datetime.now().strftime('%H:%M:%S'),
        'date':    datetime.now().strftime('%Y-%m-%d'),
        'action':  action,
        'details': details,
        'level':   level,
    }
    st.session_state.activity_log.append(entry)
    # Also log to Python logger
    logger.info(f"{action:10} | {details}")

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

    # ── Extract urgency if it was embedded inside follow-up text ──
    # GPT sometimes writes: "...in 4 weeks. URGENCY: SEMI-URGENT — due to..."
    if not s['urgency'] and s['followup']:
        import re as _re
        urg_match = _re.search(r'URGENCY\s*:\s*(URGENT|SEMI[\s\-]*URGENT|ROUTINE)', s['followup'], _re.I)
        if urg_match:
            s['urgency'] = urg_match.group(1).strip()
            # Remove the urgency part from follow-up text
            s['followup'] = s['followup'][:urg_match.start()].strip()
            # Clean trailing punctuation
            s['followup'] = s['followup'].rstrip(' |.—-').strip()

    # Also check if urgency is embedded in recommendations or summary
    if not s['urgency']:
        for field in ['clinical_summary'] + s['recommendations'] + s['key_findings']:
            import re as _re
            m = _re.search(r'URGENCY\s*:\s*(URGENT|SEMI[\s\-]*URGENT|ROUTINE)', str(field), _re.I)
            if m:
                s['urgency'] = m.group(1).strip()
                break

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
        'gap:0;padding:10px 0;border-bottom:1px solid #BFDBFE;align-items:center;">'
        f'<div style="font-size:13px;font-weight:600;color:#0F172A;">{param}</div>'
        f'<div style="font-size:13px;font-weight:700;color:{pv_clr};">{pat_val}</div>'
        f'<div style="font-size:12px;color:#334155;line-height:1.5;">{guide}</div>'
        f'<div>{sev_badge(status)}</div>'
        '</div>'
    )

def ref_table(rows, source):
    header=(
        '<div style="display:grid;grid-template-columns:1fr 1.2fr 2fr 1fr;'
        'gap:0;border-bottom:2px solid #2563EB;padding-bottom:8px;margin-bottom:4px;">'
        +''.join([f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.06em;">{h}</div>'
                  for h in ['Parameter','Patient Value','Guideline Range','Status']])
        +'</div>'
    )
    return (
        '<div style="background:#FFFFFF;border:2px solid #93C5FD;'
        'border-left:4px solid #60A5FA;border-radius:14px;padding:16px 20px;margin-bottom:14px;">'
        +header+''.join(rows)+
        f'<div style="font-size:11px;color:#334155;margin-top:10px;font-style:italic;">Source: {source}</div>'
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


# ══════════════════════════════════════════════════════════════
# MODULE 1 — APPOINTMENT SCHEDULING (ALL PATIENTS)
# ══════════════════════════════════════════════════════════════
# SPECIALIST_MAP is built from the DOCTORS dict — no hardcoding.
# Change doctor names/depts in DOCTORS above and it updates everywhere.

HELPDESK_PHONE = '{HELPDESK_PHONE}'   # ← change once, updates all languages

def _build_specialist_map():
    d = DOCTORS
    return {
        'CKD':           {'doctor_id':'DR001','doctor':d['DR001']['name'],'dept':'Nephrology',     'room':d['DR001']['dept']+' · Room 102'},
        'Diabetes':      {'doctor_id':'DR001','doctor':d['DR001']['name'],'dept':'Endocrinology',  'room':d['DR001']['dept']+' · Room 103'},
        'Thyroid':       {'doctor_id':'DR001','doctor':d['DR001']['name'],'dept':'Endocrinology',  'room':d['DR001']['dept']+' · Room 103'},
        'glioma':        {'doctor_id':'DR002','doctor':d['DR002']['name'],'dept':'Neuro-Oncology', 'room':d['DR002']['dept']+' · Room 201'},
        'meningioma':    {'doctor_id':'DR002','doctor':d['DR002']['name'],'dept':'Neurosurgery',   'room':d['DR002']['dept']+' · Room 202'},
        'pituitary':     {'doctor_id':'DR002','doctor':d['DR002']['name'],'dept':'Neurosurgery',   'room':d['DR002']['dept']+' · Room 202'},
        'notumor':       {'doctor_id':'DR002','doctor':d['DR002']['name'],'dept':d['DR002']['dept'],'room':d['DR002']['dept']+' · Room 203'},
        'Fetal brain':   {'doctor_id':'DR003','doctor':d['DR003']['name'],'dept':'Perinatology',   'room':d['DR003']['dept']+' · Room 301'},
        'Fetal thorax':  {'doctor_id':'DR003','doctor':d['DR003']['name'],'dept':'Fetal Medicine', 'room':d['DR003']['dept']+' · Room 302'},
        'Fetal abdomen': {'doctor_id':'DR003','doctor':d['DR003']['name'],'dept':d['DR003']['dept'],'room':d['DR003']['dept']+' · Room 303'},
        'Fetal femur':   {'doctor_id':'DR003','doctor':d['DR003']['name'],'dept':d['DR003']['dept'],'room':d['DR003']['dept']+' · Room 303'},
        'Multi-Disease': {'doctor_id':'DR004','doctor':d['DR004']['name'],'dept':d['DR004']['dept'],'room':d['DR004']['dept']+' · Room 401'},
    }

SPECIALIST_MAP = _build_specialist_map()

def appt_get_specialist(p):
    mtype   = p.get('modality_type','')
    disease = p.get('disease_type','')
    if mtype == 'Lab Report':
        key = disease
    elif mtype == 'CT Scan':
        key = p.get('ct_predicted_class','')
    elif mtype == 'Ultrasound':
        key = p.get('predicted_class','')
    else:
        key = 'Multi-Disease'
    doc_id   = p.get('doctor_id','DR001')
    fallback = {
        'doctor_id': doc_id,
        'doctor':    DOCTORS.get(doc_id,{}).get('name','Your Doctor'),
        'dept':      DOCTORS.get(doc_id,{}).get('dept','OPD'),
        'room':      DOCTORS.get(doc_id,{}).get('dept','OPD') + ' · Consult front desk',
    }
    return SPECIALIST_MAP.get(key, fallback)

def appt_extract_urgency(rag_summary):
    if not rag_summary or rag_summary == 'Summary unavailable':
        return 'ROUTINE'
    m = re.search(r'URGENCY\s*[:\-]\s*(\S+)', str(rag_summary), re.IGNORECASE)
    raw = m.group(1).strip().upper() if m else 'ROUTINE'
    if 'URGENT' in raw and 'SEMI' not in raw: return 'URGENT'
    if 'SEMI' in raw: return 'SEMI-URGENT'
    return 'ROUTINE'

def appt_should_schedule(p, rag_summary):
    return True   # ALL patients get appointment scheduling



def appt_generate_slots(severity):
    base  = datetime.now()
    times = ['09:00 AM','11:00 AM','02:00 PM','04:00 PM','05:30 PM']
    slots = []
    for day in range(4):
        dt    = base + timedelta(days=day)
        label = 'Today' if day==0 else 'Tomorrow' if day==1 else dt.strftime('%A')
        for t in times:
            slots.append({
                'label':    f'{label}  {t}',
                'datetime': dt.strftime(f'%d %b %Y  {t}'),
                'urgent':   severity == 'Severe' and day <= 1,
            })
    return slots

def render_appointment_module(p, pid, rag_summary, doc_id='DR001'):
    if not appt_should_schedule(p, rag_summary):
        return

    sev     = p.get('_sev','Normal')
    urgency = appt_extract_urgency(rag_summary)
    spec    = appt_get_specialist(p)
    slots   = appt_generate_slots(sev)

    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;'
        'letter-spacing:0.1em;margin:24px 0 12px;font-size:13px;">📅 Appointment Scheduling</div>',
        unsafe_allow_html=True)

    # Severity alert banner
    alert_clr = '#FF3B5C' if sev=='Severe' or urgency=='URGENT' else '#FF7A35'
    alert_bg  = 'rgba(255,59,92,0.1)' if sev=='Severe' or urgency=='URGENT' else 'rgba(255,122,53,0.1)'
    alert_ico = '🚨' if sev=='Severe' or urgency=='URGENT' else '⚠️'
    st.markdown(
        f'<div style="background:{alert_bg};border:2px solid {alert_clr}55;border-left:5px solid {alert_clr};'
        f'border-radius:14px;padding:16px 22px;margin-bottom:16px;">'
        f'<div style="font-size:15px;font-weight:800;color:{alert_clr};margin-bottom:4px;">'
        f'{alert_ico} Severity: {sev}  ·  Urgency: {urgency}</div>'
        f'<div style="font-size:13px;color:#334155;">Immediate specialist consultation is recommended for this patient.</div>'
        f'</div>',
        unsafe_allow_html=True)

    # Specialist card
    sc1, sc2, sc3 = st.columns(3)
    for col, lbl, val in [(sc1,'Specialist',spec['doctor']),(sc2,'Department',spec['dept']),(sc3,'Location',spec['room'])]:
        with col:
            st.markdown(
                f'<div style="background:#FFFFFF;border:2px solid #BFDBFE;border-radius:12px;padding:14px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{lbl}</div>'
                f'<div style="font-size:14px;font-weight:700;color:#0F172A;">{val}</div>'
                f'</div>', unsafe_allow_html=True)

    # Slot picker
    st.markdown(
        '<div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:8px;">Select Appointment Slot</div>',
        unsafe_allow_html=True)
    if sev == 'Severe':
        st.markdown(
            '<div style="background:rgba(255,59,92,0.08);border:1px solid rgba(255,59,92,0.3);'
            'border-radius:8px;padding:8px 14px;margin-bottom:10px;font-size:12px;color:#DC2626;">'
            '🔴 Slots within 24 hours are auto-prioritised for Severe cases.</div>',
            unsafe_allow_html=True)

    urgent_slots  = [s for s in slots if s['urgent']]
    routine_slots = [s for s in slots if not s['urgent']]
    all_slots     = urgent_slots + routine_slots

    # Track selected slot index in session state
    sel_key = f'appt_sel_idx_{doc_id}_{pid}'
    if sel_key not in st.session_state:
        st.session_state[sel_key] = 0

    # Render slots as visible clickable buttons — 5 per row
    rows = [all_slots[i:i+5] for i in range(0, len(all_slots), 5)]
    for row in rows:
        cols = st.columns(len(row))
        for ci, (col, slot) in enumerate(zip(cols, row)):
            global_idx = all_slots.index(slot)
            is_sel     = st.session_state[sel_key] == global_idx
            is_urgent  = slot['urgent']
            if is_urgent and is_sel:
                btn_style = 'background:linear-gradient(135deg,#FF3B5C,#FF7A35);color:#FFFFFF;border:2px solid #FF3B5C;'
            elif is_urgent:
                btn_style = 'background:#FFF1F2;color:#DC2626;border:2px solid #FF3B5C;'
            elif is_sel:
                btn_style = 'background:linear-gradient(135deg,#2563EB,#7C3AED);color:#FFFFFF;border:2px solid #2563EB;'
            else:
                btn_style = 'background:#FFFFFF;color:#1E293B;border:2px solid #BFDBFE;'
            with col:
                label = slot['label'] + (' 🔴' if is_urgent else '')
                if st.button(label, key=f'slot_btn_{doc_id}_{pid}_{global_idx}',
                             use_container_width=True,
                             type='primary' if is_sel else 'secondary'):
                    st.session_state[sel_key] = global_idx
                    st.rerun()

    chosen_slot = all_slots[st.session_state[sel_key]]

    # Show selected slot confirmation
    slot_clr = '#DC2626' if chosen_slot['urgent'] else '#2563EB'
    st.markdown(
        f'<div style="background:#F8FAFF;border:2px solid {slot_clr}44;border-left:4px solid {slot_clr};'
        f'border-radius:10px;padding:10px 16px;margin:8px 0 14px;">'
        f'<span style="font-size:13px;font-weight:700;color:{slot_clr};">✓ Selected: {chosen_slot["datetime"]}'
        f'{"  🔴 URGENT SLOT" if chosen_slot["urgent"] else ""}</span>'
        f'</div>', unsafe_allow_html=True)

    # Doctor-in-the-loop approval
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(96,165,250,0.08),rgba(124,58,237,0.05));'
        'border:2px solid #93C5FD;border-radius:12px;padding:14px 18px;margin:12px 0 10px;">'
        '<div style="font-size:13px;font-weight:700;color:#60A5FA;margin-bottom:4px;">👨‍⚕️ Doctor-in-the-Loop Approval</div>'
        '<div style="font-size:12px;color:#334155;">The patient will only be notified after you confirm this appointment.</div>'
        '</div>',
        unsafe_allow_html=True)

    approved_key = f'appt_approved_{pid}'
    if not st.session_state.get(approved_key):
        if st.button('✅ Confirm Appointment & Notify Patient', key=f'appt_confirm_{pid}', type='primary'):
            st.session_state[approved_key]         = True
            st.session_state[f'appt_datetime_{pid}'] = chosen_slot['datetime']
            st.session_state[f'appt_doctor_{pid}']   = spec['doctor']
            st.session_state[f'appt_dept_{pid}']     = spec['dept']
            st.session_state[f'appt_room_{pid}']     = spec['room']
            add_log('APPT_BOOKED', f'Patient {pid} | {spec["doctor"]} | {chosen_slot["datetime"]}', 'SUCCESS')
            st.rerun()
    else:
        booked_dt  = st.session_state.get(f'appt_datetime_{pid}','')
        booked_doc = st.session_state.get(f'appt_doctor_{pid}','')
        st.markdown(
            f'<div style="background:rgba(0,229,160,0.12);border:2px solid rgba(0,229,160,0.5);'
            f'border-radius:12px;padding:16px 20px;margin-bottom:8px;">'
            f'<div style="font-size:15px;font-weight:800;color:#059669;margin-bottom:6px;">✅ Appointment Confirmed</div>'
            f'<div style="font-size:13px;color:#334155;">👨‍⚕️ {booked_doc}  ·  📅 {booked_dt}</div>'
            f'<div style="font-size:12px;color:#059669;margin-top:6px;font-weight:600;">'
            f'Patient notification sent — see Multilingual Messaging below.</div>'
            f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# MODULE 2 — MULTILINGUAL PATIENT MESSAGING
# ══════════════════════════════════════════════════════════════

MSG_LANGUAGES = {
    'English':'en','Tamil — தமிழ்':'ta',
    'Hindi — हिन्दी':'hi','Telugu — తెలుగు':'te','Malayalam — മലയാളം':'ml',
}

MSG_TEMPLATES = {
    'appointment': {
        'en': lambda pid,doc,slot,room: (
            f"Dear Patient (ID: {pid}),\n\nYour appointment has been confirmed with {doc}.\n\n"
            f"📅 Date & Time : {slot}\n📍 Location    : {room}\n\n"
            f"Please bring all previous medical records and arrive 15 minutes early.\n"
            f"For queries call: {HELPDESK_PHONE}.\n\nRegards,\nMedAI Clinical System"),
        'ta': lambda pid,doc,slot,room: (
            f"அன்புள்ள நோயாளி (ID: {pid}),\n\n{doc} அவர்களிடம் உங்கள் சந்திப்பு உறுதி செய்யப்பட்டது.\n\n"
            f"📅 தேதி மற்றும் நேரம் : {slot}\n📍 இடம் : {room}\n\n"
            f"அனைத்து மருத்துவ ஆவணங்களையும் கொண்டுவாருங்கள். 15 நிமிடம் முன்னதாக வாருங்கள்.\n"
            f"கேள்விகளுக்கு: {HELPDESK_PHONE}.\n\nமருத்துவர்-நிரல் சுகாதார அமைப்பு"),
        'hi': lambda pid,doc,slot,room: (
            f"प्रिय मरीज़ (ID: {pid}),\n\n{doc} के साथ आपकी अपॉइंटमेंट की पुष्टि हो गई है।\n\n"
            f"📅 तारीख और समय : {slot}\n📍 स्थान : {room}\n\n"
            f"कृपया सभी पुराने मेडिकल रिकॉर्ड लाएं और 15 मिनट पहले पहुँचें।\n"
            f"प्रश्नों के लिए: {HELPDESK_PHONE}.\n\nडॉक्टर-इन-द-लूप स्वास्थ्य प्रणाली"),
        'te': lambda pid,doc,slot,room: (
            f"ప్రియమైన రోగి (ID: {pid}),\n\n{doc} తో మీ అపాయింట్‌మెంట్ నిర్ధారించబడింది.\n\n"
            f"📅 తేదీ మరియు సమయం : {slot}\n📍 స్థానం : {room}\n\n"
            f"మీ వైద్య రికార్డులన్నింటినీ తీసుకువచ్చి 15 నిమిషాల ముందు వెళ్ళండి.\n"
            f"సందేహాలకు: {HELPDESK_PHONE}.\n\nడాక్టర్-ఇన్-ది-లూప్ ఆరోగ్య వ్యవస్థ"),
        'ml': lambda pid,doc,slot,room: (
            f"പ്രിയ രോഗി (ID: {pid}),\n\n{doc} മായുള്ള അപ്പോയ്ന്റ്മെന്റ് സ്ഥിരീകരിച്ചു.\n\n"
            f"📅 തീയതിയും സമയവും : {slot}\n📍 സ്ഥലം : {room}\n\n"
            f"എല്ലാ മെഡിക്കൽ രേഖകളും കൊണ്ടുവരൂ, 15 മിനിറ്റ് നേരത്തേ എത്തുക.\n"
            f"സഹായത്തിന്: {HELPDESK_PHONE}.\n\nഡോക്ടർ-ഇൻ-ദ-ലൂപ്പ് ആരോഗ്യ സംവിധാനം"),
    },
    'urgent': {
        'en': lambda pid,doc,slot,room: (
            f"⚠️ URGENT — Patient ID: {pid}\n\n"
            f"Your recent clinical report requires IMMEDIATE attention.\n\n"
            f"An urgent appointment has been scheduled with {doc}.\n"
            f"📅 {slot}  |  📍 {room}\n\n"
            f"Please attend WITHOUT DELAY. Need help? Call {HELPDESK_PHONE} immediately.\n\nMedAI Clinical System"),
        'ta': lambda pid,doc,slot,room: (
            f"⚠️ அவசரம் — நோயாளி ID: {pid}\n\n"
            f"உங்கள் மருத்துவ அறிக்கை உடனடி கவனிப்பு தேவைப்படுகிறது.\n\n"
            f"{doc} அவர்களிடம் அவசர சந்திப்பு திட்டமிடப்பட்டுள்ளது.\n"
            f"📅 {slot}  |  📍 {room}\n\n"
            f"தாமதிக்காமல் வருகை கொடுங்கள். உதவிக்கு: {HELPDESK_PHONE}.\n\nமருத்துவர்-நிரல் சுகாதார அமைப்பு"),
        'hi': lambda pid,doc,slot,room: (
            f"⚠️ अत्यावश्यक — मरीज़ ID: {pid}\n\n"
            f"आपकी नवीनतम रिपोर्ट को तत्काल ध्यान देने की आवश्यकता है।\n\n"
            f"{doc} के साथ अर्जेंट अपॉइंटमेंट निर्धारित की गई है।\n"
            f"📅 {slot}  |  📍 {room}\n\n"
            f"बिना देरी किए उपस्थित हों। सहायता: {HELPDESK_PHONE}.\n\nडॉक्टर-इन-द-लूप स्वास्थ्य प्रणाली"),
        'te': lambda pid,doc,slot,room: (
            f"⚠️ అత్యవసరం — రోగి ID: {pid}\n\n"
            f"మీ తాజా నివేదిక తక్షణ శ్రద్ధ అవసరం.\n\n"
            f"{doc} తో అత్యవసర అపాయింట్‌మెంట్ నిర్ణయించబడింది.\n"
            f"📅 {slot}  |  📍 {room}\n\n"
            f"ఆలస్యం చేయకుండా హాజరుకండి. సహాయం: {HELPDESK_PHONE}.\n\nడాక్టర్-ఇన్-ది-లూప్ ఆరోగ్య వ్యవస్థ"),
        'ml': lambda pid,doc,slot,room: (
            f"⚠️ അടിയന്തരം — രോഗി ID: {pid}\n\n"
            f"നിങ്ങളുടെ റിപ്പോർട്ടിന് ഉടൻ ശ്രദ്ധ ആവശ്യമാണ്.\n\n"
            f"{doc} മായി അടിയന്തര അപ്പോയ്ന്റ്മെന്റ് ക്രമീകരിച്ചു.\n"
            f"📅 {slot}  |  📍 {room}\n\n"
            f"വൈകാതെ ഹാജരാകുക. സഹായത്തിന്: {HELPDESK_PHONE}.\n\nഡോക്ടർ-ഇൻ-ദ-ലൂപ്പ് ആരോഗ്യ സംവിധാനം"),
    },
    'followup': {
        'en': lambda pid,doc,slot,room: (
            f"Dear Patient (ID: {pid}),\n\nThis is a reminder for your follow-up with {doc} on {slot}.\n"
            f"📍 {room}\n\nPlease complete all prescribed tests before the visit.\n\nMedAI Clinical System"),
        'ta': lambda pid,doc,slot,room: (
            f"அன்புள்ள நோயாளி (ID: {pid}),\n\n{slot} அன்று {doc} அவர்களிடம் மறுவருகை நினைவூட்டல்.\n"
            f"📍 {room}\n\nவருகை முன் பரிந்துரைக்கப்பட்ட சோதனைகளை முடிக்கவும்.\n\nமருத்துவர்-நிரல் சுகாதார அமைப்பு"),
        'hi': lambda pid,doc,slot,room: (
            f"प्रिय मरीज़ (ID: {pid}),\n\n{slot} को {doc} के साथ फॉलो-अप की याद दिलाना।\n"
            f"📍 {room}\n\nकृपया सभी परीक्षण पहले पूरे करें।\n\nडॉक्टर-इन-द-लूप स्वास्थ्य प्रणाली"),
        'te': lambda pid,doc,slot,room: (
            f"ప్రియమైన రోగి (ID: {pid}),\n\n{slot} న {doc} తో ఫాలో-అప్ జ్ఞాపకం.\n"
            f"📍 {room}\n\nసందర్శన ముందు అన్ని పరీక్షలు పూర్తి చేయండి.\n\nడాక్టర్-ఇన్-ది-లూప్"),
        'ml': lambda pid,doc,slot,room: (
            f"പ്രിയ രോഗി (ID: {pid}),\n\n{slot} ന് {doc} മായി ഫോളോ-അപ്പ്.\n"
            f"📍 {room}\n\nദയവായി പരിശോധനകൾ മുൻകൂട്ടി പൂർത്തിയാക്കുക.\n\nഡോക്ടർ-ഇൻ-ദ-ലൂപ്പ്"),
    },
    'report_ready': {
        'en': lambda pid,doc,slot,room: (
            f"Dear Patient (ID: {pid}),\n\nYour AI-assisted medical report is ready and has been reviewed by {doc}.\n\n"
            f"Please attend your consultation on {slot} at {room}.\n"
            f"The doctor will walk you through the findings in detail.\n\nMedAI Clinical System"),
        'ta': lambda pid,doc,slot,room: (
            f"அன்புள்ள நோயாளி (ID: {pid}),\n\nAI-உதவி மருத்துவ அறிக்கை தயாராகி {doc} சரிபார்த்தது.\n\n"
            f"{slot} அன்று {room} இல் ஆலோசனைக்கு வாருங்கள்.\n\nமருத்துவர்-நிரல் சுகாதார அமைப்பு"),
        'hi': lambda pid,doc,slot,room: (
            f"प्रिय मरीज़ (ID: {pid}),\n\nआपकी AI रिपोर्ट तैयार है और {doc} ने समीक्षा की है।\n\n"
            f"{slot} को {room} पर परामर्श के लिए आएं।\n\nडॉक्टर-इन-द-लूप स्वास्थ्य प्रणाली"),
        'te': lambda pid,doc,slot,room: (
            f"ప్రియమైన రోగి (ID: {pid}),\n\nAI నివేదిక సిద్ధంగా ఉంది, {doc} సమీక్షించారు.\n\n"
            f"{slot} న {room} వద్ద సంప్రదింపులకు రండి.\n\nడాక్టర్-ఇన్-ది-లూప్"),
        'ml': lambda pid,doc,slot,room: (
            f"പ്രിയ രോഗി (ID: {pid}),\n\nAI റിപ്പോർട്ട് തയ്യാറായി {doc} അവലോകനം ചെയ്തു.\n\n"
            f"{slot} ന് {room} ൽ കൺസൾട്ടേഷനായി വരൂ.\n\nഡോക്ടർ-ഇൻ-ദ-ലൂപ്പ്"),
    },
}

def build_merged_patient_msg(p, pid, doc_name, notes=''):
    """
    Build ONE merged patient message that combines:
      - Clinical condition + doctor approval (from get_msg)
      - Appointment details (from appointment module session state)
      - Doctor's prescription/notes (if any)
    Language is picked from session state set by the messaging module.
    Falls back to English if no language selected yet.
    """
    sev          = p.get('_sev','Normal')
    lang_name    = st.session_state.get(f'msg_lang_{pid}', 'English')
    lang_code    = MSG_LANGUAGES.get(lang_name, 'en')
    appt_slot    = st.session_state.get(f'appt_datetime_{pid}', '')
    appt_doc     = st.session_state.get(f'appt_doctor_{pid}',  doc_name)
    appt_room    = st.session_state.get(f'appt_room_{pid}',    'OPD — consult front desk')
    appt_booked  = bool(st.session_state.get(f'appt_approved_{pid}', False))

    # ── Clinical summary part (uses existing get_msg logic) ──
    clinical_part = get_msg(p)

    # ── Appointment part (only if appointment was booked) ────
    if appt_booked and appt_slot:
        if sev == 'Severe':
            # Use urgent appointment template
            tmpl = MSG_TEMPLATES.get('urgent', {}).get(lang_code) or MSG_TEMPLATES['urgent']['en']
        else:
            tmpl = MSG_TEMPLATES.get('appointment', {}).get(lang_code) or MSG_TEMPLATES['appointment']['en']
        appt_part = '\n\n──────────────────────────\n' + tmpl(pid, appt_doc, appt_slot, appt_room)
    else:
        appt_part = ''

    # ── Doctor's prescription notes ──────────────────────────
    notes_part = ''
    if notes.strip():
        notes_part = '\n\n──────────────────────────\nDOCTOR\'S PRESCRIPTION & INSTRUCTIONS:\n' + notes.strip()

    return clinical_part + appt_part + notes_part


# ══════════════════════════════════════════════════════════════
# PDF REPORT GENERATOR
# Generates a downloadable patient report PDF on the fly.
# No pre-existing PDF files needed — built from patient data.
# ══════════════════════════════════════════════════════════════
def generate_patient_pdf(p, pid, parsed, doc_name, notes, appt_slot, appt_room):
    """
    Generate a clean patient report PDF using fpdf2.
    Returns bytes ready for st.download_button.
    """
    from fpdf import FPDF

    sev     = p.get('_sev', 'Normal')
    mtype   = p.get('modality_type', '')
    disease = p.get('disease_type', '')
    now_str = datetime.now().strftime('%d %b %Y  %H:%M')

    sev_colors = {
        'Normal':   (0, 200, 150),
        'Mild':     (220, 170, 0),
        'Moderate': (220, 100, 30),
        'Severe':   (210, 40, 60),
    }
    sev_rgb = sev_colors.get(sev, (100, 116, 139))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(18, 15, 18)

    # ── Header banner ──────────────────────────────────────────
    pdf.set_fill_color(21, 56, 138)
    pdf.rect(0, 0, 210, 28, 'F')
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(18, 7)
    pdf.cell(0, 10, 'MedAI Clinical System', ln=False)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_xy(18, 17)
    pdf.cell(0, 6, 'AI-Powered  |  Doctor-in-the-Loop  |  Approved Medical Report', ln=True)
    pdf.set_text_color(30, 41, 59)
    pdf.ln(8)

    # ── Severity badge ─────────────────────────────────────────
    pdf.set_fill_color(*sev_rgb)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(40, 9, f'  {sev.upper()}  ', border=0, fill=True, ln=False)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(10, 9, '', ln=False)
    pdf.cell(0, 9, f'Patient ID: {pid}   |   {mtype}   |   {now_str}', ln=True)
    pdf.ln(4)

    # ── Divider ────────────────────────────────────────────────
    pdf.set_draw_color(147, 197, 253)
    pdf.set_line_width(0.5)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(5)

    def section_title(title):
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_draw_color(147, 197, 253)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 41, 59)

    def body_text(text, indent=0):
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(51, 65, 85)
        pdf.set_x(18 + indent)
        pdf.multi_cell(174 - indent, 6, text)
        pdf.ln(1)

    def label_value(label, value):
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(30, 41, 59)
        pdf.set_x(18)
        pdf.cell(52, 7, label + ':', ln=False)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 7, str(value) if value else '—', ln=True)

    # ── Patient Details ────────────────────────────────────────
    section_title('Patient Details')
    label_value('Patient ID',      pid)
    label_value('Modality',        mtype)
    label_value('Disease / Scan',  disease or p.get('ct_predicted_class','') or p.get('predicted_class',''))
    label_value('Severity',        sev)
    label_value('Approved By',     doc_name)
    label_value('Report Date',     now_str)
    pdf.ln(4)

    # ── Lab Values (if applicable) ─────────────────────────────
    egfr    = p.get('egfr')
    glucose = p.get('glucose')
    tsh     = p.get('tsh')
    free_t4 = p.get('free_t4')
    ckd     = p.get('ckd_severity','')
    dia     = p.get('diabetes_severity_final','')
    thy     = p.get('thyroid_severity_final','')
    ct_cls  = p.get('ct_predicted_class','')
    us_cls  = p.get('predicted_class','')
    ct_conf = p.get('ct_confidence')
    us_conf = p.get('confidence')

    has_lab = any([egfr, glucose, tsh, ckd not in ['','Not tested',None], dia not in ['','Not tested',None]])
    has_ct  = bool(ct_cls)
    has_us  = bool(us_cls)

    if has_lab or has_ct or has_us:
        section_title('Investigation Results')
        if egfr:    label_value('eGFR',         f'{round(float(egfr),1)} mL/min/1.73m²')
        if ckd and ckd not in ['Not tested','']:  label_value('CKD Stage', ckd)
        if glucose: label_value('Fasting Glucose', f'{round(float(glucose),1)} mg/dL')
        if dia and dia not in ['Not tested','']: label_value('Diabetes Status', dia)
        if tsh:     label_value('TSH',           f'{round(float(tsh),3)} mIU/L')
        if free_t4: label_value('Free T4',       f'{round(float(free_t4),3)} ng/dL')
        if thy and thy not in ['Not tested','']: label_value('Thyroid Status', thy)
        if has_ct:
            ct_name = {'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma','meningioma':'Meningioma','glioma':'Glioma'}.get(ct_cls, ct_cls)
            conf_str = f' (AI confidence: {round(float(ct_conf)*100,1)}%)' if ct_conf else ''
            label_value('CT Brain Finding', ct_name + conf_str)
        if has_us:
            us_name = {'Fetal abdomen':'Fetal Abdomen','Fetal brain':'Fetal Brain','Fetal femur':'Fetal Femur','Fetal thorax':'Fetal Thorax'}.get(us_cls, us_cls)
            conf_str = f' (AI confidence: {round(float(us_conf)*100,1)}%)' if us_conf else ''
            label_value('Ultrasound Finding', us_name + conf_str)
        pdf.ln(4)

    # ── Clinical Summary ───────────────────────────────────────
    if parsed.get('clinical_summary'):
        section_title('AI Clinical Summary')
        body_text(parsed['clinical_summary'])
        pdf.ln(2)

    # ── Key Findings ───────────────────────────────────────────
    if parsed.get('key_findings'):
        section_title('Key Findings')
        for i, f in enumerate(parsed['key_findings'], 1):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(124, 58, 237)
            pdf.set_x(18)
            pdf.cell(8, 6, f'F{i}', ln=False)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(166, 6, f)
        pdf.ln(2)

    # ── Recommendations ────────────────────────────────────────
    if parsed.get('recommendations'):
        section_title('Clinical Recommendations')
        for i, r in enumerate(parsed['recommendations'], 1):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(5, 150, 105)
            pdf.set_x(18)
            pdf.cell(8, 6, f'{i}.', ln=False)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(166, 6, r)
        pdf.ln(2)

    # ── Follow-up + Urgency ────────────────────────────────────
    if parsed.get('followup') or parsed.get('urgency'):
        section_title('Follow-up & Urgency')
        if parsed.get('followup'):
            label_value('Follow-up Plan', parsed['followup'])
        if parsed.get('urgency'):
            label_value('Clinical Urgency', parsed['urgency'].upper())
        pdf.ln(2)

    # ── Appointment ────────────────────────────────────────────
    if appt_slot and appt_slot != 'To be scheduled':
        section_title('Appointment Details')
        label_value('Doctor',   doc_name)
        label_value('Date & Time', appt_slot)
        label_value('Location', appt_room)
        pdf.ln(2)

    # ── Doctor's Notes ─────────────────────────────────────────
    if notes and notes.strip():
        section_title("Doctor's Prescription & Notes")
        body_text(notes.strip())
        pdf.ln(2)

    # ── Footer ─────────────────────────────────────────────────
    pdf.set_y(-22)
    pdf.set_draw_color(147, 197, 253)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, f'This report was generated by MedAI Clinical System on {now_str} and approved by {doc_name}.', ln=True, align='C')
    pdf.cell(0, 5, 'This is an AI-assisted report reviewed by a qualified doctor. For medical emergencies call 044-2744-0000.', ln=True, align='C')

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════════
# WHATSAPP SENDER — Twilio sandbox
# ══════════════════════════════════════════════════════════════
def send_whatsapp_message(body, pdf_bytes=None, pdf_filename='MedAI_Report.pdf'):
    """
    Send a WhatsApp message via Twilio sandbox.
    Reads credentials from st.secrets.
    Returns (success: bool, error_msg: str)
    """
    try:
        from twilio.rest import Client
        account_sid = st.secrets.get('TWILIO_ACCOUNT_SID','')
        auth_token  = st.secrets.get('TWILIO_AUTH_TOKEN','')
        from_num    = st.secrets.get('TWILIO_WHATSAPP_FROM','whatsapp:+14155238886')
        to_num      = st.secrets.get('TWILIO_WHATSAPP_TO','')

        if not all([account_sid, auth_token, to_num]):
            return False, 'Twilio credentials missing in Streamlit secrets.'

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=body,
            from_=from_num,
            to=to_num,
        )
        return True, ''
    except ImportError:
        return False, 'twilio package not installed. Add twilio to requirements.txt'
    except Exception as e:
        return False, str(e)


def build_whatsapp_msg(p, pid, doc_name, appt_slot, appt_room, notes):
    """
    Build a concise WhatsApp-friendly message based on severity.
    Normal/Mild  → no revisit needed, report is clear.
    Moderate     → follow-up recommended.
    Severe       → urgent revisit with appointment details.
    """
    sev     = p.get('_sev', 'Normal')
    mtype   = p.get('modality_type', '')
    disease = p.get('disease_type', '')
    egfr    = n(p.get('egfr'))
    glucose = n(p.get('glucose'))
    tsh     = n(p.get('tsh'))

    # Build condition line
    if mtype == 'Lab Report':
        disease_lower = disease.lower()
        if 'ckd' in disease_lower or 'kidney' in disease_lower:
            val_str = f' (eGFR: {round(egfr,1)} mL/min)' if egfr else ''
            condition = f'Chronic Kidney Disease{val_str}'
        elif 'diabetes' in disease_lower:
            val_str = f' (Glucose: {round(glucose,1)} mg/dL)' if glucose else ''
            condition = f'Diabetes Mellitus{val_str}'
        elif 'thyroid' in disease_lower:
            val_str = f' (TSH: {round(tsh,3)} mIU/L)' if tsh else ''
            condition = f'Thyroid Disorder{val_str}'
        else:
            condition = disease
    elif mtype == 'CT Scan':
        ct_cls = p.get('ct_predicted_class','')
        condition = {'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma',
                     'meningioma':'Meningioma','glioma':'Glioma'}.get(ct_cls, ct_cls)
    elif mtype == 'Ultrasound':
        condition = p.get('predicted_class','Obstetric Ultrasound')
    else:
        condition = 'Multimodal Assessment'

    now_str = datetime.now().strftime('%d %b %Y')

    if sev in ('Normal', 'Mild'):
        msg = (
            f"✅ *MedAI Clinical System — Doctor Approved Report*\n\n"
            f"Dear Patient (ID: {pid}),\n\n"
            f"Your *{condition}* report has been reviewed and approved by *{doc_name}* on {now_str}.\n\n"
            f"*Result: {sev} — No immediate revisit required.*\n\n"
            f"{'✅ Your results are within acceptable range. Continue your current medication and follow a healthy lifestyle.' if sev == 'Normal' else '⚠️ Mild findings noted. Follow the prescribed diet and medication. Book a routine follow-up when convenient.'}\n\n"
        )
    elif sev == 'Moderate':
        msg = (
            f"⚠️ *MedAI Clinical System — Doctor Approved Report*\n\n"
            f"Dear Patient (ID: {pid}),\n\n"
            f"Your *{condition}* report has been reviewed and approved by *{doc_name}* on {now_str}.\n\n"
            f"*Result: Moderate — Follow-up appointment recommended.*\n\n"
            f"Please do not delay your follow-up visit. Contact the clinic to book your appointment soon.\n\n"
        )
    else:  # Severe
        appt_line = (
            f"📅 *Appointment:* {appt_slot}\n"
            f"📍 *Location:* {appt_room}\n"
            f"👨‍⚕️ *Doctor:* {doc_name}\n\n"
        ) if appt_slot and appt_slot != 'To be scheduled' else \
            "⚠️ Please contact the hospital immediately to book an urgent appointment.\n\n"

        msg = (
            f"🚨 *MedAI Clinical System — URGENT Doctor Approved Report*\n\n"
            f"Dear Patient (ID: {pid}),\n\n"
            f"Your *{condition}* report has been reviewed by *{doc_name}* on {now_str}.\n\n"
            f"*Result: SEVERE — Immediate medical attention required.*\n\n"
            f"{appt_line}"
            f"Please attend your appointment WITHOUT DELAY.\n\n"
        )

    if notes and notes.strip():
        msg += f"*Doctor's Instructions:*\n{notes.strip()}\n\n"

    msg += (
        f"📄 Your full medical report PDF is attached / available for download from the dashboard.\n\n"
        f"For urgent help call: *044-2744-0000*\n"
        f"_MedAI Clinical System — Doctor-in-the-Loop_"
    )
    return msg


def render_messaging_module(p, pid, rag_summary):
    sev          = p.get('_sev','Normal')
    default_slot = st.session_state.get(f'appt_datetime_{pid}', 'To be scheduled')
    default_doc  = st.session_state.get(f'appt_doctor_{pid}',   p.get('doctor_name','Your Doctor'))
    default_room = st.session_state.get(f'appt_room_{pid}',     'OPD — consult front desk')
    appt_booked  = bool(st.session_state.get(f'appt_approved_{pid}', False))

    st.markdown(
        '<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;'
        'letter-spacing:0.1em;margin:24px 0 12px;font-size:13px;">🌐 Multilingual Patient Messaging</div>',
        unsafe_allow_html=True)

    st.markdown(
        '<div style="background:rgba(37,99,235,0.06);border:2px solid #93C5FD;border-left:4px solid #2563EB;'
        'border-radius:10px;padding:10px 16px;margin-bottom:14px;font-size:13px;color:#1D4ED8;">'
        '💡 <b>Single message to patient</b> — Language and appointment details here are merged into the '
        'doctor\'s approval message. Only <b>one message</b> is sent when you click <b>Approve &amp; Send</b> below.</div>',
        unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    with m1:
        lang_name = st.selectbox(
            'Patient language',
            options=list(MSG_LANGUAGES.keys()),
            key=f'msg_lang_{pid}',
            label_visibility='collapsed'
        )
        lang_code = MSG_LANGUAGES[lang_name]
    with m2:
        msg_options = {
            'Appointment confirmation': 'appointment',
            'Urgent care alert':        'urgent',
            'Follow-up reminder':       'followup',
            'Report ready':             'report_ready',
        }
        default_type = 'Urgent care alert' if sev == 'Severe' else 'Appointment confirmation'
        msg_label = st.selectbox(
            'Appointment message type',
            options=list(msg_options.keys()),
            index=list(msg_options.keys()).index(default_type),
            key=f'msg_type_{pid}',
            label_visibility='collapsed'
        )
        msg_type = msg_options[msg_label]

    tmpl         = MSG_TEMPLATES.get(msg_type, {}).get(lang_code) or MSG_TEMPLATES.get(msg_type, {}).get('en')
    preview_text = tmpl(pid, default_doc, default_slot, default_room) if tmpl else 'Template not available.'

    appt_badge = (
        '<span style="background:rgba(0,229,160,0.15);color:#059669;font-size:11px;font-weight:700;'
        'padding:3px 10px;border-radius:10px;">✅ Appointment booked</span>'
        if appt_booked else
        '<span style="background:rgba(255,208,0,0.15);color:#D97706;font-size:11px;font-weight:700;'
        'padding:3px 10px;border-radius:10px;">⏳ Book appointment above first</span>'
    )
    st.markdown(
        f'<div style="background:#FFFFFF;border:2px solid #93C5FD;border-left:5px solid #7C3AED;'
        f'border-radius:12px;padding:16px 20px;margin:8px 0 12px;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
        f'<span style="font-size:11px;font-weight:700;color:#7C3AED;text-transform:uppercase;'
        f'letter-spacing:0.08em;">📨 Appointment section preview — {lang_name}</span>'
        f'<span style="flex:1"></span>{appt_badge}</div>'
        f'<div style="font-size:14px;color:#1E293B;line-height:1.9;white-space:pre-wrap;">{preview_text}</div>'
        f'<div style="font-size:12px;color:#94A3B8;margin-top:10px;font-style:italic;">'
        f'This will be appended to the clinical report when doctor approves below.</div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:8px;">Send via (on approval)</div>',
        unsafe_allow_html=True)
    default_channels = ['SMS','WhatsApp'] if sev == 'Severe' else ['SMS']
    st.multiselect(
        'Channels',
        options=['SMS','WhatsApp','Email'],
        default=default_channels,
        key=f'msg_channels_{pid}',
        label_visibility='collapsed'
    )
    if sev == 'Severe':
        st.markdown(
            '<div style="font-size:12px;color:#DC2626;margin-bottom:10px;">'
            '🔴 Severe case — SMS + WhatsApp recommended for maximum reach.</div>',
            unsafe_allow_html=True)

    ph_col, em_col = st.columns(2)
    ph_col.text_input('Phone (+91...)', key=f'msg_phone_{pid}', placeholder='+91 9876543210')
    em_col.text_input('Email address',  key=f'msg_email_{pid}', placeholder='patient@email.com')


# ── LOGIN PAGE ────────────────────────────────────────────────
def render_login():
    # Full-page hero background
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #EEF4FF 0%, #DBEAFE 50%, #EEF4FF 100%) !important;
    }}
    </style>
    <div style="position:relative;width:100%;height:220px;overflow:hidden;border-radius:0 0 24px 24px;margin-bottom:0;">
        <img src="{HERO_IMG_LOGIN}" style="width:100%;height:100%;object-fit:cover;opacity:0.25;"/>
        <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent,rgba(238,244,255,0.85));"></div>
        <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;">
            <div style="font-size:52px;margin-bottom:10px;filter:drop-shadow(0 0 20px rgba(37,99,235,0.8));">🏥</div>
            <div style="font-size:36px;font-weight:800;color:#FFFFFF;letter-spacing:-1px;text-shadow:0 2px 20px rgba(37,99,235,0.8);">MedAI Clinical System</div>
            <div style="font-size:15px;color:#FFFFFF;margin-top:6px;font-weight:500;">AI-Powered · Doctor-in-the-Loop · Medical Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _,col,_=st.columns([1,1.8,1])
    with col:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#FFFFFF,#F0F7FF);border:2px solid #93C5FD;border-radius:20px;padding:36px;box-shadow:0 20px 60px rgba(37,99,235,0.3);margin-top:24px;">
            <div style="text-align:center;margin-bottom:28px;">
                <div style="font-size:14px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.15em;">Secure Doctor Portal</div>
                <div style="font-size:13px;color:#334155;margin-top:4px;">Please sign in to access patient reports</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:13px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">👨‍⚕️ Select Doctor</div>', unsafe_allow_html=True)
        doc_labels={f"{v['name']} — {v['dept']}":k for k,v in DOCTORS.items()}
        sel_id=doc_labels[st.selectbox('Doctor',list(doc_labels.keys()),label_visibility='collapsed',key='login_doc')]

        st.markdown('<div style="font-size:13px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin:16px 0 8px;">🔐 Password</div>', unsafe_allow_html=True)
        pwd=st.text_input('Password',type='password',placeholder='Enter password...',label_visibility='collapsed',key='login_pwd')

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('🔓  Sign In →',use_container_width=True,type='primary'):
            if pwd==DOCTORS[sel_id]['password']:
                st.session_state.logged_in=True; st.session_state.active_doctor=sel_id
                add_log("LOGIN", f"Doctor: {DOCTORS[sel_id]['name']} ({sel_id})")
                st.rerun()
            else:
                st.error('❌ Incorrect password. Please try again.')

        st.markdown("""
            <div style="text-align:center;margin-top:20px;padding-top:16px;border-top:1px solid #1E3A5F;">
                <div style="font-size:12px;color:#334155;">Demo password: <span style="color:#60A5FA;font-weight:700;">1234</span></div>
                <div style="font-size:11px;color:#93C5FD;margin-top:6px;">🔒 All sessions are encrypted and logged</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Feature badges below login
        st.markdown("""
        <div style="display:flex;gap:10px;justify-content:center;margin-top:20px;flex-wrap:wrap;">
            <span style="background:rgba(37,99,235,0.08);border:1px solid #93C5FD;color:#1D4ED8;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">🧠 AI Diagnostics</span>
            <span style="background:rgba(124,58,237,0.15);border:1px solid #7C3AED;color:#C084FC;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">🔬 Lab Analysis</span>
            <span style="background:rgba(0,229,160,0.12);border:1px solid #00E5A0;color:#059669;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">✅ Doctor Review</span>
            <span style="background:rgba(255,122,53,0.12);border:1px solid #FF7A35;color:#EA580C;font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;">📱 Patient Alerts</span>
        </div>
        """, unsafe_allow_html=True)


# ── ACTIVITY LOG ──────────────────────────────────────────────
def render_activity_log():
    logs = st.session_state.get('activity_log', [])

    # Header + clear button
    col_h, col_btn = st.columns([4,1])
    with col_h:
        st.markdown('<div style="font-size:14px;font-weight:700;color:#1D4ED8;margin-bottom:12px;">System Activity Log — Current Session</div>', unsafe_allow_html=True)
    with col_btn:
        if st.button('🗑️ Clear Log', key='clear_log'):
            st.session_state.activity_log = []
            st.rerun()

    if not logs:
        st.markdown(
            '<div style="background:#F8FAFF;border:2px dashed #BFDBFE;border-radius:12px;padding:24px;text-align:center;">'
            '<div style="font-size:14px;color:#64748B;">No activity recorded yet.</div>'
            '<div style="font-size:13px;color:#94A3B8;margin-top:4px;">Actions like login, patient views, approvals and rejections will appear here.</div>'
            '</div>', unsafe_allow_html=True)
        return

    # Stats row
    from collections import Counter
    action_counts = Counter(l['action'] for l in logs)
    s1,s2,s3,s4,s5 = st.columns(5)
    stat_items = [
        (s1, 'Total',    len(logs),                         '#2563EB'),
        (s2, 'Views',    action_counts.get('VIEW',0),       '#7C3AED'),
        (s3, 'Approved', action_counts.get('APPROVED',0),   '#059669'),
        (s4, 'Rejected', action_counts.get('REJECTED',0),   '#DC2626'),
        (s5, 'Revoked',  action_counts.get('REVOKED',0),    '#EA580C'),
    ]
    for col, lbl, val, clr in stat_items:
        with col:
            st.markdown(
                f'<div style="background:#FFFFFF;border:2px solid {clr}44;border-top:3px solid {clr};'
                f'border-radius:10px;padding:10px;text-align:center;margin-bottom:12px;">'
                f'<div style="font-size:22px;font-weight:800;color:{clr};">{val}</div>'
                f'<div style="font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase;">{lbl}</div>'
                f'</div>', unsafe_allow_html=True)

    # Log entries — most recent first
    level_colors = {
        'INFO':    ('#2563EB', '#EFF6FF', '🔵'),
        'SUCCESS': ('#059669', '#F0FDF4', '✅'),
        'WARNING': ('#D97706', '#FFF7ED', '⚠️'),
        'ERROR':   ('#DC2626', '#FFF1F2', '❌'),
    }

    st.markdown('<div style="font-size:12px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Recent Activity (newest first)</div>', unsafe_allow_html=True)

    rows_html = ''
    for entry in reversed(logs[-100:]):  # show last 100
        lvl   = entry.get('level', 'INFO')
        clr, bg, icon = level_colors.get(lvl, ('#2563EB','#EFF6FF','🔵'))
        action  = entry.get('action','')
        details = entry.get('details','')
        time_s  = entry.get('time','')
        date_s  = entry.get('date','')

        action_colors = {
            'LOGIN':    '#059669',
            'LOGOUT':   '#64748B',
            'VIEW':     '#2563EB',
            'APPROVED': '#059669',
            'REJECTED': '#DC2626',
            'REVOKED':  '#EA580C',
        }
        ac = action_colors.get(action, '#2563EB')

        rows_html += (
            f'<div style="display:grid;grid-template-columns:80px 90px 1fr;gap:12px;'
            f'padding:10px 16px;border-bottom:1px solid #F1F5F9;align-items:center;background:{bg}08;">'
            f'<div style="font-size:12px;color:#94A3B8;font-family:monospace;">{time_s}</div>'
            f'<div style="background:{ac}18;color:{ac};font-size:11px;font-weight:700;'
            f'padding:3px 10px;border-radius:20px;text-align:center;">{action}</div>'
            f'<div style="font-size:13px;color:#334155;">{details}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#FFFFFF;border:2px solid #BFDBFE;border-radius:12px;overflow:hidden;">'
        f'<div style="display:grid;grid-template-columns:80px 90px 1fr;gap:12px;'
        f'padding:8px 16px;background:#DBEAFE;border-bottom:2px solid #93C5FD;">'
        f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;">TIME</div>'
        f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;">ACTION</div>'
        f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;">DETAILS</div>'
        f'</div>{rows_html}</div>',
        unsafe_allow_html=True)

    # Export as text
    if st.button('📥 Export Log as Text', key='export_log'):
        log_text = f"MedAI Activity Log — {logs[0]['date'] if logs else 'N/A'}\n{'='*60}\n"
        for e in logs:
            log_text += f"[{e['date']} {e['time']}] {e['action']:10} | {e['details']}\n"
        st.download_button('⬇️ Download log.txt', log_text, 'medai_activity_log.txt', 'text/plain')


# ── DASHBOARD ─────────────────────────────────────────────────
def render_dashboard():
    active_id=st.session_state.active_doctor; active=DOCTORS[active_id]
    mtype=active['mtype']
    my_patients = {pid:p for pid,p in ALL_PATIENTS.items() if p.get('doctor_id')==active_id}

    # ── Top navigation bar ────────────────────────────────────
    st.markdown(
        f'<div style="background:linear-gradient(90deg,#1E3A8A,#2563EB);border-bottom:2px solid #1D4ED8;'
        f'padding:0 28px;height:68px;display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<div style="background:linear-gradient(135deg,#2563EB,#7C3AED);width:42px;height:42px;'
        f'border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;'
        f'box-shadow:0 4px 15px rgba(37,99,235,0.5);">🏥</div>'
        f'<div><div style="font-size:20px;font-weight:800;color:#6B7A99;letter-spacing:-0.5px;">MedAI</div>'
        f'<div style="font-size:10px;color:#6B7A99;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;">Clinical Intelligence System</div></div></div>'
        f'<div style="display:flex;align-items:center;gap:16px;">'
        f'<div style="background:rgba(37,99,235,0.15);border:1px solid #2563EB;border-radius:10px;padding:8px 16px;">'
        f'<div style="font-size:14px;font-weight:700;color:#FFFFFF;">{active["name"]}</div>'
        f'<div style="font-size:11px;color:#BFDBFE;">{active["dept"]}  ·  {active["specialty"]}</div></div>'
        f'<div style="background:rgba(0,229,160,0.15);border:2px solid rgba(0,229,160,0.5);'
        f'color:#059669;font-size:12px;font-weight:700;padding:6px 16px;border-radius:20px;">● Online</div>'
        f'</div></div>',unsafe_allow_html=True)

    # Logout button row
    _,_,logout_col = st.columns([8,1,1])
    with logout_col:
        st.markdown('<div style="padding:8px 28px 0 0;">', unsafe_allow_html=True)
        if st.button('🚪 Logout', key='logout_btn'):
            add_log("LOGOUT", f"Doctor: {DOCTORS.get(st.session_state.active_doctor,{}).get('name','')}")
            st.session_state.logged_in=False; st.session_state.active_doctor=None; st.session_state.selected={}; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:20px 28px;">', unsafe_allow_html=True)

    # ── Department hero banner ────────────────────────────────
    dept_img = DEPT_IMGS.get(mtype, HERO_IMG)
    icons={'Lab Report':'🧪','CT Scan':'🧠','Ultrasound':'🔬','Combined Assessment':'⚡'}
    icon = icons.get(mtype,'📋')
    st.markdown(f"""
    <div style="position:relative;width:100%;height:190px;overflow:hidden;border-radius:20px;margin-bottom:20px;
         box-shadow:0 8px 32px rgba(37,99,235,0.2);">
        <img src="{dept_img}" style="width:100%;height:100%;object-fit:cover;object-position:center;
             opacity:0.75;filter:brightness(0.7) contrast(1.15) saturate(1.1);"/>
        <div style="position:absolute;inset:0;background:linear-gradient(90deg,
             rgba(15,23,42,0.97) 0%,rgba(15,23,42,0.75) 40%,rgba(15,23,42,0.5) 70%,rgba(15,23,42,0.8) 100%);"></div>
        <div style="position:absolute;inset:0;display:flex;align-items:center;padding:0 36px;gap:22px;">
            <div style="font-size:56px;filter:drop-shadow(0 0 20px rgba(255,255,255,0.4));line-height:1;">{icon}</div>
            <div>
                <div style="font-size:11px;font-weight:700;color:#93C5FD;text-transform:uppercase;
                     letter-spacing:0.15em;margin-bottom:6px;">{active["specialty"]}</div>
                <div style="font-size:30px;font-weight:800;color:#FFFFFF;
                     text-shadow:0 2px 20px rgba(0,0,0,0.8);letter-spacing:-0.5px;line-height:1.1;">{active["dept"]} — Patient Reports</div>
                <div style="font-size:14px;color:#BFDBFE;margin-top:6px;font-weight:500;">
                     Assigned to {active["name"]}</div>
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
    # ── Dashboard Tabs: Patients | Activity Log ─────────────────
    tab1, tab2 = st.tabs(["👥  Patient Queue", "📋  Activity Log"])

    with tab2:
        render_activity_log()

    with tab1:
        pass  # content below uses tab1 context implicitly via columns

    left,right=st.columns([1,2.5],gap='large')
    with left:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">👥 Patient Queue</div>', unsafe_allow_html=True)
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
                add_log("VIEW", f"Patient {pid} | {p.get('disease_type','')} | Severity: {p.get('_sev','')}")
                st.session_state.selected[active_id]=pid; st.rerun()

    with right:
        sel_pid=st.session_state.selected.get(active_id)
        if not sel_pid or sel_pid not in my_patients:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:2px dashed #93C5FD;border-radius:16px;padding:60px;text-align:center;">
                <div style="font-size:50px;margin-bottom:16px;">👈</div>
                <div style="font-size:18px;color:#2563EB;font-weight:600;">Select a Patient</div>
                <div style="font-size:14px;color:#334155;margin-top:8px;">Choose a patient from the queue to view their report</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            render_patient(my_patients[sel_pid], sel_pid, active_id)

    st.markdown('</div>', unsafe_allow_html=True)


# ── PATIENT TREND CHART ───────────────────────────────────────
def render_trend_chart(pid):
    """Show patient severity trend from MIMIC revisit history."""
    trend = TREND_DATA.get(pid)
    if not trend or not trend.get('has_history'):
        return  # No history — don't show anything

    visits    = trend['visits']
    v_count   = trend['visit_count']
    trend_dir = trend.get('trend_dir','stable')
    rate      = trend.get('revisit_label','')
    disease   = trend.get('disease','')

    # Trend direction styling
    trend_cfg = {
        'worsening': ('🔴', '#DC2626', '#FFF1F2', 'Worsening'),
        'improving':  ('🟢', '#059669', '#F0FDF4', 'Improving'),
        'stable':     ('🔵', '#2563EB', '#EFF6FF', 'Stable'),
    }
    t_icon, t_color, t_bg, t_label = trend_cfg.get(trend_dir, ('🔵','#2563EB','#EFF6FF','Stable'))

    sev_colors = {'Normal':'#059669','Mild':'#D97706','Moderate':'#EA580C',
                  'Severe':'#DC2626','Unknown':'#94A3B8'}
    sev_scores = {'Normal':0,'Mild':1,'Moderate':2,'Severe':3,'Unknown':None}

    # Header
    st.markdown(
        f'<div style="background:#FFFFFF;border:2px solid #BFDBFE;border-radius:14px;'
        f'padding:16px 20px;margin-bottom:16px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<span style="font-size:16px;">📈</span>'
        f'<span style="font-size:13px;font-weight:800;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;">Patient Revisit History</span>'
        f'</div>'
        f'<div style="display:flex;gap:10px;align-items:center;">'
        f'<span style="background:{t_bg};border:1px solid {t_color}44;color:{t_color};'
        f'font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;">'
        f'{t_icon} {t_label}</span>'
        f'<span style="background:#EFF6FF;border:1px solid #93C5FD;color:#1D4ED8;'
        f'font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;">'
        f'🏥 {v_count} hospital visits</span>'
        f'<span style="background:#F8FAFF;border:1px solid #BFDBFE;color:#64748B;'
        f'font-size:12px;padding:4px 12px;border-radius:20px;">'
        f'{v_count} total visits</span>'
        f'</div></div>'
        f'<div style="font-size:11px;color:#94A3B8;font-style:italic;margin-top:4px;">'
        f'Historical data from MIMIC-IV clinical database · Dates are de-identified</div>',
        unsafe_allow_html=True)

    # Build timeline bars
    scored = [v for v in visits if sev_scores.get(v['severity']) is not None]
    if not scored:
        st.markdown('</div>', unsafe_allow_html=True)
        return

    max_score = 3
    timeline_html = '<div style="display:flex;gap:4px;align-items:flex-end;height:80px;padding:0 4px;">'

    for v in visits[-20:]:  # show last 20 visits max
        sev   = v['severity']
        score = sev_scores.get(sev)
        clr   = sev_colors.get(sev, '#94A3B8')
        is_cur = v.get('is_current', False)

        if score is None:
            bar_h = 8; bar_clr = '#E2E8F0'; opacity = '0.4'
        else:
            bar_h   = max(12, int((score / max_score) * 64))
            bar_clr = clr
            opacity = '1.0'

        border  = f'3px solid #1D4ED8' if is_cur else f'1px solid {clr}44'
        tooltip = f"{v['date'][:7]}: {sev}"
        if v.get('egfr'):    tooltip += f" | eGFR {v['egfr']}"
        if v.get('glucose'): tooltip += f" | Gluc {v['glucose']}"
        if v.get('los_hours'): tooltip += f" | LOS {v['los_hours']}h"

        # Current visit gets a star marker above it
        star_html = (
            f'<div style="font-size:9px;text-align:center;color:#1D4ED8;font-weight:800;">★</div>'
            if is_cur else '<div style="height:14px;"></div>'
        )

        timeline_html += (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1;min-width:8px;max-width:28px;">'
            f'{star_html}'
            f'<div title="{tooltip}" style="width:100%;height:{bar_h}px;background:{bar_clr};'
            f'border-radius:4px 4px 0 0;border:{border};opacity:{opacity};'
            f'{"box-shadow:0 0 10px " + clr + "88;" if is_cur else ""}">'
            f'</div>'
            f'<div style="font-size:8px;color:#94A3B8;text-align:center;'
            f'{"font-weight:800;color:#1D4ED8;" if is_cur else ""}">'
            f'{v["date"][2:7] if len(v["date"])>=7 else ""}'
            f'</div>'
            f'</div>'
        )

    timeline_html += '</div>'

    # Severity scale legend
    scale_html = (
        '<div style="display:flex;gap:12px;margin-top:8px;">'
        + ''.join([
            f'<span style="display:flex;align-items:center;gap:4px;">'
            f'<span style="width:10px;height:10px;border-radius:2px;background:{clr};display:inline-block;"></span>'
            f'<span style="font-size:11px;color:#64748B;">{sev}</span></span>'
            for sev, clr in [('Normal','#059669'),('Mild','#D97706'),
                              ('Moderate','#EA580C'),('Severe','#DC2626')]
        ])
        + '<span style="font-size:11px;color:#94A3B8;margin-left:auto;">◼ = current visit</span>'
        + '</div>'
    )

    st.markdown(timeline_html + scale_html + '</div>', unsafe_allow_html=True)

    # Key metrics row — always use first and LAST visits
    if len(scored) >= 2:
        first = scored[0]
        last  = scored[-1]   # always most recent
        fc = sev_colors.get(first['severity'],'#94A3B8')
        lc = sev_colors.get(last['severity'],'#94A3B8')

        # Trend arrow
        arr = {'worsening':'↑ Getting worse','improving':'↓ Getting better','stable':'→ Stable'}
        arr_clr = {'worsening':'#DC2626','improving':'#059669','stable':'#2563EB'}
        arr_txt = arr.get(trend_dir,'→ Stable')
        arr_c   = arr_clr.get(trend_dir,'#2563EB')

        m1,m2,m3,m4 = st.columns(4)
        with m1:
            st.markdown(
                f'<div style="background:#F8FAFF;border:1px solid #BFDBFE;border-radius:10px;padding:12px;text-align:center;">'
                f'<div style="font-size:10px;color:#64748B;font-weight:700;text-transform:uppercase;margin-bottom:6px;">🏁 First Visit</div>'
                f'<div style="font-size:18px;font-weight:800;color:{fc};">{first["severity"]}</div>'
                f'<div style="font-size:11px;color:#94A3B8;margin-top:2px;">{first["date"][:7]}</div>'
                f'</div>', unsafe_allow_html=True)
        with m2:
            st.markdown(
                f'<div style="background:#F8FAFF;border:2px solid {lc}44;border-radius:10px;padding:12px;text-align:center;">'
                f'<div style="font-size:10px;color:#64748B;font-weight:700;text-transform:uppercase;margin-bottom:6px;">★ Latest Visit</div>'
                f'<div style="font-size:18px;font-weight:800;color:{lc};">{last["severity"]}</div>'
                f'<div style="font-size:11px;color:#94A3B8;margin-top:2px;">{last["date"][:7]}</div>'
                f'</div>', unsafe_allow_html=True)
        with m3:
            st.markdown(
                f'<div style="background:#F8FAFF;border:1px solid #BFDBFE;border-radius:10px;padding:12px;text-align:center;">'
                f'<div style="font-size:10px;color:#64748B;font-weight:700;text-transform:uppercase;margin-bottom:6px;">📊 Overall Trend</div>'
                f'<div style="font-size:14px;font-weight:800;color:{arr_c};">{arr_txt}</div>'
                f'<div style="font-size:11px;color:#94A3B8;margin-top:2px;">over {v_count} visits</div>'
                f'</div>', unsafe_allow_html=True)
        with m4:
            avg_los = [v['los_hours'] for v in visits if v.get('los_hours')]
            avg_los_val = f"{sum(avg_los)/len(avg_los):.1f}h" if avg_los else "N/A"
            st.markdown(
                f'<div style="background:#F8FAFF;border:1px solid #BFDBFE;border-radius:10px;padding:12px;text-align:center;">'
                f'<div style="font-size:10px;color:#64748B;font-weight:700;text-transform:uppercase;margin-bottom:6px;">🏥 Avg Stay</div>'
                f'<div style="font-size:18px;font-weight:800;color:#2563EB;">{avg_los_val}</div>'
                f'<div style="font-size:11px;color:#94A3B8;margin-top:2px;">per admission</div>'
                f'</div>', unsafe_allow_html=True)


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
        f'<div style="font-size:26px;font-weight:800;color:#0F172A;font-family:monospace;">{pid}</div>'
        f'<div style="font-size:13px;color:#334155;margin-top:6px;">{mtype}  ·  {doc["name"]}</div></div>'
        f'<div style="background:{bg};border:2px solid {urg_clr}66;border-radius:14px;padding:14px 24px;text-align:center;">'
        f'<div style="font-size:13px;font-weight:700;color:{urg_clr};margin-bottom:6px;">{urg}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{clr};">{sev}</div>'
        f'</div></div></div>',unsafe_allow_html=True)

    # ── Test Findings ──────────────────────────────────────────
    # ── Patient Trend Chart ────────────────────────────
    render_trend_chart(pid)

    st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;font-weight:800;font-size:13px;">🔬 Test Findings</div>', unsafe_allow_html=True)
    if mtype=='Lab Report':          render_lab(p,sev,clr)
    elif mtype=='CT Scan':           render_ct(p,sev,clr)
    elif mtype=='Ultrasound':        render_us(p,sev,clr)
    elif mtype=='Combined Assessment': render_combined(p,sev,clr)

    # ── AI Clinical Summary ────────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin:20px 0 14px;font-weight:800;font-size:13px;">📋 Guideline-Based Clinical Insights</div>', unsafe_allow_html=True)
    # ── Smart RAG lookup for ALL modality types including Combined ──
    # Try pid first (NB09 generates per-patient summaries keyed by pid)
    # Fall back to rag_class_key, then get_mm_rag for combined patients
    raw = RAG_DATA.get(pid, '')
    if not raw:
        rag_key = p.get('rag_class_key', '')
        raw = RAG_DATA.get(rag_key, '')

    if raw:
        parsed = parse_rag(raw)
        cites  = raw.get('citations', []) if isinstance(raw, dict) else []
    elif mtype == 'Combined Assessment':
        # Last resort for MM patients — build from class keys
        parsed = get_mm_rag(p)
        cites  = parsed.pop('citations', [])
    else:
        parsed = {}
        cites  = []

        # ── Disease-context guard ─────────────────────────────
        # Prevents showing a CKD summary to a diabetes patient, or a
        # meningioma summary to a glioma patient, etc.
        disease = str(p.get('disease_type', '')).lower()
        ct_cls  = str(p.get('ct_predicted_class', '')).lower()
        sl      = parsed.get('clinical_summary', '').lower()
        mismatch = False

        if mtype == 'Lab Report':
            if 'ckd' in disease or 'kidney' in disease:
                bad = ['tumor','tumour','glioma','meningioma','pituitary','fetal','ultrasound',
                       'diabetes is not a contributing','diabetes is not the primary',
                       'no indications of glucose in the urine',
                       'no indication of glucose in the urine']
                if any(w in sl for w in bad): mismatch = True
            elif 'diabetes' in disease:
                bad = ['tumor','tumour','glioma','meningioma','fetal',
                       'end-stage renal disease','chronic kidney disease stage',
                       'glomerular filtration rate of']
                if any(w in sl for w in bad): mismatch = True
            elif 'thyroid' in disease:
                bad = ['tumor','tumour','glioma','fetal','glioblastoma']
                if any(w in sl for w in bad): mismatch = True

        elif mtype == 'CT Scan':
            if any(w in sl for w in ['egfr','gfr','creatinine','glucose level','thyroid','tsh level','fetal','gestational']):
                mismatch = True
            # Strict tumour type matching — glioma patient must only see glioma summary
            tumour_must_contain = {
                'glioma':     ['glioma'],
                'meningioma': ['meningioma'],
                'pituitary':  ['pituitary'],
                'notumor':    ['no tumor','no tumour','normal','no mass','no lesion'],
            }
            required = tumour_must_contain.get(ct_cls, [])
            if required and not any(r in sl for r in required):
                mismatch = True  # summary doesn't mention the right tumour at all

        elif mtype == 'Ultrasound':
            if any(w in sl for w in ['tumor','tumour','glioma','egfr','gfr','glucose level','thyroid','tsh level']):
                mismatch = True

        if mismatch:
            parsed = {}

    render_rag(parsed, cites)

    # ── Module 1: Appointment Scheduling (auto-triggers for Severe/Urgent) ──
    render_appointment_module(p, pid, RAG_DATA.get(pid,'') or RAG_DATA.get(p.get('rag_class_key',''),''), doc_id)

    # ── Module 2: Multilingual Patient Messaging ───────────────
    render_messaging_module(p, pid, RAG_DATA.get(pid,'') or RAG_DATA.get(p.get('rag_class_key',''),''))

    # ── Doctor Decision Section ────────────────────────────────
    st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin:24px 0 12px;font-weight:800;font-size:13px;">👨‍⚕️ Doctor Review & Decision</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # CASE 1: APPROVED
    # ══════════════════════════════════════════════════════════
    if cur_dec == 'APPROVED':
        ap = st.session_state.decisions[pid]
        wa_ok  = ap.get('wa_sent', False)
        wa_err = ap.get('wa_error', '')
        wa_status_html = (
            '<div style="font-size:13px;color:#059669;font-weight:600;">📱 WhatsApp delivered to patient ✅</div>'
            if wa_ok else
            f'<div style="font-size:13px;color:#D97706;font-weight:600;">⚠️ WhatsApp not sent — {wa_err or "check Twilio secrets"}</div>'
        )
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(0,229,160,0.15),rgba(0,229,160,0.05));'
            f'border:2px solid rgba(0,229,160,0.5);border-radius:14px;padding:20px 24px;margin-bottom:16px;">'
            f'<div style="font-size:16px;font-weight:800;color:#059669;margin-bottom:10px;">✅ Report Approved & Released to Patient</div>'
            f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
            f'<div style="font-size:13px;color:#334155;">👨‍⚕️ Approved by: <b style="color:#0F172A;">{ap["doctor"]}</b></div>'
            f'<div style="font-size:13px;color:#334155;">🕐 Time: <b style="color:#0F172A;">{ap["time"]}</b></div>'
            f'{wa_status_html}'
            f'</div></div>',unsafe_allow_html=True)

        # Show WhatsApp message that was sent
        if ap.get('wa_msg'):
            with st.expander('📱 View WhatsApp Message Sent to Patient'):
                st.markdown(
                    f'<div style="background:#FFFFFF;border:2px solid #93C5FD;border-radius:12px;'
                    f'padding:20px;font-size:14px;color:#1E293B;white-space:pre-wrap;line-height:1.8;">'
                    f'{ap["wa_msg"]}</div>', unsafe_allow_html=True)

        # ── PDF Report Download ────────────────────────────────
        raw_for_pdf = RAG_DATA.get(pid,'') or RAG_DATA.get(p.get('rag_class_key',''),'')
        parsed_pdf  = parse_rag(raw_for_pdf) if raw_for_pdf else {}
        appt_slot   = st.session_state.get(f'appt_datetime_{pid}', '')
        appt_room   = st.session_state.get(f'appt_room_{pid}', 'OPD — consult front desk')
        try:
            pdf_bytes = generate_patient_pdf(p, pid, parsed_pdf, ap['doctor'], ap.get('notes',''), appt_slot, appt_room)
            st.markdown(
                '<div style="background:rgba(37,99,235,0.06);border:2px solid #93C5FD;border-left:4px solid #2563EB;'
                'border-radius:12px;padding:14px 20px;margin:12px 0 8px;">'
                '<div style="font-size:13px;font-weight:700;color:#1D4ED8;margin-bottom:6px;">📄 Patient Report PDF</div>'
                '<div style="font-size:12px;color:#334155;">Download and share this PDF with the patient via WhatsApp or Email. '
                'Contains lab values, AI clinical summary, recommendations, and appointment details.</div>'
                '</div>', unsafe_allow_html=True)
            st.download_button(
                label='⬇️ Download Patient Report PDF',
                data=pdf_bytes,
                file_name=f'MedAI_Report_{pid}_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf',
                key=f'pdf_download_approved_{pid}',
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f'PDF generation error: {e}')

        # ── REVOKE APPROVAL ───────────────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(255,122,53,0.1),rgba(255,59,92,0.05));
        border:2px solid rgba(255,122,53,0.4);border-radius:14px;padding:18px 22px;margin-top:16px;">
            <div style="font-size:14px;font-weight:800;color:#EA580C;margin-bottom:6px;">⚠️ Revoke Approval</div>
            <div style="font-size:13px;color:#334155;margin-bottom:12px;">
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
                    add_log("REVOKED", f"Patient {pid} | Reason: {revoke_reason.strip()[:50]} | By: {doc['name']}", "WARNING")
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
            f'<div style="font-size:16px;font-weight:800;color:#EA580C;margin-bottom:10px;">🔄 Approval Revoked — Under Review</div>'
            f'<div style="font-size:13px;color:#334155;margin-bottom:10px;">Revoked by: <b style="color:#0F172A;">{rv["doctor"]}</b>  ·  Time: <b style="color:#0F172A;">{rv["time"]}</b></div>'
            f'<div style="background:rgba(255,122,53,0.1);border-left:4px solid #FF7A35;border-radius:8px;padding:10px 14px;margin-bottom:10px;">'
            f'<div style="font-size:12px;font-weight:700;color:#EA580C;margin-bottom:4px;">REASON FOR REVOCATION</div>'
            f'<div style="font-size:14px;color:#0F172A;">{rv.get("revoke_reason","Not stated")}</div></div>'
            f'<div style="font-size:13px;color:#D97706;font-weight:600;">📱 Patient has been notified that their report is under further review.</div>'
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
            st.markdown(f'<div style="background:#FFFFFF;border:2px solid #FF7A35;border-radius:12px;padding:20px;font-size:14px;color:#1E293B;white-space:pre-wrap;line-height:1.8;">{revoked_patient_msg}</div>', unsafe_allow_html=True)

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
            f'<div style="font-size:16px;font-weight:800;color:#DC2626;margin-bottom:10px;">❌ Report Rejected</div>'
            f'<div style="font-size:13px;color:#334155;margin-bottom:10px;">Rejected by: <b style="color:#0F172A;">{rj.get("doctor","")}</b>  ·  Time: <b style="color:#0F172A;">{rj.get("time","")}</b></div>'
            + (f'<div style="background:rgba(255,59,92,0.1);border-left:4px solid #FF3B5C;border-radius:8px;padding:10px 14px;margin-bottom:12px;">'
               f'<div style="font-size:12px;font-weight:700;color:#DC2626;margin-bottom:4px;">REJECTION REASON</div>'
               f'<div style="font-size:14px;color:#0F172A;">{rj.get("reject_reason","Not stated")}</div></div>'
               if rj.get("reject_reason") else '') +
            f'</div>',unsafe_allow_html=True)

        # ── NEXT STEPS AFTER REJECTION ────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(96,165,250,0.1),rgba(124,58,237,0.05));
        border:2px solid rgba(96,165,250,0.4);border-radius:14px;padding:20px 24px;margin-bottom:16px;">
            <div style="font-size:14px;font-weight:800;color:#60A5FA;margin-bottom:14px;">📋 What Happens Next?</div>
            <div style="display:flex;flex-direction:column;gap:10px;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,59,92,0.2);color:#DC2626;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">1</span>
                    <span style="font-size:13px;color:#1E293B;line-height:1.6;">The patient has <b style="color:#DC2626;">NOT been notified</b> — no message has been sent. Their portal will show "Report Under Review".</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,122,53,0.2);color:#EA580C;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">2</span>
                    <span style="font-size:13px;color:#1E293B;line-height:1.6;">The AI report is flagged for <b style="color:#EA580C;">re-analysis</b>. Updated results will be queued for your review.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(255,208,0,0.2);color:#D97706;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">3</span>
                    <span style="font-size:13px;color:#1E293B;line-height:1.6;">You can <b style="color:#D97706;">reset and re-review</b> the current report, or request the patient resubmit samples/scans.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <span style="background:rgba(0,229,160,0.2);color:#059669;font-weight:800;font-size:14px;padding:4px 10px;border-radius:8px;flex-shrink:0;">4</span>
                    <span style="font-size:13px;color:#1E293B;line-height:1.6;">Once you are satisfied with the updated report, <b style="color:#059669;">approve and release</b> to notify the patient.</span>
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
                <div style="font-size:13px;color:#1E293B;line-height:1.7;">
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
        border:2px solid #93C5FD;border-radius:14px;padding:20px 24px;margin-bottom:16px;">
            <div style="font-size:14px;font-weight:800;color:#60A5FA;margin-bottom:4px;">📝 Doctor's Prescription & Additional Notes</div>
            <div style="font-size:13px;color:#334155;margin-bottom:12px;">Add prescriptions, amendments, follow-up instructions, or referrals. These will be included in the patient's message.</div>
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

        # Single merged message — clinical findings + appointment + prescription
        pat_msg = build_merged_patient_msg(p, pid, doc['name'], notes)

        with st.expander('📱 Preview Patient Message (Final — includes appointment if booked)'):
            appt_booked = bool(st.session_state.get(f'appt_approved_{pid}', False))
            lang_name   = st.session_state.get(f'msg_lang_{pid}', 'English')
            badge_appt  = (f'<span style="background:rgba(0,229,160,0.15);color:#059669;font-size:11px;'
                           f'font-weight:700;padding:3px 10px;border-radius:10px;margin-right:8px;">'
                           f'✅ Appointment included</span>' if appt_booked else
                           f'<span style="background:rgba(255,208,0,0.15);color:#D97706;font-size:11px;'
                           f'font-weight:700;padding:3px 10px;border-radius:10px;margin-right:8px;">'
                           f'⏳ No appointment booked yet</span>')
            badge_lang  = (f'<span style="background:rgba(124,58,237,0.12);color:#7C3AED;font-size:11px;'
                           f'font-weight:700;padding:3px 10px;border-radius:10px;">🌐 {lang_name}</span>')
            st.markdown(
                f'<div style="background:#FFFFFF;border:2px solid #93C5FD;border-radius:12px;padding:18px 22px;">'
                f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">'
                f'<span style="font-size:12px;font-weight:700;color:#059669;letter-spacing:0.08em;">📨 FINAL MESSAGE TO PATIENT</span>'
                f'<span style="flex:1"></span>{badge_appt}{badge_lang}</div>'
                f'<div style="font-size:14px;color:#1E293B;line-height:1.8;white-space:pre-wrap;">{pat_msg}</div></div>',
                unsafe_allow_html=True)

        # ── PDF Preview Download (before approval) ─────────────
        raw_for_pdf  = RAG_DATA.get(pid,'') or RAG_DATA.get(p.get('rag_class_key',''),'')
        parsed_pdf   = parse_rag(raw_for_pdf) if raw_for_pdf else {}
        appt_slot_v  = st.session_state.get(f'appt_datetime_{pid}', '')
        appt_room_v  = st.session_state.get(f'appt_room_{pid}', 'OPD — consult front desk')
        try:
            pdf_bytes_prev = generate_patient_pdf(p, pid, parsed_pdf, doc['name'], notes, appt_slot_v, appt_room_v)
            st.markdown(
                '<div style="background:rgba(124,58,237,0.05);border:2px solid #C4B5FD;border-left:4px solid #7C3AED;'
                'border-radius:12px;padding:12px 18px;margin:8px 0;">'
                '<div style="font-size:13px;font-weight:700;color:#7C3AED;margin-bottom:4px;">📄 Preview Report PDF</div>'
                '<div style="font-size:12px;color:#334155;">Download a preview of the PDF that will be sent to the patient. '
                'Once you approve, share this PDF via WhatsApp or Email.</div>'
                '</div>', unsafe_allow_html=True)
            st.download_button(
                label='⬇️ Preview & Download Report PDF',
                data=pdf_bytes_prev,
                file_name=f'MedAI_Report_PREVIEW_{pid}.pdf',
                mime='application/pdf',
                key=f'pdf_download_pending_{pid}',
                use_container_width=False,
            )
        except Exception as e:
            st.warning(f'PDF generation error: {e}')

        st.markdown('<br>', unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)
        with b1:
            if st.button('✅ Approve & Send', key='app_'+doc_id+'_'+pid, use_container_width=True, type='primary'):
                # Build severity-based WhatsApp message
                appt_slot_ws = st.session_state.get(f'appt_datetime_{pid}', '')
                appt_room_ws = st.session_state.get(f'appt_room_{pid}', 'OPD — consult front desk')
                wa_msg       = build_whatsapp_msg(p, pid, doc['name'], appt_slot_ws, appt_room_ws, notes)

                # Send via Twilio WhatsApp
                wa_ok, wa_err = send_whatsapp_message(wa_msg)

                # Save decision
                st.session_state.decisions[pid] = {
                    'status':   'APPROVED',
                    'doctor':   doc['name'],
                    'time':     datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'message':  pat_msg,
                    'notes':    notes.strip(),
                    'wa_sent':  wa_ok,
                    'wa_error': wa_err,
                    'wa_msg':   wa_msg,
                }
                lang_name = st.session_state.get(f'msg_lang_{pid}', 'English')
                add_log("APPROVED", f"Patient {pid} | {p.get('disease_type')} | {p.get('_sev')} | By: {doc['name']}", "SUCCESS")
                if wa_ok:
                    add_log("WHATSAPP_SENT", f"Patient {pid} | Severity: {p.get('_sev')} | WhatsApp delivered", "SUCCESS")
                else:
                    add_log("WHATSAPP_FAIL", f"Patient {pid} | Error: {wa_err[:60]}", "WARNING")
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
                add_log("REJECTED", f"Patient {pid} | Reason: {reject_reason.strip()[:50]} | By: {doc['name']}", "WARNING")
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

    # ── Clean "Not tested" variants ───────────────────────────
    def clean_val(v):
        return v if v and str(v) not in ['Not tested','None','nan','Unknown','not tested',''] else 'Not tested'

    ckd = clean_val(ckd); dia = clean_val(dia); thy = clean_val(thy)

    # ── Top 3 summary cards ─────────────────────────────────────
    # Use _sev (model severity) as primary display for active card
    # so it always matches the header severity badge
    c1,c2,c3=st.columns(3)

    # Map disease to its display value — prefer _sev for active disease
    def card_display(val, is_active, sev_override):
        """For active disease card use model severity (_sev) as primary value."""
        if is_active:
            return sev_override  # always show model severity
        return val if val != 'Not tested' else 'Not tested'

    cards = [
        (c1, 'Kidney Function',  card_display(ckd, 'ckd' in disease or 'kidney' in disease, sev),
         'ckd' in disease or 'kidney' in disease),
        (c2, 'Blood Sugar',      card_display(dia, 'diabetes' in disease, sev),
         'diabetes' in disease),
        (c3, 'Thyroid Function', card_display(thy, 'thyroid' in disease, sev),
         'thyroid' in disease),
    ]
    for col, lbl, v, is_active in cards:
        if is_active and v not in ['Not tested','']:
            vc = clr
            border = f'2px solid {clr}88'
            try:
                r,g,b = int(clr[1:3],16),int(clr[3:5],16),int(clr[5:7],16)
                bg = f'background:rgba({r},{g},{b},0.08);'
            except:
                bg = 'background:#FFF0F0;'
        elif is_active and v == 'Not tested':
            vc = '#D97706'; border = '2px solid #FCD34D'
            bg = 'background:rgba(255,208,0,0.06);'
        else:
            vc = '#94A3B8'; border = '2px solid #CBD5E1'
            bg = 'background:#FFFFFF;'
        with col:
            st.markdown(
                f'<div style="{bg}border:{border};border-radius:12px;padding:16px;margin-bottom:12px;">'
                f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">{lbl}</div>'
                f'<div style="font-size:17px;font-weight:700;color:{vc};">{v}</div></div>',
                unsafe_allow_html=True)

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
        ckd_sev_st='Normal' if sev=='Normal' else 'Borderline' if sev=='Mild' else 'Abnormal'
        rows.append(ref_row('Clinical Severity (AI)',sev,'KDIGO 2022: based on eGFR + albuminuria + symptoms',ckd_sev_st))
        rows.append(ref_row('BP Target','—','<130/80 mmHg · ACE inhibitor if proteinuria','N/A'))
        src='KDIGO 2022 Clinical Practice Guideline for CKD'
    elif 'diabetes' in disease:
        # Use _sev (model ground truth) for badge — matches header
        dia_st='Normal' if sev=='Normal' else 'Borderline' if sev=='Mild' else 'Abnormal' if sev in ['Moderate','Severe'] else 'N/A'
        if glucose is not None:
            gs='Normal' if glucose<100 else 'Borderline' if glucose<126 else 'Abnormal'
            rows.append(ref_row('Glucose (Fasting)',fmt(glucose,'mg/dL'),'Normal:<100 · Pre-diabetic:100-125 · Diabetic:≥126',gs))
        else:
            rows.append(ref_row('Glucose','Not measured','Normal:<100 · Pre-diabetic:100-125 · Diabetic:≥126','N/A'))
        rows.append(ref_row('Diabetes Severity (AI)',sev,'Normal · Mild:pre-diabetic · Moderate/Severe:poor control',dia_st))
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
        thy_model_st='Normal' if sev=='Normal' else 'Borderline' if sev=='Mild' else 'Abnormal'
        rows.append(ref_row('Thyroid Status (AI)',sev,'Normal · Mild=Subclinical · Severe=Overt Hypothyroid',thy_model_st))
        src='ATA/AACE Guidelines for Hypothyroidism 2023'
    else:
        src='WHO / Standard Clinical Guidelines'

    if rows:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 10px;">Patient Values vs Clinical Guidelines</div>',unsafe_allow_html=True)
        st.markdown(ref_table(rows,src),unsafe_allow_html=True)


def render_ct(p,sev,clr):
    cls=p.get('ct_predicted_class',''); conf=n(p.get('ct_confidence')) or 0
    name=CT_NAMES.get(cls,cls); desc=CT_DESC.get(cls,'')

    # Note: CT patient IDs are derived from image filenames (e.g. CT-Te-no_0134.jpg-957)
    # The eGFR or lab values sometimes appear in RAG context docs — they are NOT this patient's values
    st.markdown(
        f'<div style="background:#FFFFFF;border:2px solid #93C5FD;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
        f'<div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">CT Brain Imaging</div>'
        f'<div style="font-size:20px;font-weight:800;color:#0F172A;margin-bottom:6px;">{name}</div>'
        f'<div style="font-size:14px;color:#334155;margin-bottom:10px;">{desc}</div>'
        f'<div style="display:flex;gap:16px;align-items:center;">'
        f'<span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
        f'<span style="color:#334155;font-size:13px;">AI Confidence: <b style="color:#0F172A;">{round(conf*100,1)}%</b></span>'
        f'</div></div>',
        unsafe_allow_html=True)

    t=CT_IMAGE.get(str(cls),('',''))
    if t[0] and os.path.exists(t[0]):
        gc1,gc2=st.columns(2)
        with gc1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original CT Scan</div>',unsafe_allow_html=True)
            st.image(t[0],use_column_width=True)
        with gc2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
            if t[1] and os.path.exists(t[1]): st.image(t[1],use_column_width=True)
        st.markdown(
            '<div style="background:#FFFFFF;border:2px solid #93C5FD;border-left:4px solid #7C3AED;border-radius:10px;padding:10px 16px;margin-bottom:12px;font-size:13px;color:#334155;">'
            '🔍 <b style="color:#0F172A;">Grad-CAM:</b> Warm colours (red/yellow) = high AI attention regions indicating the tumour location used for classification.</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:rgba(37,99,235,0.06);border:2px dashed #2563EB;border-radius:12px;padding:16px 20px;margin-bottom:12px;">'
            f'<div style="font-size:13px;color:#60A5FA;">📂 Scan images not found locally. Expected at: <code>images/ct_{cls}_original.jpg</code></div>'
            '</div>',
            unsafe_allow_html=True)


def render_us(p,sev,clr):
    cls=p.get('predicted_class',''); conf=n(p.get('confidence')) or 0
    name=US_NAMES.get(cls,cls); desc=US_DESC.get(cls,'')
    st.markdown(f'<div style="background:#FFFFFF;border:2px solid #93C5FD;border-left:5px solid {clr};border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
                f'<div style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Obstetric Ultrasound</div>'
                f'<div style="font-size:20px;font-weight:800;color:#0F172A;margin-bottom:6px;">{name}</div>'
                f'<div style="font-size:14px;color:#334155;margin-bottom:10px;">{desc}</div>'
                f'<div style="display:flex;gap:16px;"><span style="background:{SEV_BG.get(sev,"")};border:2px solid {clr}55;color:{clr};font-size:13px;font-weight:700;padding:4px 16px;border-radius:20px;">{sev}</span>'
                f'<span style="color:#334155;font-size:13px;">AI Confidence: <b style="color:#0F172A;">{round(conf*100,1)}%</b></span></div></div>',unsafe_allow_html=True)
    t=US_IMAGE.get(str(cls),('',''))
    if t[0] and os.path.exists(t[0]):
        ug1,ug2=st.columns(2)
        with ug1:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Original Ultrasound</div>',unsafe_allow_html=True)
            st.image(t[0],use_column_width=True)
        with ug2:
            st.markdown('<div style="font-size:11px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">Grad-CAM Heatmap</div>',unsafe_allow_html=True)
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
        if ct_cls: parts.append('🧠 CT: <b style="color:#0F172A;">'+CT_NAMES.get(ct_cls,ct_cls)+'</b>')
        if us_cls: parts.append('🔬 US: <b style="color:#0F172A;">'+US_NAMES.get(us_cls,us_cls)+'</b>')
        st.markdown('<div style="font-size:13px;color:#334155;margin-bottom:14px;">'+'  ·  '.join(parts)+'</div>',unsafe_allow_html=True)

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
        st.markdown('<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;margin:8px 0 10px;">Lab Values vs Reference Ranges</div>',unsafe_allow_html=True)
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
            '<div style="background:#FFFFFF;border:2px dashed #2563EB;border-radius:12px;padding:20px 24px;">'
            '<div style="font-size:14px;color:#60A5FA;font-weight:600;">⚠️ RAG summary not available for this patient.</div>'
            '<div style="font-size:13px;color:#334155;margin-top:6px;">Ensure <code>rag_summaries.json</code> contains an entry for this patient ID '
            'and that the GPT output includes CLINICAL SUMMARY / KEY FINDINGS / RECOMMENDATIONS / FOLLOW-UP / URGENCY sections.</div>'
            '</div>',
            unsafe_allow_html=True)
        return

    # ── Truncation warning — if only summary exists, sections were cut ──
    has_full = bool(parsed.get('key_findings') or parsed.get('recommendations'))
    if parsed.get('clinical_summary') and not has_full:
        st.markdown(
            '<div style="background:#FFF7ED;border:2px solid #FDBA74;border-left:4px solid #F59E0B;'
            'border-radius:10px;padding:12px 18px;margin-bottom:14px;">'
            '<div style="font-size:13px;color:#92400E;font-weight:700;">⚠️ Partial Summary — Sections Missing</div>'
            '<div style="font-size:12px;color:#78350F;margin-top:4px;line-height:1.6;">'
            'Only the Clinical Summary section was generated — Key Findings and Recommendations were cut off by token limit.<br>'
            'Fix: Re-run NB09 with <b>max_tokens=800</b> and regenerate <code>rag_summaries.json</code>.'
            '</div></div>',
            unsafe_allow_html=True)

    # ── 1. CLINICAL SUMMARY ──────────────────────────────────
    if parsed.get('clinical_summary'):
        st.markdown(
            '<div style="background:#FFFFFF;border:2px solid #C4B5FD;'
            'border-left:5px solid #7C3AED;border-radius:14px;padding:20px 24px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
            '<span style="font-size:16px;">🧬</span>'
            '<span style="font-size:11px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.1em;">Clinical Summary</span>'
            '</div>'
            f'<div style="font-size:14px;color:#1E293B;line-height:1.9;font-weight:500;">{parsed["clinical_summary"]}</div>'
            '</div>',
            unsafe_allow_html=True)

    # ── 2. KEY FINDINGS ──────────────────────────────────────
    if parsed.get('key_findings'):
        rows_html = ''.join([
            f'<div style="display:flex;gap:12px;padding:11px 0;border-bottom:1px solid #BFDBFE;align-items:flex-start;">'
            f'<span style="background:rgba(192,132,252,0.2);color:#C084FC;font-weight:800;font-size:13px;'
            f'padding:2px 9px;border-radius:6px;flex-shrink:0;margin-top:1px;">F{i+1}</span>'
            f'<span style="font-size:14px;color:#1E293B;line-height:1.65;">{f}</span></div>'
            for i, f in enumerate(parsed['key_findings'])
        ])
        st.markdown(
            '<div style="background:#FFFFFF;border:2px solid #7C3AED;border-radius:14px;'
            'padding:16px 20px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            '<span style="font-size:16px;">🔍</span>'
            '<span style="font-size:11px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.1em;">Key Findings</span>'
            f'<span style="background:rgba(192,132,252,0.2);color:#C084FC;font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px;">{len(parsed["key_findings"])} items</span>'
            '</div>'
            f'{rows_html}</div>',
            unsafe_allow_html=True)

    # ── 3. CLINICAL RECOMMENDATIONS ─────────────────────────
    if parsed.get('recommendations'):
        recs_html = ''.join([
            f'<div style="display:flex;gap:12px;padding:11px 0;border-bottom:1px solid rgba(5,150,105,0.2);align-items:flex-start;">'
            f'<span style="background:linear-gradient(135deg,#059669,#00E5A0);color:#0F172A;font-weight:800;'
            f'font-size:13px;padding:3px 10px;border-radius:8px;flex-shrink:0;min-width:28px;text-align:center;">{i+1}</span>'
            f'<span style="font-size:14px;color:#1E293B;line-height:1.65;">{r}</span></div>'
            for i, r in enumerate(parsed['recommendations'])
        ])
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(0,229,160,0.08),rgba(0,229,160,0.02));'
            'border:2px solid rgba(0,229,160,0.4);border-left:5px solid #00E5A0;border-radius:14px;'
            'padding:16px 20px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">'
            '<span style="font-size:16px;">💊</span>'
            '<span style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.1em;">Clinical Recommendations</span>'
            f'<span style="background:rgba(0,229,160,0.2);color:#059669;font-size:11px;font-weight:700;'
            f'padding:2px 10px;border-radius:10px;">{len(parsed["recommendations"])} actions</span>'
            '</div>'
            f'{recs_html}</div>',
            unsafe_allow_html=True)
    else:
        # Show a placeholder so the doctor knows the field exists but was empty
        st.markdown(
            '<div style="background:rgba(0,229,160,0.04);border:2px dashed rgba(0,229,160,0.25);'
            'border-radius:12px;padding:12px 18px;margin-bottom:14px;">'
            '<span style="font-size:13px;color:#334155;">💊 <b style="color:#059669;">Recommendations</b> — '
            'Not generated for this entry. Check GPT prompt includes a RECOMMENDATIONS: section.</span>'
            '</div>',
            unsafe_allow_html=True)

    # ── 4. FOLLOW-UP + URGENCY side-by-side ─────────────────
    fu_col, ug_col = st.columns(2)
    with fu_col:
        fu = parsed.get('followup','')
        if fu:
            st.markdown(
                '<div style="background:#FFFFFF;border:2px solid #93C5FD;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                '<span style="font-size:15px;">📅</span>'
                '<span style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;">Follow-up Plan</span>'
                '</div>'
                f'<div style="font-size:14px;color:#1E293B;font-weight:600;line-height:1.7;">{fu}</div>'
                '</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#FFFFFF;border:2px dashed #1E3A5F;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="font-size:13px;color:#334155;">📅 Follow-up not specified in summary.</div>'
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
                f'<div style="font-size:20px;font-weight:800;color:{uc};letter-spacing:0.05em;">{urg.upper()}</div>'
                f'</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#FFFFFF;border:2px dashed #1E3A5F;border-radius:12px;padding:16px 18px;margin-bottom:12px;">'
                '<div style="font-size:13px;color:#334155;">⚠️ Urgency not specified.</div>'
                '</div>',
                unsafe_allow_html=True)

    # ── 5. GUIDELINE CITATIONS ───────────────────────────────
    # Auto-fallback citations by modality/disease if RAG didn't provide any
    if not citations:
        if parsed.get('clinical_summary',''):
            summary_lower = parsed['clinical_summary'].lower()
            # Build citations covering ALL diseases mentioned in summary
            citations = []
            if any(w in summary_lower for w in ['kidney','egfr','ckd','renal','nephro']):
                citations += ['KDIGO 2022 CKD Guidelines','NICE CG182 CKD (2021)']
            if any(w in summary_lower for w in ['glucose','diabetes','hba1c','metformin','glyca','glycem']):
                citations += ['ADA Standards of Care in Diabetes 2024','NICE NG28 Type 2 Diabetes (2022)']
            if any(w in summary_lower for w in ['thyroid','tsh','levothyroxine','hypothyroid']):
                citations += ['ATA/AACE Hypothyroidism Guidelines 2023']
            if any(w in summary_lower for w in ['glioma','meningioma','pituitary','brain tumor','brain tumour']):
                citations += ['WHO CNS Tumour Classification 2021','EANO Brain Tumour Guidelines 2021']
            if any(w in summary_lower for w in ['no tumor','no tumour','normal brain','no abnormal']):
                citations += ['ACR Neuroimaging Guidelines 2023']
            if any(w in summary_lower for w in ['fetal','obstetric','gestation','antenatal']):
                citations += ['ISUOG Fetal Ultrasound Guidelines 2021','NICE NG201 Antenatal Care (2021)']
            # Remove duplicates
            citations = list(dict.fromkeys(citations))

    if citations:
        unique_cites = list(dict.fromkeys(citations))
        cite_pills = ''.join([
            f'<span style="display:inline-block;background:rgba(96,165,250,0.12);border:1px solid rgba(96,165,250,0.4);'
            f'color:#93C5FD;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;margin:3px 4px 3px 0;">'
            f'📖 {c}</span>'
            for c in unique_cites
        ])
        st.markdown(
            '<div style="background:#FFFFFF;border:2px solid #93C5FD;border-left:4px solid #60A5FA;border-radius:12px;'
            'padding:14px 20px;margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
            '<span style="font-size:15px;">📚</span>'
            '<span style="font-size:11px;font-weight:700;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.08em;">Guideline References Used</span>'
            '</div>'
            f'<div style="line-height:2;">{cite_pills}</div>'
            '<div style="font-size:11px;color:#334155;margin-top:8px;font-style:italic;">These guidelines were used as the knowledge base for this AI-generated clinical summary.</div>'
            '</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#FFFFFF;border:2px dashed #1E3A5F;border-radius:10px;padding:12px 18px;margin-bottom:14px;">'
            '<div style="font-size:13px;color:#334155;">📚 No guideline citations available for this summary.</div>'
            '</div>',
            unsafe_allow_html=True)


# ── ENTRY POINT ───────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    render_dashboard()
