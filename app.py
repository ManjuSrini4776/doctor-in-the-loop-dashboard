"""
MedAI — Doctor-in-the-Loop Hospital System
Professional Clinical Dashboard
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0B1120;
    color: #E2E8F0;
}
.stApp { background-color: #0B1120; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Hide streamlit default padding */
[data-testid="stAppViewContainer"] { padding: 0; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0B1120; }
::-webkit-scrollbar-thumb { background: #2D3748; border-radius: 3px; }

/* Inputs */
input, textarea, select {
    background: #1A2335 !important;
    color: #E2E8F0 !important;
    border: 1px solid #2D3748 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input {
    background: #1A2335 !important;
    color: #E2E8F0 !important;
    font-size: 15px !important;
}
.stSelectbox > div > div {
    background: #1A2335 !important;
    color: #E2E8F0 !important;
}
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: #3B82F6 !important;
    border: none !important;
    color: white !important;
}
.stButton > button[kind="secondary"] {
    background: #1A2335 !important;
    border: 1px solid #2D3748 !important;
    color: #E2E8F0 !important;
}
hr { border-color: #1E2D40 !important; margin: 0 !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #111827;
    gap: 0;
    border-bottom: 1px solid #1E2D40;
    padding: 0 24px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 500;
    color: #64748B;
    padding: 14px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}
.stTabs [aria-selected="true"] {
    color: #3B82F6 !important;
    border-bottom-color: #3B82F6 !important;
    background: transparent !important;
}
.stFileUploader { background: #1A2335 !important; border-radius: 8px !important; }
.stExpander { border: 1px solid #1E2D40 !important; border-radius: 8px !important; }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
defaults = {
    'page':             'home',
    'patients':         {},
    'reports':          {},
    'current_patient':  None,
    'patient_lookup':   None,
    'doctors': {
        'DR001': {'name':'Dr. Priya Sharma',  'dept':'Internal Medicine',  'specialty':'Nephrology & Chronic Disease'},
        'DR002': {'name':'Dr. Arjun Mehta',   'dept':'Neurology',          'specialty':'Neuro-Oncology'},
        'DR003': {'name':'Dr. Kavitha Rajan', 'dept':'Obstetrics',         'specialty':'Fetal Medicine'},
        'DR004': {'name':'Dr. Suresh Kumar',  'dept':'General Medicine',   'specialty':'Multimodal Assessment'},
    }
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Top Navigation Bar ────────────────────────────────────────
def top_navbar():
    pending = sum(1 for p in st.session_state.patients.values()
                  if p.get('status') == 'PENDING')
    urgent  = sum(1 for p in st.session_state.patients.values()
                  if p.get('fusion_label') == 'Severe' and
                  p.get('status') == 'PENDING')

    st.markdown(f"""
    <div style="background:#111827;border-bottom:1px solid #1E2D40;
                padding:0 32px;display:flex;align-items:center;
                justify-content:space-between;height:60px;
                position:sticky;top:0;z-index:100;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="background:#3B82F6;width:32px;height:32px;
                        border-radius:8px;display:flex;align-items:center;
                        justify-content:center;font-size:16px;">🏥</div>
            <div>
                <div style="font-size:15px;font-weight:700;color:#F1F5F9;
                            letter-spacing:-0.3px;">MedAI</div>
                <div style="font-size:10px;color:#475569;
                            font-family:'JetBrains Mono',monospace;
                            letter-spacing:0.05em;">CLINICAL SYSTEM v1.0</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            {'<div style="background:#EF4444;color:white;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;margin-right:8px;">⚠ ' + str(urgent) + ' URGENT</div>' if urgent > 0 else ''}
            {'<div style="background:#F59E0B;color:#1A1A1A;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;margin-right:8px;">' + str(pending) + ' Pending</div>' if pending > 0 else ''}
            <div style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);
                        color:#10B981;font-size:11px;font-weight:500;
                        padding:3px 10px;border-radius:20px;
                        font-family:'JetBrains Mono',monospace;">● ONLINE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation tabs
    pages = [
        ('home',    '🏠', 'Home'),
        ('patient', '👤', 'Patient Registration'),
        ('doctor',  '🩺', 'Doctor Dashboard'),
        ('result',  '📋', 'My Report'),
    ]
    nav_cols = st.columns(len(pages))
    for col, (pid, icon, label) in zip(nav_cols, pages):
        with col:
            is_active = st.session_state.page == pid
            if st.button(
                f"{icon}  {label}",
                key=f'nav_{pid}',
                use_container_width=True,
                type='primary' if is_active else 'secondary'
            ):
                st.session_state.page = pid
                st.rerun()

# ── Render ────────────────────────────────────────────────────
top_navbar()
st.markdown('<div style="padding:24px 32px;">', unsafe_allow_html=True)

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
