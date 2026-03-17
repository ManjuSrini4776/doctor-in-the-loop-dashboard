"""
Doctor-in-the-Loop Medical AI Dashboard
Multimodal Clinical Decision Support System
Lab Report + CT Tumor + Fetal Ultrasound
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime
from PIL import Image
import io
import base64

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Doctor-in-the-Loop AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&family=Playfair+Display:wght@600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #080C14;
    color: #C8D0E0;
}
.stApp { background-color: #080C14; }

/* ── Hide streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* ── Top header bar ── */
.top-header {
    background: linear-gradient(135deg, #0D1621 0%, #111827 100%);
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-title {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    color: #F0F4FF;
    margin: 0;
}
.header-subtitle {
    font-size: 12px;
    color: #64748B;
    margin-top: 4px;
    font-family: 'IBM Plex Mono', monospace;
}
.header-badge {
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.3);
    color: #10B981;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Metric cards ── */
.metric-card {
    background: #0D1621;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 16px 20px;
    height: 100%;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    border-radius: 10px 0 0 10px;
}
.card-normal::before   { background: #10B981; }
.card-mild::before     { background: #F59E0B; }
.card-moderate::before { background: #F97316; }
.card-severe::before   { background: #EF4444; }
.card-unknown::before  { background: #475569; }
.card-info::before     { background: #3B82F6; }

.metric-label {
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 28px;
    font-weight: 600;
    color: #F0F4FF;
    line-height: 1;
}
.metric-sub {
    font-size: 12px;
    color: #94A3B8;
    margin-top: 4px;
}

/* ── Severity badge ── */
.sev-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'IBM Plex Mono', monospace;
}
.sev-Normal   { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.sev-Mild     { background:rgba(245,158,11,0.15);  color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.sev-Moderate { background:rgba(249,115,22,0.15);  color:#F97316; border:1px solid rgba(249,115,22,0.3); }
.sev-Severe   { background:rgba(239,68,68,0.15);   color:#EF4444; border:1px solid rgba(239,68,68,0.3); }
.sev-Unknown  { background:rgba(71,85,105,0.15);   color:#94A3B8; border:1px solid rgba(71,85,105,0.3); }

/* ── Section headers ── */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #3B82F6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 8px 0;
    border-bottom: 1px solid #1E293B;
    margin-bottom: 16px;
}

/* ── Patient row ── */
.patient-row {
    background: #0D1621;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.patient-row:hover { border-color: #3B82F6; background: #111827; }

/* ── Report box ── */
.report-box {
    background: #0D1621;
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 20px 24px;
    font-size: 14px;
    line-height: 1.8;
    color: #C8D0E0;
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
}

/* ── Action buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 20px !important;
    border: 1px solid !important;
    transition: all 0.15s !important;
}

/* ── Sidebar ── */
.css-1d391kg, [data-testid="stSidebar"] {
    background: #0A0F1A !important;
    border-right: 1px solid #1E293B !important;
}

/* ── Divider ── */
hr { border-color: #1E293B !important; }

/* ── Progress bar ── */
.stProgress > div > div { background-color: #3B82F6 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0D1621;
    border-radius: 8px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    color: #64748B;
    border-radius: 6px;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #1E293B !important;
    color: #F0F4FF !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────
SEV_COLORS = {
    'Normal':   '#10B981',
    'Mild':     '#F59E0B',
    'Moderate': '#F97316',
    'Severe':   '#EF4444',
    'Unknown':  '#94A3B8'
}

SCORE_TO_LABEL = {0: 'Normal', 1: 'Mild', 2: 'Moderate', 3: 'Severe'}

CT_CLASS_DESC = {
    'notumor':    'No tumor detected',
    'pituitary':  'Pituitary adenoma',
    'meningioma': 'Meningioma',
    'glioma':     'Glioma (high-grade)'
}

US_CLASS_DESC = {
    'Fetal abdomen': 'Normal fetal abdominal plane',
    'Fetal brain':   'Fetal brain — neurological assessment',
    'Fetal femur':   'Fetal femur — growth assessment',
    'Fetal thorax':  'Fetal thorax — cardiac/lung assessment'
}


def sev_badge(label: str) -> str:
    return f'<span class="sev-badge sev-{label}">{label}</span>'


def metric_card(label: str, value: str, sub: str = '',
                card_class: str = 'card-info') -> str:
    return f"""
    <div class="metric-card {card_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {'<div class="metric-sub">' + sub + '</div>' if sub else ''}
    </div>"""


def score_to_card_class(score) -> str:
    if pd.isna(score): return 'card-unknown'
    s = int(score)
    return {0: 'card-normal', 1: 'card-mild',
            2: 'card-moderate', 3: 'card-severe'}.get(s, 'card-unknown')


def load_sample_data():
    """Generate realistic sample data for demo."""
    np.random.seed(42)
    n = 50

    ct_classes = ['notumor', 'pituitary', 'meningioma', 'glioma']
    us_classes  = ['Fetal abdomen', 'Fetal brain', 'Fetal femur', 'Fetal thorax']
    ct_sev_map  = {'notumor': 0, 'pituitary': 1, 'meningioma': 2, 'glioma': 3}
    us_sev_map  = {'Fetal abdomen': 0, 'Fetal femur': 1,
                   'Fetal thorax': 2, 'Fetal brain': 3}

    records = []
    for i in range(n):
        ct_cls  = np.random.choice(ct_classes, p=[0.4, 0.2, 0.25, 0.15])
        us_cls  = np.random.choice(us_classes)
        lab_s   = np.random.choice([0,1,2,3], p=[0.35,0.30,0.20,0.15])
        ct_s    = ct_sev_map[ct_cls]
        us_s    = us_sev_map[us_cls]
        fus_s   = max(lab_s, ct_s, us_s)

        records.append({
            'case_id':           f'PT-{1000+i:04d}',
            'lab_score':         lab_s,
            'lab_severity_label':SCORE_TO_LABEL[lab_s],
            'ct_score':          ct_s,
            'ct_predicted_class':ct_cls,
            'ct_confidence':     round(np.random.uniform(0.75, 0.99), 3),
            'ct_severity_label': SCORE_TO_LABEL[ct_s],
            'us_score':          us_s,
            'us_predicted_class':us_cls,
            'us_confidence':     round(np.random.uniform(0.80, 0.99), 3),
            'us_severity_label': SCORE_TO_LABEL[us_s],
            'fusion_score':      fus_s,
            'fusion_label':      SCORE_TO_LABEL[fus_s],
            'modalities_available': 3,
            'review_status':     'PENDING'
        })

    return pd.DataFrame(records)


@st.cache_data
def get_openai_client():
    try:
        from openai import OpenAI
        api_key = st.secrets.get('OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY',''))
        if api_key:
            return OpenAI(api_key=api_key)
    except Exception:
        pass
    return None


@st.cache_resource
def load_rag_retriever():
    """Load FAISS baseline RAG if available."""
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size': 32}
        )
        db_path = 'rag_output/baseline_vector_db'
        if os.path.exists(db_path):
            db = FAISS.load_local(db_path, emb,
                                  allow_dangerous_deserialization=True)
            return db
    except Exception:
        pass
    return None


def generate_report_rag(patient: dict, rag_db=None,
                        openai_client=None) -> str:
    """Generate clinical report using RAG + GPT-4o-mini."""
    sev_text = {0: 'Normal', 1: 'Mild', 2: 'Moderate', 3: 'Severe'}

    query_parts = []
    if pd.notna(patient.get('lab_score')):
        query_parts.append(
            f"Lab findings indicate {sev_text.get(int(patient['lab_score']),'unknown')} "
            f"chronic disease severity."
        )
    if pd.notna(patient.get('ct_score')):
        cls = patient.get('ct_predicted_class', 'brain tumor')
        query_parts.append(
            f"CT imaging: {CT_CLASS_DESC.get(cls, cls)} with "
            f"{sev_text.get(int(patient['ct_score']),'unknown')} severity "
            f"(confidence: {patient.get('ct_confidence',0):.1%})."
        )
    if pd.notna(patient.get('us_score')):
        cls = patient.get('us_predicted_class', 'fetal plane')
        query_parts.append(
            f"Ultrasound: {US_CLASS_DESC.get(cls, cls)} — "
            f"{sev_text.get(int(patient['us_score']),'unknown')} risk level "
            f"(confidence: {patient.get('us_confidence',0):.1%})."
        )
    query_parts.append(
        f"Overall multimodal fusion severity: {patient.get('fusion_label','Unknown')}."
    )
    query = ' '.join(query_parts)

    # RAG context
    context = ''
    if rag_db:
        try:
            docs    = rag_db.similarity_search(query, k=4)
            context = '\n\n'.join([d.page_content for d in docs])
        except Exception:
            context = ''

    if not openai_client:
        return (
            f"Clinical Interpretation: Patient shows "
            f"{patient.get('fusion_label','Unknown')} overall severity based on "
            f"multimodal assessment. "
            f"{'CT indicates ' + CT_CLASS_DESC.get(patient.get('ct_predicted_class',''), '') + '.' if pd.notna(patient.get('ct_score')) else ''} "
            f"{'Ultrasound shows ' + US_CLASS_DESC.get(patient.get('us_predicted_class',''), '') + '.' if pd.notna(patient.get('us_score')) else ''}\n\n"
            f"Recommended Actions: Schedule follow-up based on severity level. "
            f"Review all modality findings before finalising treatment plan.\n\n"
            f"Urgency: {'High' if patient.get('fusion_label') == 'Severe' else 'Medium' if patient.get('fusion_label') == 'Moderate' else 'Low'}\n\n"
            f"⚠️ Note: AI-generated draft — requires doctor review and validation."
        )

    prompt = f"""You are a clinical decision support assistant in a Doctor-in-the-Loop AI system.

