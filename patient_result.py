import streamlit as st
from datetime import datetime
import time
from utils import SEV_COLORS, SEV_BG, SEV_ICON

SEV_HEADLINE = {
    'Normal':   'Your results are normal',
    'Mild':     'Your results show mild findings',
    'Moderate': 'Your results need attention',
    'Severe':   'Your results require urgent care',
    'Unknown':  'Your report is ready',
}
SEV_MESSAGE = {
    'Normal': (
        'Good news — your test results are within the normal range.',
        'No immediate medical attention is required at this time.',
        'Follow your doctor\'s prescription and attend your next scheduled check-up.',
        'You do not need to revisit the hospital for this report.'
    ),
    'Mild': (
        'Your results show mild findings that need to be monitored.',
        'There is no emergency, but a follow-up is recommended.',
        'Please follow your doctor\'s prescription and contact them if symptoms worsen.',
        'You may be able to discuss your results by phone before visiting.'
    ),
    'Moderate': (
        'Your results indicate findings that need medical attention.',
        'Please follow your doctor\'s instructions carefully.',
        'Book a follow-up appointment within the next 7 to 10 days.',
        'Bring this report to your next appointment.'
    ),
    'Severe': (
        'Your results indicate findings that need prompt attention.',
        'Please follow your doctor\'s instructions without delay.',
        'Contact your doctor today or visit the hospital if you feel unwell.',
        'Early treatment leads to the best outcomes.'
    ),
    'Unknown': (
        'Your report has been reviewed and approved by your doctor.',
        'Please follow your doctor\'s prescription carefully.',
        'Contact your doctor if you have any questions.',
        'Your doctor will guide you on next steps.'
    ),
}


