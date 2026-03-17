"""
MedAI — Doctor-in-the-Loop Clinical System
"""
import streamlit as st

st.set_page_config(
    page_title="MedAI Clinical System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#0B1120;color:#E2E8F0;}
.stApp{background:#0B1120;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
.stTextInput>div>div>input{background:#1A2335!important;color:#F1F5F9!important;border:1px solid #2D3748!important;border-radius:8px!important;font-size:15px!important;}
.stTextArea textarea{background:#1A2335!important;color:#F1F5F9!important;border:1px solid #2D3748!important;border-radius:8px!important;font-size:14px!important;}
.stSelectbox>div>div{background:#1A2335!important;color:#F1F5F9!important;}
.stButton>button{font-family:'Inter',sans-serif!important;font-weight:500!important;font-size:14px!important;border-radius:8px!important;padding:10px 20px!important;transition:all 0.2s!important;}
.stButton>button[kind="primary"]{background:#3B82F6!important;border:none!important;color:white!important;}
.stButton>button[kind="secondary"]{background:#1A2335!important;border:1px solid #2D3748!important;color:#E2E8F0!important;}
.stTabs [data-baseweb="tab-list"]{background:#111827;border-bottom:1px solid #1E2D40;padding:0 8px;gap:0;}
.stTabs [data-baseweb="tab"]{font-size:14px;font-weight:500;color:#64748B;padding:14px 20px;}
.stTabs [aria-selected="true"]{color:#3B82F6!important;border-bottom:2px solid #3B82F6!important;background:transparent!important;}
.stExpander{border:1px solid #1E2D40!important;border-radius:10px!important;background:#111827!important;}
.stFileUploader{border-radius:8px!important;}
hr{border-color:#1E2D40!important;margin:0!important;}
div[data-testid="stFileUploadDropzone"]{background:#1A2335!important;border:1px dashed #2D3748!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
from utils import DOCTORS
for k, v in {
    'page':            'home',
    'patients':        {},   # pid → patient record
    'reports':         {},   # pid → generated report
    'current_patient': None,
    'patient_lookup':  None,
    'doctors':         DOCTORS,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Top bar ───────────────────────────────────────────────────
pending = sum(1 for p in st.session_state.patients.values()
              if p.get('status') == 'PENDING')
urgent  = sum(1 for p in st.session_state.patients.values()
              if p.get('fusion_label','') == 'Severe'
              and p.get('status') == 'PENDING')

badges = ''
if urgent > 0:
    badges += (f'<span style="background:#EF4444;color:white;font-size:12px;'
               f'font-weight:600;padding:4px 12px;border-radius:20px;'
               f'margin-right:8px;">⚠ {urgent} Urgent</span>')
if pending > 0:
    badges += (f'<span style="background:#F59E0B;color:#0B1120;font-size:12px;'
               f'font-weight:600;padding:4px 12px;border-radius:20px;'
               f'margin-right:8px;">{pending} Pending</span>')
badges += ('<span style="background:rgba(16,185,129,0.15);'
           'border:1px solid rgba(16,185,129,0.3);color:#10B981;'
           'font-size:12px;font-weight:500;padding:4px 12px;'
           'border-radius:20px;font-family:monospace;">● Online</span>')

st.markdown(
    '<div style="background:#111827;border-bottom:1px solid #1E2D40;'
    'padding:12px 28px;display:flex;align-items:center;'
    'justify-content:space-between;">'
    '<div style="display:flex;align-items:center;gap:10px;">'
    '<div style="background:#3B82F6;width:34px;height:34px;border-radius:8px;'
    'display:flex;align-items:center;justify-content:center;font-size:18px;">🏥</div>'
    '<div><div style="font-size:16px;font-weight:700;color:#F1F5F9;">MedAI</div>'
    '<div style="font-size:10px;color:#475569;font-family:monospace;'
    'letter-spacing:0.05em;">CLINICAL SYSTEM v1.0</div></div></div>'
    f'<div style="display:flex;align-items:center;gap:8px;">{badges}</div>'
    '</div>',
    unsafe_allow_html=True
)

# Navigation
nav_pages = [
    ('home',    '🏠  Home'),
    ('patient', '👤  Patient Portal'),
    ('doctor',  '🩺  Doctor Dashboard'),
    ('result',  '📋  My Report'),
]
nav_cols = st.columns(len(nav_pages))
for col, (pid, label) in zip(nav_cols, nav_pages):
    with col:
        if st.button(label, key=f'nav_{pid}',
                     use_container_width=True,
                     type='primary' if st.session_state.page == pid
                     else 'secondary'):
            st.session_state.page = pid
            st.rerun()

# ── Page content ──────────────────────────────────────────────
st.markdown('<div style="padding:24px 28px;">', unsafe_allow_html=True)

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
