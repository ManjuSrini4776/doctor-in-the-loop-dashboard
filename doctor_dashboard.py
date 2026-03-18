"""
Doctor Dashboard — 4 department tabs
RAG summaries pre-generated at load time (not live)
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils import (SEV_COLOR, SEV_BG, CT_NAMES, CT_DESC, CT_IMAGE,
                   US_NAMES, US_DESC, US_IMAGE,
                   SCORE_TO_LABEL, DOCTORS, PRESCRIPTIONS,
                   load_lab, load_ct, load_us, load_fusion)

URGENCY = {
    'Severe':   ('URGENT',      '#FF3B3B', 'rgba(255,59,59,0.12)'),
    'Moderate': ('SEMI-URGENT', '#FF6B35', 'rgba(255,107,53,0.12)'),
    'Mild':     ('ROUTINE',     '#FFB800', 'rgba(255,184,0,0.12)'),
    'Normal':   ('ROUTINE',     '#00C48C', 'rgba(0,196,140,0.12)'),
    'Unknown':  ('REVIEW',      '#8892A4', 'rgba(136,146,164,0.12)'),
}

# Patient-friendly messages
PATIENT_MSG = {
    'Normal': (
        "Your test results have been reviewed by your doctor.\n\n"
        "Good news — your results are within the normal healthy range. "
        "No immediate medical attention is required.\n\n"
        "Please continue your current medication and maintain a healthy lifestyle. "
        "Your next routine check-up is recommended in 3 months.\n\n"
        "If you have any concerns, please contact your doctor."
    ),
    'Mild': (
        "Your test results have been reviewed by your doctor.\n\n"
        "Your results show some mild findings that need to be monitored. "
        "There is no emergency at this time.\n\n"
        "Please follow your doctor's prescription carefully and schedule "
        "a follow-up appointment within 2 to 4 weeks.\n\n"
        "Contact your doctor if your symptoms worsen."
    ),
    'Moderate': (
        "Your test results have been reviewed by your doctor.\n\n"
        "Your results indicate findings that need medical attention. "
        "Please follow your doctor's instructions carefully.\n\n"
        "Please book a follow-up appointment within the next 7 to 10 days. "
        "Bring this report to your next appointment.\n\n"
        "Do not ignore these findings — early treatment leads to better outcomes."
    ),
    'Severe': (
        "Your test results have been reviewed by your doctor.\n\n"
        "Your results indicate findings that require prompt medical attention. "
        "Please do not delay in following your doctor's instructions.\n\n"
        "Please contact your doctor today or visit the hospital if you feel unwell. "
        "Your doctor has been notified and may contact you directly.\n\n"
        "Early treatment is critical for the best outcomes."
    ),
}


# ── RAG setup ─────────────────────────────────────────────────
@st.cache_resource
def get_rag_components():
    """Load RAG DB and OpenAI client once — cached."""
    rag_db = None
    client = None

    # Find FAISS index — check multiple paths
    faiss_paths = [
        'rag_output/baseline_vector_db',
        'baseline_vector_db',
        '.',  # root folder (where user uploaded)
    ]
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            encode_kwargs={'batch_size': 32}
        )
        for path in faiss_paths:
            if os.path.exists(os.path.join(path, 'index.faiss')):
                rag_db = FAISS.load_local(
                    path, emb,
                    allow_dangerous_deserialization=True
                )
                break
    except Exception:
        pass

    # OpenAI client
    try:
        from openai import OpenAI
        key = st.secrets.get('OPENAI_API_KEY',
                             os.environ.get('OPENAI_API_KEY', ''))
        if key:
            client = OpenAI(api_key=key)
    except Exception:
        pass

    return rag_db, client


def build_rag_summary(patient: dict, rag_db, client) -> dict:
    """
    Build RAG summary with citations and recommendations.
    Returns dict with: summary, citations, recommendations, urgency
    """
    fus   = patient.get('_sev', 'Unknown')
    mtype = patient.get('_mtype', '')

    # Build clinical query
    findings = []
    if mtype == 'Lab Report':
        ckd = patient.get('ckd_severity', '')
        dia = patient.get('diabetes_severity_final', '')
        thy = patient.get('thyroid_severity_final', '')
        sev = patient.get('final_severity_label', fus)
        if ckd and str(ckd) not in ['None','nan','Not tested']:
            findings.append(f"Chronic kidney disease: {ckd}")
        if dia and str(dia) not in ['None','nan','Not tested']:
            findings.append(f"Diabetes mellitus: {dia}")
        if thy and str(thy) not in ['None','nan','Not tested']:
            findings.append(f"Thyroid disorder: {thy}")
        findings.append(f"Overall lab severity: {sev}")

    elif mtype == 'CT Scan':
        cls  = patient.get('ct_predicted_class', '')
        conf = patient.get('ct_confidence', 0)
        sev  = patient.get('ct_severity_label', fus)
        findings.append(f"CT Brain: {CT_NAMES.get(cls, cls)}")
        findings.append(f"Classification confidence: {float(conf):.1%}")
        findings.append(f"Imaging severity: {sev}")

    elif mtype == 'Ultrasound':
        cls  = patient.get('predicted_class', '')
        conf = patient.get('confidence', 0)
        sev  = patient.get('us_severity_label', fus)
        findings.append(f"Ultrasound: {US_NAMES.get(cls, cls)}")
        findings.append(f"Classification confidence: {float(conf):.1%}")
        findings.append(f"Ultrasound severity: {sev}")

    elif mtype == 'Combined Assessment':
        for label, key in [('Lab', 'lab_score'),
                           ('CT', 'ct_score'),
                           ('Ultrasound', 'us_score')]:
            val = patient.get(key)
            if val is not None and str(val) not in ['None','nan']:
                try:
                    findings.append(
                        f"{label}: {SCORE_TO_LABEL.get(int(float(val)), 'Unknown')}"
                    )
                except Exception:
                    pass
        findings.append(f"Fusion severity: {fus}")

    query = '. '.join(findings)

    # Retrieve context from RAG
    rag_context = []
    citations   = []
    if rag_db and query:
        try:
            docs = rag_db.similarity_search(query, k=4)
            for i, doc in enumerate(docs):
                rag_context.append(doc.page_content)
                src = doc.metadata.get('source', '')
                if src:
                    fname = os.path.basename(src).replace('.pdf','')
                    citations.append(f"[{i+1}] {fname}")
        except Exception:
            pass

    context_text = '\n\n'.join(rag_context) if rag_context else ''

    # Try OpenAI with RAG context
    if client and query:
        prompt = (
            "You are a clinical decision support system in a hospital.\n"
            "A doctor is reviewing a patient's AI-analysed medical report.\n"
            "Generate a structured clinical summary with citations.\n\n"
            f"Patient findings:\n{query}\n\n"
            + (f"Relevant clinical guidelines:\n{context_text}\n\n"
               if context_text else "") +
            "Generate the following sections. Be concise and clinical.\n"
            "Do NOT mention AI, machine learning, or system names.\n\n"
            "CLINICAL SUMMARY:\n"
            "[2-3 sentence clinical overview of the patient's condition]\n\n"
            "KEY FINDINGS:\n"
            "• [finding with guideline reference if available]\n"
            "• [finding with guideline reference if available]\n\n"
            "RECOMMENDATIONS:\n"
            "• [specific clinical action 1]\n"
            "• [specific clinical action 2]\n"
            "• [specific clinical action 3]\n\n"
            "FOLLOW-UP PLAN:\n"
            "[specific timeline and monitoring plan]\n\n"
            f"URGENCY: {URGENCY.get(fus, URGENCY['Unknown'])[0]}"
        )
        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.1,
                max_tokens=600
            )
            text = resp.choices[0].message.content
            return _parse_llm_response(text, citations, fus)
        except Exception:
            pass

    # Fallback — structured template using RAG context
    return _build_fallback_summary(findings, fus, mtype, citations, context_text)


def _parse_llm_response(text: str, citations: list, fus: str) -> dict:
    """Parse LLM response into structured dict."""
    sections = {
        'summary':         '',
        'key_findings':    [],
        'recommendations': [],
        'followup':        '',
        'citations':       citations,
        'urgency':         URGENCY.get(fus, URGENCY['Unknown'])[0],
    }
    current = None
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if 'CLINICAL SUMMARY' in line.upper():
            current = 'summary'
        elif 'KEY FINDINGS' in line.upper():
            current = 'findings'
        elif 'RECOMMENDATIONS' in line.upper():
            current = 'recommendations'
        elif 'FOLLOW' in line.upper():
            current = 'followup'
        elif 'URGENCY' in line.upper():
            pass
        elif current == 'summary':
            sections['summary'] += line + ' '
        elif current == 'findings' and line.startswith('•'):
            sections['key_findings'].append(line[1:].strip())
        elif current == 'recommendations' and line.startswith('•'):
            sections['recommendations'].append(line[1:].strip())
        elif current == 'followup':
            sections['followup'] += line + ' '
    return sections


def _build_fallback_summary(findings, fus, mtype, citations, context):
    """Clean fallback when no OpenAI key."""
    urg = URGENCY.get(fus, URGENCY['Unknown'])[0]

    summary_map = {
        'Severe':   f"Patient presents with severe {mtype.lower()} findings requiring immediate clinical attention. Prompt specialist referral is indicated.",
        'Moderate': f"Patient presents with moderate {mtype.lower()} findings requiring medical review. Specialist consultation within 7 days is recommended.",
        'Mild':     f"Patient presents with mild {mtype.lower()} findings requiring monitoring. Outpatient follow-up within 2-4 weeks is advised.",
        'Normal':   f"Patient's {mtype.lower()} results are within normal limits. Routine follow-up is recommended.",
    }

    recs_map = {
        'Severe':   ['Immediate specialist referral required',
                     'Consider hospital admission for close monitoring',
                     'Initiate appropriate treatment protocol without delay',
                     'Daily monitoring of relevant parameters'],
        'Moderate': ['Specialist review within 7 days',
                     'Medication adjustment may be required',
                     'Repeat investigations in 2 weeks',
                     'Patient education on warning signs'],
        'Mild':     ['Outpatient follow-up within 2-4 weeks',
                     'Lifestyle modification counselling',
                     'Monitor symptoms and report changes',
                     'Review current medications'],
        'Normal':   ['Routine follow-up in 3 months',
                     'Continue current management plan',
                     'Maintain healthy diet and exercise',
                     'Annual screening recommended'],
    }

    followup_map = {
        'Severe':   'Immediate — within 24 to 48 hours',
        'Moderate': 'Within 7 to 10 days',
        'Mild':     'Within 2 to 4 weeks',
        'Normal':   'Routine review in 3 months',
    }

    # Extract guideline snippets for citations
    cite_texts = []
    if context:
        lines = [l.strip() for l in context.split('\n') if len(l.strip()) > 40]
        cite_texts = lines[:3]

    return {
        'summary':         summary_map.get(fus, f"Clinical review of {mtype.lower()} findings."),
        'key_findings':    [f.capitalize() for f in findings[:4]],
        'recommendations': recs_map.get(fus, recs_map['Normal']),
        'followup':        followup_map.get(fus, 'As clinically indicated'),
        'citations':       citations,
        'cite_texts':      cite_texts,
        'urgency':         urg,
    }


# ── Pre-generate summaries for all patients in a dataframe ────
def pregenerate_summaries(df: pd.DataFrame, rag_db, client,
                          key_prefix: str):
    """Generate RAG summaries for top 50 patients — stored in session."""
    if 'rag_summaries' not in st.session_state:
        st.session_state['rag_summaries'] = {}

    for _, row in df.head(50).iterrows():
        pid = str(row['_id'])
        k   = key_prefix + '_' + pid
        if k not in st.session_state['rag_summaries']:
            st.session_state['rag_summaries'][k] = \
                build_rag_summary(row.to_dict(), rag_db, client)


# ── Main render ───────────────────────────────────────────────
def render():
    st.markdown(
        '<div style="font-size:28px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.7px;margin-bottom:4px;">Doctor Dashboard</div>'
        '<div style="font-size:16px;color:#7A90A8;margin-bottom:20px;">'
        'Review AI-analysed patient reports, add prescriptions '
        'and release results to patients</div>',
        unsafe_allow_html=True
    )

    # Load RAG once
    rag_db, client = get_rag_components()

    rag_status = (
        '🟢 RAG + GPT-4o-mini active'
        if client and rag_db else
        '🟡 RAG active (no GPT — using template)' if rag_db else
        '⚪ Template mode (RAG not loaded)'
    )
    st.markdown(
        '<div style="font-size:12px;color:#4A6080;margin-bottom:18px;'
        'font-family:monospace;">' + rag_status + '</div>',
        unsafe_allow_html=True
    )

    # Load all data
    lab_df = load_lab()
    ct_df  = load_ct()
    us_df  = load_us()
    fus_df = load_fusion()

    # 4 department tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        '🧪  Lab Reports — Dr. Priya Sharma',
        '🧠  CT Scans — Dr. Arjun Mehta',
        '🔬  Ultrasound — Dr. Kavitha Rajan',
        '⚡  Combined — Dr. Suresh Kumar',
    ])

    configs = [
        (tab1, lab_df,  'lab',  'DR001', 'Lab Report'),
        (tab2, ct_df,   'ct',   'DR002', 'CT Scan'),
        (tab3, us_df,   'us',   'DR003', 'Ultrasound'),
        (tab4, fus_df,  'fus',  'DR004', 'Combined Assessment'),
    ]

    for tab, df, prefix, doc_id, mtype in configs:
        with tab:
            if df is None:
                st.markdown(
                    '<div style="background:#112033;border:2px dashed #1E3250;'
                    'border-radius:12px;padding:40px;text-align:center;">'
                    '<div style="font-size:16px;color:#7A90A8;">No data loaded for this tab</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                continue

            # Pre-generate summaries silently
            pregenerate_summaries(df, rag_db, client, prefix)

            render_department_tab(df, prefix, doc_id, mtype, rag_db, client)


def render_department_tab(df, prefix, doc_id, mtype, rag_db, client):
    doc = DOCTORS[doc_id]

    # Doctor info bar
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-radius:10px;padding:12px 20px;margin-bottom:16px;'
        'display:flex;align-items:center;gap:14px;">'
        '<div style="background:' + doc['color'] + '22;width:40px;height:40px;'
        'border-radius:50%;display:flex;align-items:center;justify-content:center;'
        'font-size:18px;border:2px solid ' + doc['color'] + '44;">🩺</div>'
        '<div>'
        '<div style="font-size:15px;font-weight:700;color:#F0F6FF;">'
        + doc['name'] + '</div>'
        '<div style="font-size:13px;color:#7A90A8;">'
        + doc['dept'] + '  ·  ' + doc['specialty'] + '</div>'
        '</div>'
        '<div style="margin-left:auto;background:rgba(0,196,140,0.12);'
        'border:1px solid rgba(0,196,140,0.3);color:#00C48C;'
        'font-size:12px;font-weight:600;padding:4px 14px;border-radius:20px;">'
        '● On Duty</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Stats
    sev_counts = df['_sev'].value_counts()
    s1,s2,s3,s4 = st.columns(4)
    for col,(lbl,sev,clr) in zip([s1,s2,s3,s4],[
        ('Severe',   'Severe',   '#FF3B3B'),
        ('Moderate', 'Moderate', '#FF6B35'),
        ('Mild',     'Mild',     '#FFB800'),
        ('Normal',   'Normal',   '#00C48C'),
    ]):
        cnt = int(sev_counts.get(sev, 0))
        with col:
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-top:3px solid ' + clr + ';border-radius:10px;'
                'padding:12px;text-align:center;margin-bottom:14px;">'
                '<div style="font-size:26px;font-weight:800;color:' + clr + ';">'
                + str(cnt) + '</div>'
                '<div style="font-size:13px;color:#7A90A8;margin-top:3px;">'
                + lbl + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    # Two column layout
    left, right = st.columns([1, 2.4], gap='large')

    with left:
        st.markdown(
            '<div style="font-size:13px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;'
            'margin-bottom:12px;">Patient Queue</div>',
            unsafe_allow_html=True
        )

        # Severity filter
        sev_filter = st.selectbox(
            'Filter', ['All','Severe','Moderate','Mild','Normal'],
            key='filter_' + prefix,
            label_visibility='collapsed'
        )

        filt_df = df if sev_filter == 'All' \
                  else df[df['_sev'] == sev_filter]

        sev_order = {'Severe':0,'Moderate':1,'Mild':2,'Normal':3,'Unknown':4}
        filt_df   = filt_df.sort_values(
            '_sev', key=lambda x: x.map(sev_order)
        ).head(50)

        for _, row in filt_df.iterrows():
            pid    = str(row['_id'])
            sev    = row.get('_sev','Unknown')
            clr    = SEV_COLOR.get(sev,'#8892A4')
            is_sel = st.session_state.get('sel_' + prefix) == pid
            status = st.session_state.get('status_' + prefix + '_' + pid, 'PENDING')
            s_icon = {'APPROVED':'✓','REJECTED':'✗','PENDING':'○'}.get(status,'○')

            if st.button(
                s_icon + '  ' + pid + '  ·  ' + sev,
                key='btn_' + prefix + '_' + pid,
                use_container_width=True,
                type='primary' if is_sel else 'secondary'
            ):
                st.session_state['sel_' + prefix] = pid
                st.rerun()

    with right:
        sel_pid = st.session_state.get('sel_' + prefix)

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

        # Get patient row
        match = df[df['_id'] == sel_pid]
        if match.empty:
            return
        p   = match.iloc[0].to_dict()
        sev = p.get('_sev','Unknown')
        clr = SEV_COLOR.get(sev,'#8892A4')
        bg  = SEV_BG.get(sev,'rgba(136,146,164,0.1)')
        urg_tag, urg_clr, urg_bg = URGENCY.get(sev, URGENCY['Unknown'])

        # Patient header
        st.markdown(
            '<div style="background:#112033;border:1.5px solid #1E3250;'
            'border-radius:14px;padding:18px 22px;margin-bottom:18px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;">'
            '<div>'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
            'Patient ID</div>'
            '<div style="font-size:22px;font-weight:800;color:#F0F6FF;'
            'font-family:monospace;">' + sel_pid + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
            + mtype + '  ·  Ordered by ' + doc['name'] + '</div>'
            '</div>'
            '<div style="background:' + urg_bg + ';border:2px solid ' +
            urg_clr + '44;border-radius:10px;padding:12px 20px;text-align:center;">'
            '<div style="font-size:11px;font-weight:700;color:' + urg_clr + ';'
            'letter-spacing:0.12em;margin-bottom:4px;">' + urg_tag + '</div>'
            '<div style="font-size:20px;font-weight:800;color:' + clr + ';">'
            + sev + '</div>'
            '</div></div></div>',
            unsafe_allow_html=True
        )

        # ── Test Findings ─────────────────────────────────────
        st.markdown(
            '<div style="font-size:14px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;'
            'margin-bottom:12px;">Test Findings</div>',
            unsafe_allow_html=True
        )

        render_findings(p, mtype)

        # ── RAG Summary ───────────────────────────────────────
        st.markdown(
            '<div style="font-size:14px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;'
            'margin:20px 0 12px;">AI Clinical Summary</div>',
            unsafe_allow_html=True
        )

        # Get pre-generated summary
        sum_key = prefix + '_' + sel_pid
        summaries = st.session_state.get('rag_summaries', {})

        if sum_key not in summaries:
            summaries[sum_key] = build_rag_summary(p, rag_db, client)
            st.session_state['rag_summaries'] = summaries

        s = summaries[sum_key]

        # Summary text
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #263A55;'
            'border-left:5px solid #7C3AED;border-radius:12px;'
            'padding:20px 24px;margin-bottom:14px;">'
            '<div style="font-size:15px;color:#E8EDF5;line-height:1.8;">'
            + s.get('summary','') + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Key Findings
        if s.get('key_findings'):
            findings_html = ''.join([
                '<div style="display:flex;gap:10px;padding:8px 0;'
                'border-bottom:1px solid #1E3250;">'
                '<span style="color:#7C3AED;font-weight:700;flex-shrink:0;">•</span>'
                '<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">'
                + f + '</span></div>'
                for f in s['key_findings']
            ])
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:16px 20px;margin-bottom:14px;">'
                '<div style="font-size:13px;font-weight:700;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">'
                'Key Findings</div>'
                + findings_html +
                '</div>',
                unsafe_allow_html=True
            )

        # Recommendations
        if s.get('recommendations'):
            rec_html = ''.join([
                '<div style="display:flex;gap:12px;padding:10px 0;'
                'border-bottom:1px solid #1E3250;">'
                '<span style="background:#2563EB22;color:#4A9EFF;'
                'font-weight:700;font-size:13px;padding:2px 8px;'
                'border-radius:6px;flex-shrink:0;height:fit-content;">'
                + str(i+1) + '</span>'
                '<span style="font-size:14px;color:#C8D6E8;line-height:1.6;">'
                + r + '</span></div>'
                for i, r in enumerate(s['recommendations'])
            ])
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-left:5px solid #00C48C;border-radius:10px;'
                'padding:16px 20px;margin-bottom:14px;">'
                '<div style="font-size:13px;font-weight:700;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">'
                'Recommendations</div>'
                + rec_html +
                '</div>',
                unsafe_allow_html=True
            )

        # Follow-up plan
        if s.get('followup'):
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:14px 20px;margin-bottom:14px;">'
                '<div style="font-size:13px;font-weight:700;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                'Follow-up Plan</div>'
                '<div style="font-size:15px;color:#E8EDF5;font-weight:500;">'
                + s.get('followup','') + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # Citations from guidelines
        if s.get('citations'):
            cite_html = '  ·  '.join(s['citations'])
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:12px 18px;margin-bottom:18px;">'
                '<div style="font-size:12px;font-weight:700;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                'Guideline References</div>'
                '<div style="font-size:13px;color:#64748B;font-family:monospace;">'
                + cite_html + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
        elif s.get('cite_texts'):
            st.markdown(
                '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:12px 18px;margin-bottom:18px;">'
                '<div style="font-size:12px;font-weight:700;color:#4A6080;'
                'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
                'From Clinical Guidelines</div>'
                + ''.join([
                    '<div style="font-size:13px;color:#64748B;'
                    'font-style:italic;padding:4px 0;border-bottom:1px solid #1E3250;">'
                    '"' + t[:120] + '..."</div>'
                    for t in s['cite_texts'][:2]
                ]) +
                '</div>',
                unsafe_allow_html=True
            )

        # ── GradCAM ───────────────────────────────────────────
        if mtype == 'CT Scan':
            cls      = p.get('ct_predicted_class','')
            img_path = CT_IMAGE.get(cls,'')
            if img_path and os.path.exists(img_path):
                st.markdown(
                    '<div style="font-size:14px;font-weight:700;color:#F0F6FF;'
                    'margin-bottom:10px;">AI Attention Map (Grad-CAM)</div>',
                    unsafe_allow_html=True
                )
                gc1, gc2 = st.columns(2)
                with gc1:
                    st.image(img_path, caption='CT Scan',
                             use_column_width=True)
                with gc2:
                    st.image(img_path, caption='Grad-CAM Heatmap',
                             use_column_width=True)
                st.markdown(
                    '<div style="font-size:12px;color:#4A6080;margin-bottom:16px;">'
                    'Highlighted regions show where the AI model focused '
                    'during classification.</div>',
                    unsafe_allow_html=True
                )

        if mtype == 'Ultrasound':
            cls      = p.get('predicted_class','')
            img_path = US_IMAGE.get(cls,'')
            if img_path and os.path.exists(img_path):
                st.markdown(
                    '<div style="font-size:14px;font-weight:700;color:#F0F6FF;'
                    'margin-bottom:10px;">AI Attention Map (Grad-CAM)</div>',
                    unsafe_allow_html=True
                )
                ug1, ug2 = st.columns(2)
                with ug1:
                    st.image(img_path, caption='Ultrasound Scan',
                             use_column_width=True)
                with ug2:
                    st.image(img_path, caption='Grad-CAM Heatmap',
                             use_column_width=True)

        # ── Doctor Approval ───────────────────────────────────
        st.markdown(
            '<div style="font-size:14px;font-weight:700;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.1em;'
            'margin:20px 0 12px;">Doctor Review & Approval</div>',
            unsafe_allow_html=True
        )

        doc_notes = st.text_area(
            'Add clinical notes or prescription',
            placeholder='Add prescription, clinical notes, amendments...',
            height=100,
            key='notes_' + prefix + '_' + sel_pid,
            label_visibility='collapsed'
        )

        # Patient message preview
        fus_label = p.get('_sev','Unknown')
        pat_msg   = PATIENT_MSG.get(fus_label, PATIENT_MSG['Normal'])
        if doc_notes:
            pat_msg += f"\n\nDoctor's note: {doc_notes}"

        with st.expander('📱  Preview Patient Message'):
            st.markdown(
                '<div style="background:#0A1628;border:1.5px solid #1E3250;'
                'border-radius:12px;padding:20px 24px;">'
                '<div style="font-size:12px;font-weight:600;color:#00C48C;'
                'margin-bottom:12px;letter-spacing:0.08em;">MESSAGE TO PATIENT</div>'
                '<div style="font-size:14px;color:#C8D6E8;line-height:1.8;'
                'white-space:pre-wrap;">' + pat_msg + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # Approve / Reject buttons
        st.markdown('<br>', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        status_key = 'status_' + prefix + '_' + sel_pid

        with b1:
            if st.button('✅  Approve & Send',
                         key='app_' + prefix + '_' + sel_pid,
                         use_container_width=True,
                         type='primary'):
                st.session_state[status_key] = 'APPROVED'
                # Store approved record
                st.session_state.patients[sel_pid] = {
                    **p,
                    'patient_id':    sel_pid,
                    'case_id':       sel_pid,
                    'name':          sel_pid,
                    'modality_type': mtype,
                    'fusion_label':  fus_label,
                    'severity_label':fus_label,
                    'doctor_id':     doc_id,
                    'doctor_name':   doc['name'],
                    'status':        'APPROVED',
                    'final_report':  s.get('summary',''),
                    'prescription':  doc_notes,
                    'doctor_notes':  doc_notes,
                    'patient_message': pat_msg,
                    'reviewed_at':   datetime.now().isoformat(),
                    'reviewed_by':   doc['name'],
                }
                st.success('✅  Report approved! Patient has been notified.')
                st.balloons()

        with b2:
            if st.button('✏️  Approve with Edits',
                         key='edit_' + prefix + '_' + sel_pid,
                         use_container_width=True):
                st.session_state[status_key] = 'APPROVED'
                st.session_state.patients[sel_pid] = {
                    **p,
                    'patient_id':    sel_pid,
                    'case_id':       sel_pid,
                    'name':          sel_pid,
                    'modality_type': mtype,
                    'fusion_label':  fus_label,
                    'severity_label':fus_label,
                    'doctor_id':     doc_id,
                    'doctor_name':   doc['name'],
                    'status':        'APPROVED',
                    'final_report':  s.get('summary',''),
                    'prescription':  doc_notes,
                    'doctor_notes':  doc_notes,
                    'patient_message': pat_msg,
                    'reviewed_at':   datetime.now().isoformat(),
                    'reviewed_by':   doc['name'],
                }
                st.info('Report approved with your notes.')

        with b3:
            if st.button('❌  Reject',
                         key='rej_' + prefix + '_' + sel_pid,
                         use_container_width=True):
                st.session_state[status_key] = 'REJECTED'
                st.error('Report rejected.')

        # Status badge
        cur = st.session_state.get(status_key,'PENDING')
        if cur == 'APPROVED':
            st.markdown(
                '<div style="background:rgba(0,196,140,0.1);'
                'border:1.5px solid rgba(0,196,140,0.3);border-radius:10px;'
                'padding:14px 20px;margin-top:14px;">'
                '<div style="font-size:15px;font-weight:700;color:#00C48C;">'
                '✅  Approved by ' + doc['name'] + '  ·  '
                + datetime.now().strftime('%Y-%m-%d %H:%M') + '</div>'
                '<div style="font-size:13px;color:#7A90A8;margin-top:4px;">'
                'Report released. Patient message sent.</div>'
                '</div>',
                unsafe_allow_html=True
            )


def render_findings(p, mtype):
    """Render test-specific findings cleanly."""
    if mtype == 'Lab Report':
        ckd = p.get('ckd_severity','Not tested')
        dia = p.get('diabetes_severity_final','Not tested')
        thy = p.get('thyroid_severity_final','Not tested')
        sev = p.get('final_severity_label', p.get('_sev','Unknown'))
        clr = SEV_COLOR.get(sev,'#8892A4')

        c1,c2,c3 = st.columns(3)
        for col,(lbl,val) in zip([c1,c2,c3],[
            ('Kidney Function', ckd),
            ('Blood Sugar', dia),
            ('Thyroid Function', thy)
        ]):
            v = str(val) if val and str(val) not in \
                ['None','nan','NaN','Unknown'] else 'Not tested'
            with col:
                st.markdown(
                    '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                    'border-radius:10px;padding:16px;margin-bottom:12px;">'
                    '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                    'text-transform:uppercase;letter-spacing:0.08em;'
                    'margin-bottom:8px;">' + lbl + '</div>'
                    '<div style="font-size:16px;font-weight:700;color:#F0F6FF;">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
        # Overall lab severity
        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid ' + clr + ';border-radius:10px;'
            'padding:14px 18px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
            'Overall Lab Severity</div>'
            '<div style="font-size:18px;font-weight:800;color:' + clr + ';">'
            + sev + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    elif mtype == 'CT Scan':
        cls  = p.get('ct_predicted_class','')
        conf = p.get('ct_confidence', 0)
        sev  = p.get('ct_severity_label', p.get('_sev','Unknown'))
        clr  = SEV_COLOR.get(sev,'#8892A4')
        name = CT_NAMES.get(cls, cls)
        desc = CT_DESC.get(cls,'')

        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid ' + clr + ';border-radius:10px;'
            'padding:18px 22px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
            'CT Brain Scan</div>'
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="display:flex;gap:20px;">'
            '<span style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '</span>'
            '<span style="font-size:14px;color:#7A90A8;">'
            'Confidence: ' + str(round(float(conf)*100,1)) + '%</span>'
            '</div></div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Ultrasound':
        cls  = p.get('predicted_class','')
        conf = p.get('confidence', 0)
        sev  = p.get('us_severity_label', p.get('_sev','Unknown'))
        clr  = SEV_COLOR.get(sev,'#8892A4')
        name = US_NAMES.get(cls, cls)
        desc = US_DESC.get(cls,'')

        st.markdown(
            '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
            'border-left:5px solid ' + clr + ';border-radius:10px;'
            'padding:18px 22px;margin-bottom:12px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">'
            'Obstetric Ultrasound</div>'
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:6px;">' + name + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-bottom:8px;">'
            + desc + '</div>'
            '<div style="display:flex;gap:20px;">'
            '<span style="font-size:14px;color:' + clr + ';font-weight:600;">'
            + sev + '</span>'
            '<span style="font-size:14px;color:#7A90A8;">'
            'Confidence: ' + str(round(float(conf)*100,1)) + '%</span>'
            '</div></div>',
            unsafe_allow_html=True
        )

    elif mtype == 'Combined Assessment':
        c1,c2,c3,c4 = st.columns(4)
        for col,(lbl,key) in zip([c1,c2,c3,c4],[
            ('Lab',       'lab_score'),
            ('CT',        'ct_score'),
            ('Ultrasound','us_score'),
            ('Fusion',    'fusion_score'),
        ]):
            val = p.get(key)
            try:
                v = SCORE_TO_LABEL.get(int(float(val)),'—') \
                    if val is not None and str(val) not in ['None','nan'] else '—'
            except Exception:
                v = '—'
            clr = SEV_COLOR.get(v,'#4A6080')
            with col:
                st.markdown(
                    '<div style="background:#0D1B2E;border:1.5px solid #1E3250;'
                    'border-radius:10px;padding:14px;text-align:center;'
                    'margin-bottom:12px;">'
                    '<div style="font-size:11px;font-weight:600;color:#4A6080;'
                    'text-transform:uppercase;letter-spacing:0.08em;'
                    'margin-bottom:8px;">' + lbl + '</div>'
                    '<div style="font-size:22px;font-weight:800;color:' + clr + ';">'
                    + v + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