def render():
    st.markdown(
        '<div style="font-size:26px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;margin-bottom:4px;">My Report</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:20px;">'
        'View your doctor-approved report and health status</div>',
        unsafe_allow_html=True
    )

    # Lookup
    col1, col2 = st.columns([3, 1])
    with col1:
        default   = st.session_state.get('patient_lookup', '')
        pid_input = st.text_input(
            'Your Patient Reference Number',
            value=default,
            placeholder='Enter your reference number (e.g. 24992831)',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('<br>', unsafe_allow_html=True)
        st.button('Find My Report', use_container_width=True,
                  type='primary', key='find_report')

    if not pid_input:
        st.markdown(
            '<div style="background:#111827;border:2px dashed #1E2D40;'
            'border-radius:12px;padding:64px;text-align:center;margin-top:20px;">'
            '<div style="font-size:40px;margin-bottom:16px;">🔍</div>'
            '<div style="font-size:16px;font-weight:500;color:#F1F5F9;'
            'margin-bottom:8px;">Enter your reference number above</div>'
            '<div style="font-size:14px;color:#64748B;">'
            'Your reference number was given when you registered at the hospital.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    pid = pid_input.strip()

    if pid not in st.session_state.patients:
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.08);'
            f'border:1px solid rgba(239,68,68,0.2);border-radius:12px;'
            f'padding:24px;margin-top:16px;">'
            f'<div style="font-size:16px;font-weight:600;color:#EF4444;'
            f'margin-bottom:8px;">Reference number not found</div>'
            f'<div style="font-size:14px;color:#94A3B8;">'
            f'We could not find a record for '
            f'<b style="color:#F1F5F9;font-family:monospace;">{pid}</b>. '
            f'Please check the number and try again.</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        return

    p      = st.session_state.patients[pid]
    status = p.get('status', 'PENDING')

    # Pending
    if status == 'PENDING':
        st.markdown(
            f'<div style="background:rgba(245,158,11,0.08);'
            f'border:1px solid rgba(245,158,11,0.2);'
            f'border-radius:16px;padding:40px;text-align:center;margin-top:16px;">'
            f'<div style="font-size:40px;margin-bottom:16px;">⏳</div>'
            f'<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
            f'margin-bottom:10px;">Your report is being reviewed</div>'
            f'<div style="font-size:15px;color:#94A3B8;margin-bottom:20px;">'
            f'Dr. <b style="color:#F1F5F9;">{p.get("doctor_name","")}</b> '
            f'is currently reviewing your results.</div>'
            f'<div style="background:rgba(245,158,11,0.1);'
            f'border:1px solid rgba(245,158,11,0.25);'
            f'border-radius:10px;padding:12px 24px;display:inline-block;'
            f'font-size:14px;color:#F59E0B;font-weight:500;">'
            f'You will be notified once approved — '
            f'no need to visit the hospital</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        return

    # Rejected
    if status == 'REJECTED':
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.08);'
            f'border:1px solid rgba(239,68,68,0.2);'
            f'border-radius:16px;padding:40px;text-align:center;margin-top:16px;">'
            f'<div style="font-size:40px;margin-bottom:16px;">📞</div>'
            f'<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
            f'margin-bottom:10px;">Please contact your doctor</div>'
            f'<div style="font-size:15px;color:#94A3B8;">'
            f'Your doctor has reviewed your report and would like to '
            f'discuss the findings with you directly.<br><br>'
            f'Please contact <b style="color:#F1F5F9;">'
            f'{p.get("doctor_name","your doctor")}</b> at your earliest convenience.'
            f'</div></div>',
            unsafe_allow_html=True
        )
        return

    # ── APPROVED ─────────────────────────────────────────────
    fus      = p.get('fusion_label', p.get('severity_label','Unknown'))
    fus_clr  = SEV_COLORS.get(fus, '#94A3B8')
    fus_bg   = SEV_BG.get(fus, 'rgba(148,163,184,0.08)')
    icon     = SEV_ICON.get(fus, '📋')
    headline = SEV_HEADLINE.get(fus, 'Your report is ready')
    msgs     = SEV_MESSAGE.get(fus, SEV_MESSAGE['Unknown'])

    # Main result card
    st.markdown(
        f'<div style="background:{fus_bg};border:2px solid {fus_clr}33;'
        f'border-radius:20px;padding:36px 48px;text-align:center;'
        f'margin:16px 0 28px;">'
        f'<div style="font-size:52px;margin-bottom:14px;">{icon}</div>'
        f'<div style="font-size:28px;font-weight:700;color:#F1F5F9;'
        f'letter-spacing:-0.5px;margin-bottom:10px;">{headline}</div>'
        f'<div style="font-size:15px;color:#94A3B8;margin-bottom:22px;">'
        f'Reference: <b style="color:#F1F5F9;font-family:monospace;">{pid}</b>'
        f'  ·  {p.get("name","")}</div>'
        f'<div style="background:{fus_bg};border:2px solid {fus_clr}55;'
        f'border-radius:50px;padding:10px 36px;display:inline-block;'
        f'margin-bottom:24px;">'
        f'<span style="font-size:22px;font-weight:700;color:{fus_clr};">'
        f'{fus}</span></div>'
        f'<div style="max-width:560px;margin:0 auto;text-align:left;'
        f'background:rgba(0,0,0,0.2);border-radius:12px;padding:22px 26px;">'
        f'<div style="font-size:15px;color:#F1F5F9;font-weight:500;'
        f'margin-bottom:10px;line-height:1.5;">{msgs[0]}</div>'
        f'<div style="font-size:14px;color:#94A3B8;margin-bottom:8px;'
        f'line-height:1.6;">{msgs[1]}</div>'
        f'<div style="font-size:14px;color:{fus_clr};margin-bottom:8px;'
        f'line-height:1.6;font-weight:500;">📅 {msgs[2]}</div>'
        f'<div style="font-size:13px;color:#64748B;padding-top:10px;'
        f'border-top:1px solid rgba(255,255,255,0.06);line-height:1.6;">'
        f'{msgs[3]}</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    dc1, dc2 = st.columns([3, 2])

    with dc1:
        # Prescription from doctor
        prescription = p.get('prescription','')
        if prescription:
            st.markdown(
                '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
                'margin-bottom:12px;">Doctor\'s Prescription</div>',
                unsafe_allow_html=True
            )
            rx_lines = prescription.strip().split('\n')
            rx_html  = ''.join(
                [f'<div style="display:flex;gap:10px;padding:8px 0;'
                 f'border-bottom:1px solid #1E2D40;">'
                 f'<span style="color:#3B82F6;font-weight:600;'
                 f'flex-shrink:0;">{i+1}.</span>'
                 f'<span style="font-size:14px;color:#E2E8F0;">{line.strip()}</span>'
                 f'</div>'
                 for i, line in enumerate(rx_lines) if line.strip()]
            )
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-left:4px solid #3B82F6;border-radius:10px;'
                f'padding:16px 20px;margin-bottom:16px;">'
                f'{rx_html}</div>',
                unsafe_allow_html=True
            )

        # Doctor notes
        if p.get('doctor_notes'):
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-radius:10px;padding:14px 18px;margin-bottom:14px;">'
                f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
                f'letter-spacing:0.06em;margin-bottom:6px;">Doctor\'s Note</div>'
                f'<div style="font-size:14px;color:#94A3B8;font-style:italic;">'
                f'"{p.get("doctor_notes","")}"</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Approved by
        st.markdown(
            f'<div style="background:#111827;border:1px solid #1E2D40;'
            f'border-radius:10px;padding:16px 18px;margin-bottom:14px;">'
            f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
            f'letter-spacing:0.06em;margin-bottom:6px;">Reviewed & Approved by</div>'
            f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;">'
            f'{p.get("reviewed_by", p.get("doctor_name",""))}</div>'
            f'<div style="font-size:13px;color:#64748B;margin-top:3px;">'
            f'{p.get("reviewed_at","")[:16]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Full clinical report (collapsible)
        if p.get('final_report'):
            with st.expander('📄  View Full Clinical Report'):
                st.markdown(
                    f'<div style="background:#0B1120;border-radius:8px;'
                    f'padding:16px;font-size:13px;line-height:1.8;'
                    f'color:#94A3B8;white-space:pre-wrap;">'
                    f'{p.get("final_report","")}</div>',
                    unsafe_allow_html=True
                )

    with dc2:
        # SMS notification preview
        st.markdown(
            '<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
            'margin-bottom:12px;">Notification Preview</div>',
            unsafe_allow_html=True
        )

        rx_short = p.get('prescription','').split('\n')[0] \
                   if p.get('prescription') else msgs[2]

        sms = (
            f"[MedAI Hospital]\n\n"
            f"Dear {p.get('name','Patient')},\n\n"
            f"Your medical report is ready.\n\n"
            f"Result: {fus} {icon}\n\n"
            f"{msgs[0]}\n\n"
            f"Doctor: {p.get('reviewed_by', p.get('doctor_name',''))}\n\n"
            f"Prescription:\n{rx_short}\n\n"
            f"Ref: {pid}\n\n"
            f"View full report:\nmedai.streamlit.app\n\n"
            f"MedAI Clinical System"
        )

        st.markdown(
            f'<div style="display:flex;justify-content:center;">'
            f'<div style="background:#1A1A2E;border:2px solid #2A2A4A;'
            f'border-radius:28px;padding:20px 16px;width:260px;">'
            f'<div style="text-align:center;margin-bottom:14px;">'
            f'<div style="background:#2A2A4A;height:4px;width:40px;'
            f'border-radius:2px;margin:0 auto 8px;"></div>'
            f'<div style="font-size:11px;color:#64748B;">'
            f'{p.get("phone","Not provided")}</div>'
            f'<div style="font-size:10px;color:#334155;">'
            f'{datetime.now().strftime("%H:%M")}</div></div>'
            f'<div style="background:rgba(16,185,129,0.12);'
            f'border:1px solid rgba(16,185,129,0.25);'
            f'border-radius:14px 14px 14px 0;padding:14px;">'
            f'<div style="font-size:10px;color:#10B981;font-weight:600;'
            f'margin-bottom:8px;">MedAI Hospital</div>'
            f'<div style="font-size:11px;color:#D1FAE5;'
            f'white-space:pre-wrap;line-height:1.6;">{sms}</div>'
            f'</div>'
            f'<div style="text-align:right;font-size:10px;color:#334155;'
            f'margin-top:6px;">✓✓ Delivered</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('📱  Send SMS Notification',
                     use_container_width=True,
                     type='primary', key='send_sms'):
            with st.spinner('Sending...'):
                time.sleep(1.5)
            st.success(f'✅  SMS sent to {p.get("phone","patient")}!')

    st.markdown(
        f'<div style="background:#111827;border:1px solid #1E2D40;'
        f'border-radius:12px;padding:18px 24px;text-align:center;margin-top:24px;">'
        f'<div style="font-size:15px;color:#F1F5F9;font-weight:500;margin-bottom:6px;">'
        f'Thank you for using MedAI Clinical System</div>'
        f'<div style="font-size:13px;color:#64748B;">'
        f'This report was reviewed and approved by '
        f'<b style="color:#94A3B8;">'
        f'{p.get("reviewed_by", p.get("doctor_name","your doctor"))}</b>. '
        f'For any questions, please contact your doctor directly.</div>'
        f'</div>',
        unsafe_allow_html=True
    )
