"""
Doctor-in-the-Loop Hospital AI System
Multi-page Hospital Report Automation
"""
import streamlit as st

st.set_page_config(
    page_title="MedAI Hospital System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Shared CSS (loaded once) ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&family=Playfair+Display:wght@600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #060A10;
    color: #C8D0E0;
}
.stApp { background-color: #060A10; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #080C14 !important;
    border-right: 1px solid #1E293B !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8 !important;
    font-size: 13px !important;
}

/* Nav pills in sidebar */
.nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 8px;
    margin-bottom: 4px; cursor: pointer;
    border: 1px solid transparent;
    font-size: 13px; color: #64748B;
    transition: all 0.15s;
}
.nav-item:hover { background: #111827; color: #F0F4FF; border-color: #1E293B; }
.nav-item.active { background: #111827; color: #3B82F6; border-color: #1E293B; }
.nav-icon { font-size: 16px; }

/* Buttons */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all 0.15s !important;
}

/* Cards */
.card {
    background: #0D1621; border: 1px solid #1E293B;
    border-radius: 12px; padding: 20px 24px;
}
.card-sm {
    background: #0D1621; border: 1px solid #1E293B;
    border-radius: 8px; padding: 14px 18px;
}

/* Severity badges */
.sev { display:inline-block; padding:3px 12px; border-radius:20px;
       font-size:12px; font-weight:500;
       font-family:'IBM Plex Mono',monospace; }
.sev-Normal   { background:rgba(16,185,129,.15); color:#10B981; border:1px solid rgba(16,185,129,.3); }
.sev-Mild     { background:rgba(245,158,11,.15);  color:#F59E0B; border:1px solid rgba(245,158,11,.3); }
.sev-Moderate { background:rgba(249,115,22,.15);  color:#F97316; border:1px solid rgba(249,115,22,.3); }
.sev-Severe   { background:rgba(239,68,68,.15);   color:#EF4444; border:1px solid rgba(239,68,68,.3); }
.sev-Unknown  { background:rgba(71,85,105,.15);   color:#94A3B8; border:1px solid rgba(71,85,105,.3); }
.sev-Pending  { background:rgba(59,130,246,.15);  color:#3B82F6; border:1px solid rgba(59,130,246,.3); }

hr { border-color: #1E293B !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────
defaults = {
    'page':           'home',
    'patients':       {},      # patient_id → patient record
    'reviews':        {},      # patient_id → doctor review
    'reports':        {},      # patient_id → generated AI report
    'current_patient': None,   # viewing patient (doctor side)
    'patient_lookup':  None,   # patient checking own result
    'doctors': {
        'DR001': {'name': 'Dr. Priya Sharma',    'dept': 'Internal Medicine',   'specialty': 'Nephrology'},
        'DR002': {'name': 'Dr. Arjun Mehta',     'dept': 'Neurology',           'specialty': 'Brain Tumor'},
        'DR003': {'name': 'Dr. Kavitha Rajan',   'dept': 'Obstetrics & Gynecology', 'specialty': 'Fetal Medicine'},
        'DR004': {'name': 'Dr. Suresh Kumar',    'dept': 'General Medicine',    'specialty': 'Chronic Disease'},
    }
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar navigation ────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 4px 12px;">
        <div style="font-family:'Playfair Display',serif;
                    font-size:20px;color:#F0F4FF;letter-spacing:-.3px;">
            🏥 MedAI
        </div>
        <div style="font-size:11px;color:#334155;margin-top:2px;
                    font-family:'IBM Plex Mono',monospace;">
            Hospital Report System
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    pages = [
        ('home',    '🏠', 'Home'),
        ('patient', '👤', 'Patient Portal'),
        ('doctor',  '🩺', 'Doctor Dashboard'),
        ('result',  '📋', 'My Report'),
    ]

    for page_id, icon, label in pages:
        active = 'active' if st.session_state.page == page_id else ''
        if st.button(f'{icon}  {label}',
                     key=f'nav_{page_id}',
                     use_container_width=True):
            st.session_state.page = page_id
            st.rerun()

    st.markdown('<hr>', unsafe_allow_html=True)

    # Live queue counter
    total_p   = len(st.session_state.patients)
    pending_p = len([p for p in st.session_state.patients.values()
                     if p.get('status') == 'PENDING'])
    approved_p = len([p for p in st.session_state.patients.values()
                      if p.get('status') == 'APPROVED'])

    st.markdown(f"""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;">
        <div style="color:#64748B;margin-bottom:6px;">── LIVE QUEUE</div>
        <div style="display:flex;justify-content:space-between;
                    margin-bottom:4px;">
            <span style="color:#94A3B8;">Total</span>
            <span style="color:#F0F4FF;font-weight:500;">{total_p}</span>
        </div>
        <div style="display:flex;justify-content:space-between;
                    margin-bottom:4px;">
            <span style="color:#94A3B8;">Pending</span>
            <span style="color:#F59E0B;font-weight:500;">{pending_p}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="color:#94A3B8;">Approved</span>
            <span style="color:#10B981;font-weight:500;">{approved_p}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────
page = st.session_state.page

if page == 'home':
    from pages.home import render
    render()
elif page == 'patient':
    from pages.patient_portal import render
    render()
elif page == 'doctor':
    from pages.doctor_dashboard import render
    render()
elif page == 'result':
    from pages.patient_result import render
    render()