Patient Assessment:
{query}

{"Relevant Clinical Guideline Evidence:" + chr(10) + context if context else ""}

Task: Write a concise clinical dashboard summary for the reviewing doctor.

Rules:
- Ground every statement in evidence (if provided)
- Do not hallucinate clinical facts
- Maximum 4 sentences
- Flag if severity is Moderate or Severe

Format:
Clinical Interpretation: <interpretation>
Recommended Actions: <specific actionable steps>
Urgency: <Low / Medium / High>

End with:
⚠️ AI-generated draft — requires doctor review and validation."""

    try:
        response = openai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Report generation failed: {e}\n\n⚠️ Please check your OpenAI API key."


# ── Session state ──────────────────────────────────────────────
if 'df' not in st.session_state:
    st.session_state.df = None
if 'reviews' not in st.session_state:
    st.session_state.reviews = {}
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'generated_reports' not in st.session_state:
    st.session_state.generated_reports = {}


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 8px;">
        <div style="font-family:'Playfair Display',serif;font-size:18px;color:#F0F4FF;">
            🏥 Medical AI
        </div>
        <div style="font-size:11px;color:#475569;margin-top:2px;
                    font-family:'IBM Plex Mono',monospace;">
            Doctor-in-the-Loop System
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    st.markdown("**📂 Data Source**")
    data_source = st.radio(
        '', ['Use Sample Data', 'Upload My Data'],
        label_visibility='collapsed'
    )

    if data_source == 'Upload My Data':
        st.markdown("**Fusion Output**")
        fusion_file = st.file_uploader(
            'FINAL_MULTIMODAL_FUSION.parquet',
            type=['parquet', 'csv'],
            key='fusion_upload'
        )
        if fusion_file:
            if fusion_file.name.endswith('.parquet'):
                st.session_state.df = pd.read_parquet(fusion_file)
            else:
                st.session_state.df = pd.read_csv(fusion_file)
            st.success(f'{len(st.session_state.df):,} patients loaded')
    else:
        if st.button('Load Sample Data', use_container_width=True):
            st.session_state.df = load_sample_data()
            st.success('50 sample patients loaded')

    st.markdown('<hr>', unsafe_allow_html=True)

    # Severity filter
    st.markdown("**🔍 Filter Patients**")
    sev_filter = st.multiselect(
        'Severity',
        ['Normal', 'Mild', 'Moderate', 'Severe', 'Unknown'],
        default=['Normal', 'Mild', 'Moderate', 'Severe', 'Unknown'],
        label_visibility='collapsed'
    )

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;">
        <div style="margin-bottom:4px;">📊 Lab: MIMIC-IV</div>
        <div style="margin-bottom:4px;">🧠 CT: EfficientNet-B0</div>
        <div style="margin-bottom:4px;">🔬 US: DenseNet121</div>
        <div style="margin-bottom:4px;">🤖 RAG: Baseline V1</div>
        <div style="color:#334155;margin-top:8px;">v1.0 · Final Year Project</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main content ───────────────────────────────────────────────

# Top header
st.markdown("""
<div class="top-header">
    <div>
        <div class="header-title">Doctor-in-the-Loop Clinical AI Dashboard</div>
        <div class="header-subtitle">
            Multimodal Severity Assessment · Lab Report + CT Tumor + Fetal Ultrasound
        </div>
    </div>
    <div class="header-badge">● SYSTEM ACTIVE</div>
