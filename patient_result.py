import streamlit as st
from datetime import datetime
import time

SEV_COLORS = {
    'Normal':'#10B981','Mild':'#F59E0B',
    'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
}
SEV_BG = {
    'Normal':'rgba(16,185,129,0.08)','Mild':'rgba(245,158,11,0.08)',
    'Moderate':'rgba(249,115,22,0.08)','Severe':'rgba(239,68,68,0.08)',
    'Unknown':'rgba(148,163,184,0.08)'
}
SEV_ICON = {
    'Normal':'✅','Mild':'⚠️','Moderate':'🔶','Severe':'🚨','Unknown':'📋'
}
SEV_HEADLINE = {
    'Normal':   'Your results are normal',
    'Mild':     'Your results show mild findings',
    'Moderate': 'Your results need attention',
    'Severe':   'Your results require urgent care',
    'Unknown':  'Your report is ready'
}
SEV_MESSAGE = {
    'Normal': (
        'Great news — your test results are within the normal healthy range.',
        'No immediate medical attention is required at this time.',
        'We recommend continuing your current health routine and attending your next scheduled check-up.',
        'You do not need to visit the hospital for this report.'
    ),
    'Mild': (
        'Your results show some mild findings that should be monitored.',
        'There is no emergency, but we recommend a follow-up with your doctor.',
        'Please contact your doctor to arrange a review within the next 2 to 4 weeks.',
        'You may be able to discuss this over the phone before deciding to visit.'
    ),
    'Moderate': (
        'Your results indicate findings that need medical attention.',
        'We recommend you see a specialist within the next 7 to 10 days.',
        'Please contact your doctor to book an appointment at your earliest convenience.',
        'Bring this report along to your next appointment.'
    ),
    'Severe': (
        'Your results indicate findings that require prompt medical attention.',
        'Please contact your doctor today or visit the hospital if you feel unwell.',
        'Early treatment leads to the best outcomes — please do not delay.',
        'Your doctor has been notified and may contact you directly.'
    ),
    'Unknown': (
        'Your medical report has been reviewed by your doctor.',
        'Please contact your doctor for a detailed discussion of your results.',
        'Schedule a follow-up appointment at your earliest convenience.',
        'Your doctor will guide you on the appropriate next steps.'
    )
}


