import streamlit as st
import pandas as pd
import numpy as np
import random
import string
from datetime import datetime


# ── Severity maps ─────────────────────────────────────────────
SCORE_TO_LABEL = {0: 'Normal', 1: 'Mild', 2: 'Moderate', 3: 'Severe'}

CT_SEVERITY_MAP = {
    'notumor': 0, 'pituitary': 1, 'meningioma': 2, 'glioma': 3
}
US_SEVERITY_MAP = {
    'Fetal abdomen': 0, 'Fetal femur': 1,
    'Fetal thorax': 2, 'Fetal brain': 3
}
CT_CLASSES = ['notumor', 'pituitary', 'meningioma', 'glioma']
US_CLASSES  = ['Fetal abdomen', 'Fetal brain', 'Fetal femur', 'Fetal thorax']
LAB_DISEASES = ['CKD', 'Diabetes', 'Thyroid', 'CKD+Diabetes', 'All Three']

CT_DESC = {
    'notumor':    'No tumor detected — normal brain scan',
    'pituitary':  'Pituitary adenoma detected',
    'meningioma': 'Meningioma identified',
    'glioma':     'Glioma detected — urgent review required'
}
US_DESC = {
    'Fetal abdomen': 'Normal fetal abdominal measurements',
    'Fetal brain':   'Fetal brain anomaly assessment required',
    'Fetal femur':   'Fetal femur length — normal growth',
    'Fetal thorax':  'Fetal thoracic assessment'
}


def generate_patient_id() -> str:
    return 'PT-' + ''.join(random.choices(string.digits, k=6))


def simulate_ai_processing(test_type: str, seed: int) -> dict:
    """Simulate AI model inference for demo."""
    rng = np.random.RandomState(seed)

    result = {
        'lab_score':    None, 'lab_severity_label':  None,
        'ct_score':     None, 'ct_severity_label':   None,
        'ct_predicted_class': None, 'ct_confidence': None,
        'us_score':     None, 'us_severity_label':   None,
        'us_predicted_class': None, 'us_confidence': None,
    }

    if test_type in ['Lab Report', 'All Tests']:
        s = int(rng.choice([0,1,2,3], p=[0.35,0.30,0.20,0.15]))
        result['lab_score']         = s
        result['lab_severity_label'] = SCORE_TO_LABEL[s]

    if test_type in ['CT Scan', 'All Tests']:
        cls = rng.choice(CT_CLASSES, p=[0.40,0.20,0.25,0.15])
        s   = CT_SEVERITY_MAP[cls]
        result['ct_predicted_class'] = cls
        result['ct_confidence']      = round(float(rng.uniform(0.78, 0.99)), 3)
        result['ct_score']           = s
        result['ct_severity_label']  = SCORE_TO_LABEL[s]

    if test_type in ['Ultrasound', 'All Tests']:
        cls = rng.choice(US_CLASSES)
        s   = US_SEVERITY_MAP[cls]
        result['us_predicted_class'] = cls
        result['us_confidence']      = round(float(rng.uniform(0.82, 0.99)), 3)
        result['us_score']           = s
        result['us_severity_label']  = SCORE_TO_LABEL[s]

    # Fusion — MAX rule
    scores = [v for v in [result['lab_score'],
                           result['ct_score'],
                           result['us_score']] if v is not None]
    fus_s  = max(scores) if scores else None
    result['fusion_score'] = fus_s
    result['fusion_label'] = SCORE_TO_LABEL.get(fus_s, 'Unknown') \
                             if fus_s is not None else 'Processing'
    return result


