import streamlit as st

st.set_page_config(
    page_title="MedAI Clinical System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Epic EMR Style CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #0D1B2E !important;
    color: #E8EDF5 !important;
}
.stApp { background: #0D1B2E !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Inputs */
.stTextInput > div > div > input {
    background: #162236 !important;
    color: #E8EDF5 !important;
    border: 1.5px solid #263A55 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 14px !important;
}
.stTextArea textarea {
    background: #162236 !important;
    color: #E8EDF5 !important;
    border: 1.5px solid #263A55 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
}
.stSelectbox > div > div {
    background: #162236 !important;
    color: #E8EDF5 !important;
    border: 1.5px solid #263A55 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
}
.stNumberInput > div > div > input {
    background: #162236 !important;
    color: #E8EDF5 !important;
    border: 1.5px solid #263A55 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
}
label { color: #94A3B8 !important; font-size: 14px !important; font-weight: 500 !important; }

/* Buttons */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    padding: 11px 22px !important;
    transition: all 0.2s ease !important;
    letter-spacing: -0.1px !important;
}
.stButton > button[kind="primary"] {
    background: #2563EB !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.45) !important;
}
.stButton > button[kind="secondary"] {
    background: #162236 !important;
    border: 1.5px solid #263A55 !important;
    color: #94A3B8 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #4A9EFF !important;
    color: #E8EDF5 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #112033 !important;
    border-bottom: 2px solid #1E3250 !important;
    padding: 0 4px !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 14px 24px !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: #4A9EFF !important;
    border-bottom-color: #4A9EFF !important;
    background: transparent !important;
    font-weight: 600 !important;
}

/* File uploader */
div[data-testid="stFileUploadDropzone"] {
    background: #162236 !important;
    border: 2px dashed #263A55 !important;
    border-radius: 10px !important;
}

/* Expander */
.stExpander {
    background: #112033 !important;
    border: 1px solid #1E3250 !important;
    border-radius: 10px !important;
}

/* Success / Error / Info */
.stSuccess { background: rgba(0,196,140,0.1) !important; border-color: rgba(0,196,140,0.3) !important; }
.stError   { background: rgba(255,59,59,0.1) !important; border-color: rgba(255,59,59,0.3) !important; }
.stInfo    { background: rgba(74,158,255,0.1) !important; border-color: rgba(74,158,255,0.3) !important; }

hr { border-color: #1E3250 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
from utils import DOCTORS
for k, v in {
    'page':            'home',
    'patients':        {},
    'reports':         {},
    'current_patient': None,
    'patient_lookup':  None,
    'selected_doc':    None,
    'doctors':         DOCTORS,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Top Bar ───────────────────────────────────────────────────
pending = sum(1 for p in st.session_state.patients.values()
              if p.get('status') == 'PENDING')
urgent  = sum(1 for p in st.session_state.patients.values()
              if p.get('fusion_label','') == 'Severe'
              and p.get('status') == 'PENDING')

badges = ''
if urgent > 0:
    badges += ('<span style="background:#FF3B3B;color:white;font-size:13px;'
               'font-weight:700;padding:5px 14px;border-radius:20px;'
               'margin-right:10px;">🚨 ' + str(urgent) + ' Urgent</span>')
if pending > 0:
    badges += ('<span style="background:#FFB800;color:#0D1B2E;font-size:13px;'
               'font-weight:700;padding:5px 14px;border-radius:20px;'
               'margin-right:10px;">' + str(pending) + ' Pending</span>')
badges += ('<span style="background:rgba(0,196,140,0.15);'
           'border:1.5px solid rgba(0,196,140,0.4);color:#00C48C;'
           'font-size:13px;font-weight:600;padding:5px 14px;'
           'border-radius:20px;">● System Online</span>')

st.markdown(
    '<div style="background:#0A1628;border-bottom:2px solid #1E3250;'
    'padding:0 32px;height:64px;display:flex;align-items:center;'
    'justify-content:space-between;">'
    '<div style="display:flex;align-items:center;gap:12px;">'
    '<div style="background:#2563EB;width:38px;height:38px;border-radius:10px;'
    'display:flex;align-items:center;justify-content:center;'
    'font-size:20px;box-shadow:0 2px 8px rgba(37,99,235,0.4);">🏥</div>'
    '<div>'
    '<div style="font-size:18px;font-weight:800;color:#F0F6FF;'
    'letter-spacing:-0.5px;">MedAI</div>'
    '<div style="font-size:11px;color:#4A6080;font-weight:500;'
    'letter-spacing:0.08em;text-transform:uppercase;">Clinical System</div>'
    '</div></div>'
    '<div style="display:flex;align-items:center;gap:10px;">' + badges + '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Navigation ────────────────────────────────────────────────
nav_items = [
    ('home',    '🏠', 'Home'),
    ('patient', '👤', 'Patient Portal'),
    ('doctor',  '🩺', 'Doctor Dashboard'),
    ('result',  '📋', 'My Report'),
]
nav_cols = st.columns(len(nav_items))
for col, (pid, icon, label) in zip(nav_cols, nav_items):
    with col:
        active = st.session_state.page == pid
        if st.button(
            icon + '  ' + label,
            key='nav_' + pid,
            use_container_width=True,
            type='primary' if active else 'secondary'
        ):
            st.session_state.page = pid
            st.rerun()

# ── Page ──────────────────────────────────────────────────────
st.markdown('<div style="padding:28px 32px 40px;">', unsafe_allow_html=True)

page = st.session_state.page
if page == 'home':
    from home import render
elif page == 'patient':
    from patient_portal import render
elif page == 'doctor':
    from doctor_dashboard import render
elif page == 'result':
    from patient_result import render

render()
st.markdown('</div>', unsafe_allow_html=True)