</div>
""", unsafe_allow_html=True)

df = st.session_state.df

if df is None:
    # Landing state
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;">
        <div style="font-size:48px;margin-bottom:16px;">🏥</div>
        <div style="font-family:'Playfair Display',serif;font-size:24px;
                    color:#F0F4FF;margin-bottom:8px;">
            Welcome to the Medical AI Dashboard
        </div>
        <div style="font-size:14px;color:#64748B;max-width:500px;margin:0 auto;">
            Load sample data or upload your fusion output from the sidebar
            to begin reviewing patient cases.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    cols = st.columns(4)
    features = [
        ('🧪', 'Lab Severity', 'CKD + Diabetes + Thyroid fusion scoring'),
        ('🧠', 'CT Analysis', 'EfficientNet-B0 tumor classification + GradCAM'),
        ('🔬', 'Ultrasound', 'DenseNet121 fetal plane classification + GradCAM'),
        ('📋', 'AI Reports', 'RAG + GPT-4o-mini clinical report generation'),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class="metric-card card-info" style="text-align:center;padding:20px;">
                <div style="font-size:28px;margin-bottom:8px;">{icon}</div>
                <div style="font-size:13px;font-weight:600;color:#F0F4FF;
                            margin-bottom:4px;">{title}</div>
                <div style="font-size:12px;color:#64748B;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # Apply severity filter
    if 'fusion_label' in df.columns:
        df_filtered = df[df['fusion_label'].isin(sev_filter)].copy()
    else:
        df_filtered = df.copy()

    if 'review_status' not in df_filtered.columns:
        df_filtered['review_status'] = 'PENDING'

    # ── Overview metrics ──────────────────────────────────────
    st.markdown('<div class="section-header">── Overview</div>',
                unsafe_allow_html=True)

    total      = len(df)
    pending    = len([v for v in st.session_state.reviews.values()
                      if v.get('status') == 'PENDING']) or total
    approved   = len([v for v in st.session_state.reviews.values()
                      if v.get('status') == 'APPROVED'])
    rejected   = len([v for v in st.session_state.reviews.values()
                      if v.get('status') == 'REJECTED'])
    severe_n   = len(df[df.get('fusion_label', pd.Series()) == 'Severe']) \
                 if 'fusion_label' in df.columns else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(metric_card('Total Patients', f'{total:,}',
                                'in system', 'card-info'),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card('Pending Review',
                                f'{total - approved - rejected:,}',
                                'awaiting doctor', 'card-mild'),
                    unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card('Approved', f'{approved:,}',
                                'reports signed off', 'card-normal'),
                    unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card('Rejected', f'{rejected:,}',
                                'reports returned', 'card-moderate'),
                    unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card('Severe Cases', f'{severe_n:,}',
                                'requires urgent attention', 'card-severe'),
                    unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Two columns layout ────────────────────────────────────
    left_col, right_col = st.columns([1, 2], gap='large')

    with left_col:
        st.markdown('<div class="section-header">── Patient List</div>',
                    unsafe_allow_html=True)

        # Severity distribution mini chart
        if 'fusion_label' in df.columns:
            sev_counts = df['fusion_label'].value_counts()
            for sev in ['Severe', 'Moderate', 'Mild', 'Normal']:
                cnt = sev_counts.get(sev, 0)
                pct = round(100 * cnt / len(df), 1)
                color = SEV_COLORS.get(sev, '#94A3B8')
                st.markdown(f"""
                <div style="display:flex;align-items:center;
                            gap:8px;margin-bottom:5px;">
                    <div style="width:60px;font-size:11px;color:#64748B;
                                font-family:'IBM Plex Mono',monospace;">{sev}</div>
                    <div style="flex:1;height:6px;background:#1E293B;
                                border-radius:3px;overflow:hidden;">
                        <div style="width:{pct}%;height:100%;
                                    background:{color};border-radius:3px;"></div>
                    </div>
                    <div style="width:36px;font-size:11px;color:#94A3B8;
                                text-align:right;">{cnt}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)

        # Patient list
        display_cols = ['case_id', 'fusion_label', 'modalities_available'] \
            if all(c in df_filtered.columns
                   for c in ['case_id', 'fusion_label', 'modalities_available']) \
            else df_filtered.columns[:3].tolist()

        for _, row in df_filtered.head(30).iterrows():
            case_id = str(row.get('case_id', row.name))
            fus_lbl = row.get('fusion_label', 'Unknown')
            mods    = int(row.get('modalities_available', 1))
            color   = SEV_COLORS.get(fus_lbl, '#94A3B8')
            status  = st.session_state.reviews.get(case_id, {}).get('status', '')
            status_icon = {'APPROVED': '✅', 'REJECTED': '❌',
                           'EDITED': '✏️'}.get(status, '⏳')

            if st.button(
                f"{status_icon}  {case_id}  ·  {fus_lbl}  ·  {mods}🔲",
                key=f'pt_{case_id}',
                use_container_width=True
            ):
                st.session_state.selected_patient = case_id

    with right_col:
        if st.session_state.selected_patient:
            case_id = st.session_state.selected_patient
            mask    = df_filtered['case_id'].astype(str) == case_id \
                      if 'case_id' in df_filtered.columns \
                      else df_filtered.index.astype(str) == case_id

            if mask.any():
                patient = df_filtered[mask].iloc[0].to_dict()

                # Patient header
                fus_lbl = patient.get('fusion_label', 'Unknown')
                st.markdown(f"""
                <div style="display:flex;align-items:center;
                            justify-content:space-between;margin-bottom:16px;">
                    <div>
                        <span style="font-family:'IBM Plex Mono',monospace;
                                     font-size:18px;color:#F0F4FF;
                                     font-weight:500;">
                            {case_id}
                        </span>
                        <span style="margin-left:12px;">
                            {sev_badge(fus_lbl)}
                        </span>
                    </div>
                    <div style="font-size:11px;color:#475569;
                                font-family:'IBM Plex Mono',monospace;">
                        {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    '📊 Severity Scores',
                    '🧠 CT Analysis',
                    '🔬 Ultrasound',
                    '📋 Clinical Report'
                ])

                # ── Tab 1: Severity ──────────────────────────
                with tab1:
                    st.markdown('<div class="section-header">── Modality Scores</div>',
                                unsafe_allow_html=True)

                    c1, c2, c3, c4 = st.columns(4)
                    lab_s  = patient.get('lab_score')
                    ct_s   = patient.get('ct_score')
                    us_s   = patient.get('us_score')
                    fus_s  = patient.get('fusion_score')

                    with c1:
                        lbl = SCORE_TO_LABEL.get(int(lab_s), 'Unknown') \
                              if pd.notna(lab_s) else 'N/A'
                        st.markdown(
                            metric_card('Lab Score',
                                        str(int(lab_s)) if pd.notna(lab_s) else '—',
                                        lbl,
                                        score_to_card_class(lab_s)),
                            unsafe_allow_html=True)
                    with c2:
                        lbl = SCORE_TO_LABEL.get(int(ct_s), 'Unknown') \
                              if pd.notna(ct_s) else 'N/A'
                        st.markdown(
                            metric_card('CT Score',
                                        str(int(ct_s)) if pd.notna(ct_s) else '—',
                                        lbl,
                                        score_to_card_class(ct_s)),
                            unsafe_allow_html=True)
                    with c3:
                        lbl = SCORE_TO_LABEL.get(int(us_s), 'Unknown') \
                              if pd.notna(us_s) else 'N/A'
                        st.markdown(
                            metric_card('US Score',
                                        str(int(us_s)) if pd.notna(us_s) else '—',
                                        lbl,
                                        score_to_card_class(us_s)),
                            unsafe_allow_html=True)
                    with c4:
                        st.markdown(
                            metric_card('Fusion Score',
                                        str(int(fus_s)) if pd.notna(fus_s) else '—',
                                        fus_lbl,
                                        score_to_card_class(fus_s)),
                            unsafe_allow_html=True)

                    st.markdown('<br>', unsafe_allow_html=True)

                    # Score bar chart
                    scores = {}
                    if pd.notna(lab_s):  scores['Lab']        = int(lab_s)
                    if pd.notna(ct_s):   scores['CT']         = int(ct_s)
                    if pd.notna(us_s):   scores['Ultrasound'] = int(us_s)
                    if pd.notna(fus_s):  scores['Fusion']     = int(fus_s)

                    if scores:
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        colors_list = [
                            SEV_COLORS.get(SCORE_TO_LABEL.get(v,'Unknown'),'#94A3B8')
                            for v in scores.values()
                        ]
                        fig.add_trace(go.Bar(
                            x=list(scores.keys()),
                            y=list(scores.values()),
                            marker_color=colors_list,
                            text=[SCORE_TO_LABEL.get(v,'?')
                                  for v in scores.values()],
                            textposition='outside',
                            textfont=dict(color='#C8D0E0', size=11)
                        ))
                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#94A3B8', family='DM Sans'),
                            yaxis=dict(range=[0, 4], tickvals=[0,1,2,3],
                                       ticktext=['Normal','Mild','Moderate','Severe'],
                                       gridcolor='#1E293B'),
                            xaxis=dict(gridcolor='#1E293B'),
                            height=280,
                            margin=dict(t=20, b=20, l=10, r=10),
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # Lab details
                    if any(c in patient for c in
                           ['ckd_severity','diabetes_severity_final',
                            'thyroid_severity_final']):
                        st.markdown('<div class="section-header">'
                                    '── Lab Details</div>',
                                    unsafe_allow_html=True)
                        lc1, lc2, lc3 = st.columns(3)
                        with lc1:
                            v = patient.get('ckd_severity', 'N/A')
                            st.markdown(
                                metric_card('CKD Stage', str(v) if v else 'N/A',
                                            '', 'card-info'),
                                unsafe_allow_html=True)
                        with lc2:
                            v = patient.get('diabetes_severity_final', 'N/A')
                            st.markdown(
                                metric_card('Diabetes', str(v) if v else 'N/A',
                                            '', 'card-info'),
                                unsafe_allow_html=True)
                        with lc3:
                            v = patient.get('thyroid_severity_final', 'N/A')
                            st.markdown(
                                metric_card('Thyroid', str(v) if v else 'N/A',
                                            '', 'card-info'),
                                unsafe_allow_html=True)

                # ── Tab 2: CT ────────────────────────────────
                with tab2:
                    st.markdown('<div class="section-header">'
                                '── CT Tumor Classification</div>',
                                unsafe_allow_html=True)

                    ct_cls  = patient.get('ct_predicted_class', 'N/A')
                    ct_conf = patient.get('ct_confidence', None)
                    ct_sev  = patient.get('ct_severity_label',
                                          SCORE_TO_LABEL.get(
                                              int(ct_s) if pd.notna(ct_s) else -1,
                                              'Unknown'))

                    gc1, gc2 = st.columns(2)
                    with gc1:
                        st.markdown(
                            metric_card('Predicted Class',
                                        ct_cls.title() if ct_cls != 'N/A' else '—',
                                        CT_CLASS_DESC.get(ct_cls, ''),
                                        score_to_card_class(ct_s)),
                            unsafe_allow_html=True)
                    with gc2:
                        conf_str = f'{float(ct_conf):.1%}' \
                                   if ct_conf is not None else '—'
                        st.markdown(
                            metric_card('Confidence', conf_str,
                                        f'Severity: {ct_sev}',
                                        score_to_card_class(ct_s)),
                            unsafe_allow_html=True)

                    # GradCAM
                    st.markdown('<br>', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">'
                                '── Grad-CAM Explainability</div>',
                                unsafe_allow_html=True)

                    gradcam_path = patient.get('gradcam_path', '')
                    if gradcam_path and os.path.exists(str(gradcam_path)):
                        img = Image.open(gradcam_path)
                        st.image(img, caption=f'Grad-CAM — {ct_cls}',
                                 use_column_width=True)
                        st.markdown("""
                        <div style="font-size:11px;color:#64748B;margin-top:4px;
                                    font-family:'IBM Plex Mono',monospace;">
                            Heatmap shows regions the model focused on for
                            classification decision.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="metric-card card-info"
                             style="text-align:center;padding:40px;">
                            <div style="font-size:32px;margin-bottom:8px;">🧠</div>
                            <div style="color:#64748B;font-size:13px;">
                                Grad-CAM image not available for this patient.<br>
                                Run CT_NB03 to generate heatmaps.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Tab 3: Ultrasound ────────────────────────
                with tab3:
                    st.markdown('<div class="section-header">'
                                '── Fetal Ultrasound Classification</div>',
                                unsafe_allow_html=True)

                    us_cls  = patient.get('us_predicted_class', 'N/A')
                    us_conf = patient.get('us_confidence', None)
                    us_sev  = patient.get('us_severity_label',
                                          SCORE_TO_LABEL.get(
                                              int(us_s) if pd.notna(us_s) else -1,
                                              'Unknown'))

                    uc1, uc2 = st.columns(2)
                    with uc1:
                        st.markdown(
                            metric_card('Fetal Plane', us_cls if us_cls!='N/A' else '—',
                                        US_CLASS_DESC.get(us_cls, ''),
                                        score_to_card_class(us_s)),
                            unsafe_allow_html=True)
                    with uc2:
                        conf_str = f'{float(us_conf):.1%}' \
                                   if us_conf is not None else '—'
                        st.markdown(
                            metric_card('Confidence', conf_str,
                                        f'Severity: {us_sev}',
                                        score_to_card_class(us_s)),
                            unsafe_allow_html=True)

                    # GradCAM
                    st.markdown('<br>', unsafe_allow_html=True)
                    st.markdown('<div class="section-header">'
                                '── Grad-CAM Explainability</div>',
                                unsafe_allow_html=True)

                    us_gradcam = patient.get('us_gradcam_path', '')
                    if us_gradcam and os.path.exists(str(us_gradcam)):
                        img = Image.open(us_gradcam)
                        st.image(img, caption=f'Grad-CAM — {us_cls}',
                                 use_column_width=True)
                    else:
                        st.markdown("""
                        <div class="metric-card card-info"
                             style="text-align:center;padding:40px;">
                            <div style="font-size:32px;margin-bottom:8px;">🔬</div>
                            <div style="color:#64748B;font-size:13px;">
                                Grad-CAM image not available for this patient.<br>
                                Run US_NB03 to generate heatmaps.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Tab 4: Clinical Report ───────────────────
                with tab4:
                    st.markdown('<div class="section-header">'
                                '── AI-Generated Clinical Report</div>',
                                unsafe_allow_html=True)

                    existing_review = st.session_state.reviews.get(case_id, {})

                    # Generate button
                    if case_id not in st.session_state.generated_reports:
                        if st.button('🤖 Generate AI Report',
                                     use_container_width=True,
                                     key=f'gen_{case_id}'):
                            with st.spinner('Retrieving guidelines + generating report...'):
                                rag_db = load_rag_retriever()
                                oai    = get_openai_client()
                                report = generate_report_rag(patient, rag_db, oai)
                                st.session_state.generated_reports[case_id] = report
                            st.rerun()
                    else:
                        report = st.session_state.generated_reports[case_id]

                        st.markdown('<div class="section-header">'
                                    '── Draft Report</div>',
                                    unsafe_allow_html=True)
                        st.markdown(
                            f'<div class="report-box">{report}</div>',
                            unsafe_allow_html=True
                        )

                        st.markdown('<br>', unsafe_allow_html=True)
                        st.markdown('<div class="section-header">'
                                    '── Doctor Review</div>',
                                    unsafe_allow_html=True)

                        # Editable report
                        edited = st.text_area(
                            'Edit report (optional)',
                            value=report,
                            height=200,
                            key=f'edit_{case_id}',
                            label_visibility='collapsed'
                        )

                        # Doctor notes
                        notes = st.text_input(
                            'Doctor notes',
                            placeholder='Add clinical notes...',
                            key=f'notes_{case_id}',
                            label_visibility='collapsed'
                        )

                        # Action buttons
                        bc1, bc2, bc3, bc4 = st.columns(4)
                        with bc1:
                            if st.button('✅ Approve', key=f'app_{case_id}',
                                         use_container_width=True):
                                st.session_state.reviews[case_id] = {
                                    'status':       'APPROVED',
                                    'final_report': edited,
                                    'notes':        notes,
                                    'reviewed_at':  datetime.now().isoformat(),
                                    'reviewer':     'Doctor'
                                }
                                st.success('Report approved and signed off!')
                        with bc2:
                            if st.button('✏️ Approve + Edit',
                                         key=f'edit_app_{case_id}',
                                         use_container_width=True):
                                st.session_state.reviews[case_id] = {
                                    'status':       'EDITED',
                                    'final_report': edited,
                                    'notes':        notes,
                                    'reviewed_at':  datetime.now().isoformat(),
                                    'reviewer':     'Doctor'
                                }
                                st.info('Report approved with edits.')
                        with bc3:
                            if st.button('❌ Reject', key=f'rej_{case_id}',
                                         use_container_width=True):
                                st.session_state.reviews[case_id] = {
                                    'status':       'REJECTED',
                                    'final_report': '',
                                    'notes':        notes,
                                    'reviewed_at':  datetime.now().isoformat(),
                                    'reviewer':     'Doctor'
                                }
                                st.error('Report rejected.')
                        with bc4:
                            if st.button('🔄 Regenerate',
                                         key=f'regen_{case_id}',
                                         use_container_width=True):
                                del st.session_state.generated_reports[case_id]
                                st.rerun()

                        # Show current status
                        if case_id in st.session_state.reviews:
                            status = st.session_state.reviews[case_id]['status']
                            status_colors = {
                                'APPROVED': 'success',
                                'EDITED':   'info',
                                'REJECTED': 'error'
                            }
                            getattr(st, status_colors.get(status, 'info'))(
                                f'Status: {status} · '
                                f'{st.session_state.reviews[case_id]["reviewed_at"][:16]}'
                            )

        else:
            st.markdown("""
            <div style="text-align:center;padding:80px 20px;">
                <div style="font-size:40px;margin-bottom:12px;">👈</div>
                <div style="font-size:14px;color:#64748B;">
                    Select a patient from the list to view details
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Export reviewed reports ───────────────────────────────
    if st.session_state.reviews:
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">── Export</div>',
                    unsafe_allow_html=True)

        reviews_df = pd.DataFrame([
            {'case_id': k, **v}
            for k, v in st.session_state.reviews.items()
        ])

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                '⬇️ Download Reviewed Reports (CSV)',
                data=reviews_df.to_csv(index=False),
                file_name=f'reviewed_reports_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
                use_container_width=True
            )
        with col_exp2:
            st.download_button(
                '⬇️ Download as JSON',
                data=json.dumps(st.session_state.reviews, indent=2),
                file_name=f'reviewed_reports_{datetime.now().strftime("%Y%m%d_%H%M")}.json',
                mime='application/json',
                use_container_width=True
            )