def render():
    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;
                border-radius:12px;padding:20px 28px;margin-bottom:24px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;
                    color:#F0F4FF;">👤 Patient Portal</div>
        <div style="font-size:12px;color:#64748B;margin-top:4px;
                    font-family:'IBM Plex Mono',monospace;">
            Register for tests · Upload reports · View processing status
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(['📝 Register & Submit', '📊 Track My Status'])

    # ── Tab 1: Register ───────────────────────────────────────
    with tab1:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:18px;">── Patient Registration</div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            name    = st.text_input('Full Name *', placeholder='e.g. Ramesh Kumar')
            age     = st.number_input('Age *', min_value=1, max_value=120, value=35)
            gender  = st.selectbox('Gender', ['Male', 'Female', 'Other'])
            phone   = st.text_input('Phone Number *', placeholder='+91 98765 43210')

        with col2:
            doctors = st.session_state.doctors
            doc_options = {
                f"{v['name']} — {v['dept']}": k
                for k, v in doctors.items()
            }
            selected_doc_label = st.selectbox(
                'Assigned Doctor *',
                list(doc_options.keys())
            )
            selected_doc_id = doc_options[selected_doc_label]

            test_type = st.selectbox(
                'Test Type *',
                ['Lab Report', 'CT Scan', 'Ultrasound', 'All Tests']
            )
            symptoms = st.text_area(
                'Symptoms / Reason for Visit',
                placeholder='e.g. Fatigue, headaches for 2 weeks...',
                height=80
            )

        st.markdown('<br>', unsafe_allow_html=True)

        # Upload section
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:14px;">── Upload Reports (Optional)</div>
        """, unsafe_allow_html=True)

        uc1, uc2, uc3 = st.columns(3)
        with uc1:
            lab_file = st.file_uploader(
                '🧪 Lab Results (CSV/Parquet)',
                type=['csv', 'parquet'],
                key='lab_upload'
            )
        with uc2:
            ct_file = st.file_uploader(
                '🧠 CT Scan Results (CSV)',
                type=['csv'],
                key='ct_upload'
            )
        with uc3:
            us_file = st.file_uploader(
                '🔬 Ultrasound Results (CSV)',
                type=['csv'],
                key='us_upload'
            )

        st.markdown('<br>', unsafe_allow_html=True)

        if st.button('🚀 Submit for AI Processing',
                     use_container_width=True, type='primary'):
            if not name or not phone:
                st.error('Please fill in Name and Phone Number.')
            else:
                # Generate patient ID
                pid  = generate_patient_id()
                seed = hash(pid) % 10000

                # Simulate AI processing
                with st.spinner('🤖 AI processing your reports...'):
                    import time; time.sleep(1.5)
                    ai_result = simulate_ai_processing(test_type, seed)

                    # If files uploaded, use them
                    if lab_file and test_type in ['Lab Report', 'All Tests']:
                        try:
                            if lab_file.name.endswith('.parquet'):
                                lab_df = pd.read_parquet(lab_file)
                            else:
                                lab_df = pd.read_csv(lab_file)
                            if 'final_severity_score' in lab_df.columns:
                                s = int(lab_df['final_severity_score'].dropna().iloc[0])
                                ai_result['lab_score']         = s
                                ai_result['lab_severity_label'] = SCORE_TO_LABEL.get(s, 'Unknown')
                        except Exception:
                            pass

                # Store patient record
                st.session_state.patients[pid] = {
                    'patient_id':    pid,
                    'name':          name,
                    'age':           age,
                    'gender':        gender,
                    'phone':         phone,
                    'doctor_id':     selected_doc_id,
                    'doctor_name':   doctors[selected_doc_id]['name'],
                    'test_type':     test_type,
                    'symptoms':      symptoms,
                    'status':        'PENDING',
                    'registered_at': datetime.now().isoformat(),
                    **ai_result
                }

                st.success(f'✅ Registered successfully!')
                st.markdown(f"""
                <div style="background:#0D2818;border:1px solid #10B981;
                            border-radius:10px;padding:20px 24px;margin-top:12px;">
                    <div style="font-family:'IBM Plex Mono',monospace;
                                font-size:13px;color:#10B981;margin-bottom:12px;">
                        ── REGISTRATION CONFIRMED
                    </div>
                    <div style="display:flex;gap:24px;flex-wrap:wrap;">
                        <div>
                            <div style="font-size:11px;color:#64748B;">Patient ID</div>
                            <div style="font-size:20px;font-weight:600;
                                        color:#F0F4FF;font-family:'IBM Plex Mono',monospace;">
                                {pid}
                            </div>
                            <div style="font-size:11px;color:#64748B;margin-top:4px;">
                                Save this ID to check your report
                            </div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#64748B;">Assigned Doctor</div>
                            <div style="font-size:14px;color:#F0F4FF;margin-top:2px;">
                                {doctors[selected_doc_id]['name']}
                            </div>
                            <div style="font-size:12px;color:#64748B;">
                                {doctors[selected_doc_id]['dept']}
                            </div>
                        </div>
                        <div>
                            <div style="font-size:11px;color:#64748B;">AI Severity</div>
                            <div style="font-size:14px;color:#F0F4FF;margin-top:2px;">
                                {ai_result.get('fusion_label','Processing')}
                            </div>
                            <div style="font-size:11px;color:#64748B;">
                                Pending doctor review
                            </div>
                        </div>
                    </div>
                    <div style="margin-top:14px;padding-top:12px;
                                border-top:1px solid #1E3A2A;
                                font-size:12px;color:#64748B;">
                        📱 Your report will be available at
                        <b style="color:#10B981;">My Report</b> page
                        once the doctor reviews it.
                        No need to revisit the hospital!
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 2: Track Status ───────────────────────────────────
    with tab2:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:18px;">── Track Your Submission</div>
        """, unsafe_allow_html=True)

        track_id = st.text_input(
            'Enter your Patient ID',
            placeholder='e.g. PT-123456'
        )

        if track_id and track_id in st.session_state.patients:
            p      = st.session_state.patients[track_id]
            status = p.get('status', 'PENDING')
            clr    = {'APPROVED': '#10B981', 'REJECTED': '#EF4444',
                      'PENDING': '#F59E0B'}.get(status, '#64748B')

            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-radius:10px;padding:20px 24px;margin-top:12px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:14px;">
                    <div style="font-family:'IBM Plex Mono',monospace;
                                font-size:16px;color:#F0F4FF;">{track_id}</div>
                    <div style="background:rgba(0,0,0,.2);
                                border:1px solid {clr};color:{clr};
                                font-size:12px;padding:3px 12px;
                                border-radius:20px;
                                font-family:'IBM Plex Mono',monospace;">
                        {status}
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;
                            gap:12px;">
                    <div>
                        <div style="font-size:11px;color:#64748B;">Patient</div>
                        <div style="font-size:13px;color:#F0F4FF;">
                            {p.get('name','')} · {p.get('age','')}y
                        </div>
                    </div>
                    <div>
                        <div style="font-size:11px;color:#64748B;">Doctor</div>
                        <div style="font-size:13px;color:#F0F4FF;">
                            {p.get('doctor_name','')}
                        </div>
                    </div>
                    <div>
                        <div style="font-size:11px;color:#64748B;">Test</div>
                        <div style="font-size:13px;color:#F0F4FF;">
                            {p.get('test_type','')}
                        </div>
                    </div>
                </div>
                <div style="margin-top:14px;padding-top:12px;
                            border-top:1px solid #1E293B;font-size:12px;
                            color:#64748B;">
                    Submitted: {p.get('registered_at','')[:16]}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if status == 'APPROVED':
                st.success('✅ Your report is ready! Go to **My Report** page.')
                if st.button('View My Report →', key='track_view'):
                    st.session_state.patient_lookup = track_id
                    st.session_state.page = 'result'
                    st.rerun()
            else:
                st.info('⏳ Report is being reviewed by your doctor. '
                        'You will be notified once approved.')

        elif track_id:
            st.error('Patient ID not found. Please check and try again.')