def render():
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:26px;font-weight:700;color:#F1F5F9;
                    letter-spacing:-0.5px;margin-bottom:6px;">
            My Report
        </div>
        <div style="font-size:15px;color:#94A3B8;">
            Enter your case reference number to view your approved report
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Lookup form
    col1, col2 = st.columns([3,1])
    with col1:
        default = st.session_state.get('patient_lookup','')
        pid_input = st.text_input(
            'Case Reference Number',
            value=default,
            placeholder='e.g. 24992831 or CASE-1004',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('<br>', unsafe_allow_html=True)
        check = st.button('Find My Report',
                          use_container_width=True,
                          type='primary')

    if not pid_input:
        st.markdown("""
        <div style="background:#111827;border:2px dashed #1E2D40;
                    border-radius:12px;padding:64px;text-align:center;
                    margin-top:20px;">
            <div style="font-size:40px;margin-bottom:16px;">🔍</div>
            <div style="font-size:16px;font-weight:500;color:#F1F5F9;
                        margin-bottom:8px;">Enter your reference number above</div>
            <div style="font-size:14px;color:#64748B;">
                Your reference number was given to you when you registered.<br>
                It is also in any SMS or notification you received.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    pid = pid_input.strip()

    if pid not in st.session_state.patients:
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.08);
                    border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px;padding:24px;margin-top:16px;">
            <div style="font-size:16px;font-weight:600;color:#EF4444;
                        margin-bottom:8px;">Reference number not found</div>
            <div style="font-size:14px;color:#94A3B8;">
                We could not find a record for <b style="color:#F1F5F9;">
                {pid}</b>. Please check the number and try again, or contact 
                the hospital registration desk.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    p      = st.session_state.patients[pid]
    status = p.get('status','PENDING')

    # Pending
    if status == 'PENDING':
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.08);
                    border:1px solid rgba(245,158,11,0.2);
                    border-radius:16px;padding:40px;text-align:center;
                    margin-top:16px;">
            <div style="font-size:40px;margin-bottom:16px;">⏳</div>
            <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                        margin-bottom:10px;">Your report is being reviewed</div>
            <div style="font-size:15px;color:#94A3B8;margin-bottom:20px;">
                Your doctor <b style="color:#F1F5F9;">
                {p.get('doctor_name','')}</b> is currently reviewing your results.
            </div>
            <div style="background:rgba(245,158,11,0.12);
                        border:1px solid rgba(245,158,11,0.25);
                        border-radius:10px;padding:14px 24px;
                        display:inline-block;font-size:14px;color:#F59E0B;
                        font-weight:500;">
                You will be notified here once approved — 
                no need to visit the hospital
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Rejected
    if status == 'REJECTED':
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.08);
                    border:1px solid rgba(239,68,68,0.2);
                    border-radius:16px;padding:40px;text-align:center;
                    margin-top:16px;">
            <div style="font-size:40px;margin-bottom:16px;">📞</div>
            <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                        margin-bottom:10px;">
                Please contact your doctor
            </div>
            <div style="font-size:15px;color:#94A3B8;">
                Your doctor has reviewed your report and would like to 
                discuss the findings with you directly.<br><br>
                Please contact <b style="color:#F1F5F9;">
                {p.get('doctor_name','your doctor')}</b> at your earliest 
                convenience.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── APPROVED ─────────────────────────────────────────────
    fus      = p.get('fusion_label', p.get('severity_label','Unknown'))
    fus_clr  = SEV_COLORS.get(fus,'#94A3B8')
    fus_bg   = SEV_BG.get(fus,'rgba(148,163,184,0.08)')
    icon     = SEV_ICON.get(fus,'📋')
    headline = SEV_HEADLINE.get(fus,'Your report is ready')
    msgs     = SEV_MESSAGE.get(fus, SEV_MESSAGE['Unknown'])

    # Main result card
    st.markdown(f"""
    <div style="background:{fus_bg};border:2px solid {fus_clr}33;
                border-radius:20px;padding:40px 48px;text-align:center;
                margin:16px 0 28px;">
        <div style="font-size:56px;margin-bottom:16px;">{icon}</div>
        <div style="font-size:28px;font-weight:700;color:#F1F5F9;
                    letter-spacing:-0.5px;margin-bottom:10px;">
            {headline}
        </div>
        <div style="font-size:15px;color:#94A3B8;margin-bottom:24px;">
            Case reference: <b style="color:#F1F5F9;
            font-family:'JetBrains Mono',monospace;">{pid}</b>
        </div>
        <div style="background:{fus_bg};border:2px solid {fus_clr}55;
                    border-radius:50px;padding:12px 36px;
                    display:inline-block;margin-bottom:28px;">
            <span style="font-size:24px;font-weight:700;color:{fus_clr};">
                {fus}
            </span>
        </div>
        <div style="max-width:560px;margin:0 auto;text-align:left;
                    background:rgba(0,0,0,0.2);border-radius:12px;
                    padding:24px 28px;">
            <div style="font-size:16px;color:#F1F5F9;font-weight:500;
                        margin-bottom:10px;line-height:1.5;">{msgs[0]}</div>
            <div style="font-size:14px;color:#94A3B8;margin-bottom:8px;
                        line-height:1.6;">{msgs[1]}</div>
            <div style="font-size:14px;color:{fus_clr};margin-bottom:8px;
                        line-height:1.6;font-weight:500;">📅 {msgs[2]}</div>
            <div style="font-size:13px;color:#64748B;padding-top:10px;
                        border-top:1px solid rgba(255,255,255,0.06);
                        line-height:1.6;">{msgs[3]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Details + SMS
    dc1, dc2 = st.columns([3,2])

    with dc1:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin-bottom:14px;">Report Details</div>
        """, unsafe_allow_html=True)

        # What was tested
        mtype = p.get('modality_type','')
        test_items = []
        if 'final_severity_label' in p or mtype=='Lab Report':
            ckd = p.get('ckd_severity','')
            dia = p.get('diabetes_severity_final','')
            thy = p.get('thyroid_severity_final','')
            vals = [v for v in [
                f"Kidney: {ckd}" if ckd and str(ckd) not in ['None','nan'] else None,
                f"Diabetes: {dia}" if dia and str(dia) not in ['None','nan'] else None,
                f"Thyroid: {thy}" if thy and str(thy) not in ['None','nan'] else None
            ] if v]
            if vals:
                test_items.append(('🧪 Blood Test Results',
                                   ' · '.join(vals)))

        if 'ct_predicted_class' in p:
            from doctor_dashboard import CT_DIAGNOSIS
            cls  = p.get('ct_predicted_class','')
            name = CT_DIAGNOSIS.get(cls,(cls,''))[0]
            test_items.append(('🧠 CT Brain Scan', name))

        if 'predicted_class' in p or 'us_predicted_class' in p:
            from doctor_dashboard import US_DIAGNOSIS
            cls  = p.get('predicted_class',p.get('us_predicted_class',''))
            name = US_DIAGNOSIS.get(cls,(cls,''))[0]
            test_items.append(('🔬 Ultrasound', name))

        for lbl, val in test_items:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-radius:10px;padding:14px 18px;
                        margin-bottom:8px;display:flex;
                        justify-content:space-between;align-items:center;">
                <div style="font-size:13px;color:#94A3B8;">{lbl}</div>
                <div style="font-size:14px;font-weight:500;color:#F1F5F9;">
                    {val}</div>
            </div>
            """, unsafe_allow_html=True)

        # Doctor sign-off
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1E2D40;
                    border-radius:10px;padding:16px 18px;margin-top:4px;">
            <div style="font-size:12px;color:#64748B;margin-bottom:6px;
                        text-transform:uppercase;letter-spacing:0.06em;">
                Reviewed and Approved by</div>
            <div style="font-size:16px;font-weight:600;color:#F1F5F9;">
                {p.get('reviewed_by', p.get('doctor_name',''))}</div>
            <div style="font-size:13px;color:#64748B;margin-top:4px;">
                {p.get('reviewed_at','')[:16]}</div>
            {f'<div style="font-size:13px;color:#94A3B8;margin-top:8px;padding-top:8px;border-top:1px solid #1E2D40;font-style:italic;">{p.get("doctor_notes","")}</div>' if p.get("doctor_notes") else ''}
        </div>
        """, unsafe_allow_html=True)

        # Full report
        if p.get('final_report'):
            with st.expander('📄  View Full Clinical Report'):
                st.markdown(f"""
                <div style="background:#0B1120;border-radius:8px;
                            padding:16px 18px;font-size:13px;
                            line-height:1.8;color:#94A3B8;
                            white-space:pre-wrap;">
{p.get('final_report','')}
                </div>
                """, unsafe_allow_html=True)

    with dc2:
        st.markdown("""
        <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                    margin-bottom:14px;">SMS Notification Preview</div>
        """, unsafe_allow_html=True)

        sms = (
            f"[MedAI Hospital]\n\n"
            f"Dear {p.get('name','Patient')},\n\n"
            f"Your medical report is ready.\n\n"
            f"Result: {fus} {icon}\n\n"
            f"{msgs[0]}\n\n"
            f"{msgs[2]}\n\n"
            f"Doctor: {p.get('reviewed_by',p.get('doctor_name',''))}\n"
            f"Ref: {pid}\n\n"
            f"View full report at medai.streamlit.app\n\n"
            f"MedAI Clinical System"
        )

        st.markdown(f"""
        <div style="display:flex;justify-content:center;">
        <div style="background:#1A1A2E;border:2px solid #2A2A4A;
                    border-radius:28px;padding:20px 16px;width:260px;">
            <div style="text-align:center;margin-bottom:14px;">
                <div style="background:#2A2A4A;height:4px;width:40px;
                            border-radius:2px;margin:0 auto 8px;"></div>
                <div style="font-size:11px;color:#64748B;">
                    {p.get('phone','Not provided')}
                </div>
                <div style="font-size:10px;color:#334155;">
                    {datetime.now().strftime('%H:%M')}
                </div>
            </div>
            <div style="background:rgba(16,185,129,0.12);
                        border:1px solid rgba(16,185,129,0.25);
                        border-radius:14px 14px 14px 0;padding:14px;">
                <div style="font-size:10px;color:#10B981;font-weight:600;
                            margin-bottom:8px;">MedAI Hospital</div>
                <div style="font-size:11px;color:#D1FAE5;
                            white-space:pre-wrap;line-height:1.6;">
{sms}
                </div>
            </div>
            <div style="text-align:right;font-size:10px;color:#334155;
                        margin-top:6px;">✓✓ Delivered</div>
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('📱  Send SMS Notification',
                     use_container_width=True,
                     type='primary',
                     key='send_sms'):
            with st.spinner('Sending...'):
                time.sleep(1.5)
            st.success(
                f'✅  SMS sent to {p.get("phone","patient")}!'
            )

    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1E2D40;
                border-radius:12px;padding:20px 24px;
                text-align:center;margin-top:24px;">
        <div style="font-size:15px;color:#F1F5F9;font-weight:500;
                    margin-bottom:6px;">
            Thank you for using MedAI Clinical System
        </div>
        <div style="font-size:13px;color:#64748B;">
            This report was reviewed and approved by 
            <b style="color:#94A3B8;">
            {p.get('reviewed_by',p.get('doctor_name','your doctor'))}</b>.
            For any questions, please contact your doctor directly.
        </div>
    </div>
    """, unsafe_allow_html=True)
