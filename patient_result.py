import streamlit as st
from datetime import datetime
import time

SEV_COLORS = {
    'Normal':   '#10B981', 'Mild':    '#F59E0B',
    'Moderate': '#F97316', 'Severe':  '#EF4444', 'Unknown': '#94A3B8'
}
SEV_ICONS = {
    'Normal':   '✅', 'Mild':    '⚠️',
    'Moderate': '🔶', 'Severe':  '🚨', 'Unknown': '❓'
}
SEV_MESSAGES = {
    'Normal': (
        "Great news! Your test results are within normal range.",
        "No immediate medical attention required.",
        "Continue your current health routine and schedule your next regular check-up.",
        "You do NOT need to revisit the hospital for this report."
    ),
    'Mild': (
        "Your results show mild findings that need monitoring.",
        "No emergency intervention required at this time.",
        "Please follow up with your doctor within 2-4 weeks.",
        "You may consult your doctor via phone before visiting."
    ),
    'Moderate': (
        "Your results indicate moderate severity findings.",
        "A follow-up visit with your specialist is recommended.",
        "Please book an appointment within the next 7-10 days.",
        "Bring this report to your next appointment."
    ),
    'Severe': (
        "Your results indicate findings that require prompt attention.",
        "Please contact your doctor or visit the hospital soon.",
        "Do not delay — early treatment leads to better outcomes.",
        "Your doctor has been notified and will contact you."
    ),
    'Unknown': (
        "Your report has been reviewed by your doctor.",
        "Please contact your doctor for detailed interpretation.",
        "Schedule a follow-up appointment at your earliest convenience.",
        "Your doctor will guide you on next steps."
    ),
    'Processing': (
        "Your report is being processed.",
        "Please check back shortly.",
        "Contact your doctor if you have urgent concerns.",
        "No action required at this time."
    )
}


def render():
    st.markdown("""
    <div style="background:#0D1621;border:1px solid #1E293B;
                border-radius:12px;padding:20px 28px;margin-bottom:24px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;
                    color:#F0F4FF;">📋 My Report</div>
        <div style="font-size:12px;color:#64748B;margin-top:4px;
                    font-family:'IBM Plex Mono',monospace;">
            Check your approved medical report · No hospital visit needed
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Patient ID lookup
    col1, col2 = st.columns([2, 1])
    with col1:
        # Pre-fill if coming from patient portal
        default_id = st.session_state.get('patient_lookup', '')
        pid_input  = st.text_input(
            'Enter your Patient ID',
            value=default_id,
            placeholder='e.g. PT-123456',
            key='result_pid_input'
        )
    with col2:
        st.markdown('<br>', unsafe_allow_html=True)
        check_btn = st.button('🔍 Get My Report',
                              use_container_width=True,
                              type='primary')

    if not pid_input:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:40px;margin-bottom:12px;">📋</div>
            <div style="font-size:14px;color:#64748B;">
                Enter your Patient ID above to view your report.<br>
                Your ID was given when you registered.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    pid = pid_input.strip()

    if pid not in st.session_state.patients:
        st.error('❌ Patient ID not found. Please check your ID.')
        return

    p      = st.session_state.patients[pid]
    status = p.get('status', 'PENDING')

    if status == 'PENDING':
        st.markdown(f"""
        <div style="background:#0D1621;border:1px solid #F59E0B;
                    border-radius:12px;padding:28px;text-align:center;">
            <div style="font-size:36px;margin-bottom:12px;">⏳</div>
            <div style="font-size:16px;font-weight:600;color:#F0F4FF;
                        margin-bottom:8px;">Report Pending Review</div>
            <div style="font-size:13px;color:#64748B;margin-bottom:16px;">
                Your doctor <b style="color:#F0F4FF;">
                {p.get('doctor_name','')}</b> is reviewing your report.<br>
                You will be notified once it's approved.
            </div>
            <div style="background:#1A1400;border:1px solid #F59E0B;
                        border-radius:8px;padding:12px 20px;
                        display:inline-block;font-size:12px;color:#F59E0B;
                        font-family:'IBM Plex Mono',monospace;">
                No need to visit the hospital — we'll notify you here!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if status == 'REJECTED':
        st.markdown(f"""
        <div style="background:#0D1621;border:1px solid #EF4444;
                    border-radius:12px;padding:28px;text-align:center;">
            <div style="font-size:36px;margin-bottom:12px;">❌</div>
            <div style="font-size:16px;font-weight:600;color:#F0F4FF;
                        margin-bottom:8px;">Report Requires Manual Review</div>
            <div style="font-size:13px;color:#64748B;">
                Your doctor has flagged this report for manual review.<br>
                Please contact <b style="color:#F0F4FF;">
                {p.get('doctor_name','')}</b> directly.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── APPROVED — Show full report ───────────────────────────
    fus_lbl  = p.get('fusion_label', 'Unknown')
    fus_clr  = SEV_COLORS.get(fus_lbl, '#94A3B8')
    fus_icon = SEV_ICONS.get(fus_lbl, '❓')
    msgs     = SEV_MESSAGES.get(fus_lbl, SEV_MESSAGES.get('Unknown', ('Report reviewed.','Contact your doctor.','Schedule follow-up.','No revisit needed.')))

    # Big result card
    bg_clr = {
        'Normal':   '#0D2818', 'Mild':    '#1A1400',
        'Moderate': '#1A0E00', 'Severe':  '#1A0808', 'Unknown': '#0D1621'
    }.get(fus_lbl, '#0D1621')

    st.markdown(f"""
    <div style="background:{bg_clr};border:2px solid {fus_clr};
                border-radius:16px;padding:32px;text-align:center;
                margin-bottom:24px;">
        <div style="font-size:52px;margin-bottom:12px;">{fus_icon}</div>
        <div style="font-family:'Playfair Display',serif;font-size:28px;
                    color:#F0F4FF;margin-bottom:6px;">
            Your Report is Ready
        </div>
        <div style="font-size:14px;color:#94A3B8;margin-bottom:20px;">
            Patient: <b style="color:#F0F4FF;">{p.get('name','')}</b> ·
            ID: <b style="color:#F0F4FF;">{pid}</b>
        </div>
        <div style="display:inline-block;background:rgba(0,0,0,.3);
                    border:2px solid {fus_clr};border-radius:50px;
                    padding:10px 32px;margin-bottom:20px;">
            <span style="font-size:22px;font-weight:700;color:{fus_clr};
                         font-family:'IBM Plex Mono',monospace;">
                {fus_lbl.upper()}
            </span>
        </div>
        <div style="max-width:500px;margin:0 auto;">
            <div style="font-size:15px;color:#F0F4FF;margin-bottom:8px;
                        font-weight:500;">{msgs[0]}</div>
            <div style="font-size:13px;color:#94A3B8;margin-bottom:6px;">
                {msgs[1]}
            </div>
            <div style="font-size:13px;color:{fus_clr};margin-bottom:6px;">
                📅 {msgs[2]}
            </div>
            <div style="font-size:12px;color:#64748B;
                        font-family:'IBM Plex Mono',monospace;
                        margin-top:10px;">
                {msgs[3]}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Details + SMS simulation
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:14px;">── Report Details</div>
        """, unsafe_allow_html=True)

        # Score breakdown
        score_items = [
            ('🧪 Lab Score',  p.get('lab_score'),
             p.get('lab_severity_label', 'N/A')),
            ('🧠 CT Score',   p.get('ct_score'),
             p.get('ct_severity_label', 'N/A')),
            ('🔬 US Score',   p.get('us_score'),
             p.get('us_severity_label', 'N/A')),
        ]
        for lbl, score, sev in score_items:
            if score is not None:
                clr = SEV_COLORS.get(sev, '#94A3B8')
                st.markdown(f"""
                <div style="background:#0D1621;border:1px solid #1E293B;
                            border-left:3px solid {clr};border-radius:6px;
                            padding:10px 14px;margin-bottom:6px;
                            display:flex;justify-content:space-between;
                            align-items:center;">
                    <div style="font-size:13px;color:#94A3B8;">{lbl}</div>
                    <div style="font-size:13px;color:{clr};font-weight:500;">
                        {sev}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Doctor info
        st.markdown(f"""
        <div style="background:#0D1621;border:1px solid #1E293B;
                    border-radius:8px;padding:14px 18px;margin-top:10px;">
            <div style="font-size:11px;color:#64748B;
                        font-family:'IBM Plex Mono',monospace;
                        margin-bottom:8px;">REVIEWED BY</div>
            <div style="font-size:14px;color:#F0F4FF;font-weight:500;">
                {p.get('reviewed_by', p.get('doctor_name',''))}
            </div>
            <div style="font-size:12px;color:#64748B;margin-top:2px;">
                Approved: {p.get('reviewed_at','')[:16]}
            </div>
            {('<div style="margin-top:8px;padding-top:8px;'
              'border-top:1px solid #1E293B;font-size:12px;'
              'color:#94A3B8;font-style:italic;">'
              + p.get("doctor_notes","") + '</div>')
             if p.get("doctor_notes") else ''}
        </div>
        """, unsafe_allow_html=True)

        # Full clinical report
        if p.get('final_report'):
            st.markdown("""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                        color:#3B82F6;letter-spacing:.1em;
                        text-transform:uppercase;padding-bottom:6px;
                        border-bottom:1px solid #1E293B;margin:14px 0 10px;">
                ── Clinical Report
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#0A0D14;border:1px solid #1E293B;
                        border-radius:8px;padding:14px 18px;
                        font-size:12px;line-height:1.8;color:#94A3B8;
                        white-space:pre-wrap;">
{p.get('final_report','')}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # SMS simulation
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:8px;border-bottom:1px solid #1E293B;
                    margin-bottom:14px;">── SMS Notification</div>
        """, unsafe_allow_html=True)

        sms_text = (
            f"[MedAI Hospital]\n\n"
            f"Dear {p.get('name','Patient')},\n\n"
            f"Your medical report is ready.\n\n"
            f"Result: {fus_lbl.upper()} {fus_icon}\n\n"
            f"{msgs[0]}\n\n"
            f"{msgs[2]}\n\n"
            f"Doctor: {p.get('reviewed_by', p.get('doctor_name',''))}\n"
            f"Patient ID: {pid}\n\n"
            f"View full report at:\n"
            f"medai-hospital.streamlit.app\n\n"
            f"MedAI - Doctor-in-the-Loop System"
        )

        # Phone mockup
        st.markdown(f"""
        <div style="display:flex;justify-content:center;">
        <div style="background:#1A1A2E;border:2px solid #2A2A4A;
                    border-radius:24px;padding:20px;width:240px;
                    box-shadow:0 0 30px rgba(59,130,246,.1);">

            <!-- Phone top -->
            <div style="text-align:center;margin-bottom:12px;">
                <div style="background:#2A2A4A;height:4px;width:40px;
                            border-radius:2px;margin:0 auto 8px;"></div>
                <div style="font-size:10px;color:#475569;
                            font-family:'IBM Plex Mono',monospace;">
                    {p.get('phone','+91 XXXXXXXXXX')}
                </div>
                <div style="font-size:9px;color:#334155;">
                    {datetime.now().strftime('%H:%M')}
                </div>
            </div>

            <!-- SMS bubble -->
            <div style="background:#0D4A1F;border:1px solid #10B981;
                        border-radius:12px 12px 12px 0;
                        padding:12px;margin-bottom:6px;">
                <div style="font-size:9px;color:#10B981;margin-bottom:6px;
                            font-family:'IBM Plex Mono',monospace;">
                    MedAI Hospital
                </div>
                <div style="font-size:10px;color:#D1FAE5;
                            white-space:pre-wrap;line-height:1.5;">
{sms_text}
                </div>
            </div>

            <!-- Delivered indicator -->
            <div style="text-align:right;font-size:9px;color:#334155;
                        font-family:'IBM Plex Mono',monospace;">
                ✓✓ Delivered
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        # Simulate send button
        if st.button('📱 Simulate SMS Send',
                     use_container_width=True):
            with st.spinner('Sending SMS...'):
                time.sleep(1.5)
            st.success(
                f'✅ SMS sent to {p.get("phone","patient")}!'
            )

    # Footer message
    st.markdown(f"""
    <div style="background:#0A1628;border:1px solid #1E3A5F;
                border-radius:10px;padding:16px 20px;margin-top:20px;
                text-align:center;">
        <div style="font-size:14px;color:#F0F4FF;margin-bottom:4px;">
            🏥 Thank you for using MedAI Hospital System
        </div>
        <div style="font-size:12px;color:#64748B;">
            Your health is our priority.
            This report was reviewed and approved by
            <b style="color:#3B82F6;">
            {p.get('reviewed_by', p.get('doctor_name','your doctor'))}
            </b>.
            <br>For any concerns, please contact your doctor directly.
        </div>
    </div>
    """, unsafe_allow_html=True)
