import streamlit as st
from datetime import datetime
import time
from utils import SEV_COLOR, SEV_BG, SEV_ICON

SEV_HEADLINE = {
    'Normal':   'Your results are normal',
    'Mild':     'Your results show mild findings',
    'Moderate': 'Your results need attention',
    'Severe':   'Your results require urgent care',
    'Unknown':  'Your report is ready',
}
SEV_MSG = {
    'Normal': [
        'Good news — your test results are within the normal healthy range.',
        'No immediate medical attention is required at this time.',
        'Follow your doctor\'s prescription and attend your next routine check-up.',
        'You do not need to revisit the hospital for this report.',
    ],
    'Mild': [
        'Your results show mild findings that need to be monitored.',
        'There is no emergency, but a follow-up visit is recommended.',
        'Follow your doctor\'s prescription carefully.',
        'Contact your doctor if symptoms worsen before your next appointment.',
    ],
    'Moderate': [
        'Your results indicate findings that need medical attention.',
        'Please follow your doctor\'s instructions carefully.',
        'Book a follow-up appointment within the next 7 to 10 days.',
        'Bring this report to your next appointment.',
    ],
    'Severe': [
        'Your results indicate findings that need prompt medical attention.',
        'Please follow your doctor\'s instructions without delay.',
        'Contact your doctor today or visit the hospital if you feel unwell.',
        'Early treatment leads to the best outcomes.',
    ],
    'Unknown': [
        'Your report has been reviewed and approved by your doctor.',
        'Please follow your doctor\'s prescription carefully.',
        'Contact your doctor if you have any questions.',
        'Your doctor will guide you on next steps.',
    ],
}


def render():
    st.markdown(
        '<div style="font-size:28px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.7px;margin-bottom:6px;">My Report</div>'
        '<div style="font-size:16px;color:#7A90A8;margin-bottom:24px;">'
        'View your doctor-approved report, prescription and health status</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        default   = st.session_state.get('patient_lookup','')
        pid_input = st.text_input(
            'Reference Number',
            value=default,
            placeholder='Enter your patient reference number...',
            label_visibility='collapsed'
        )
    with col2:
        st.markdown('<br>', unsafe_allow_html=True)
        st.button('Find My Report', use_container_width=True,
                  type='primary', key='find_report')

    if not pid_input:
        st.markdown(
            '<div style="background:#112033;border:2px dashed #1E3250;'
            'border-radius:14px;padding:72px;text-align:center;margin-top:24px;">'
            '<div style="font-size:48px;margin-bottom:18px;">🔍</div>'
            '<div style="font-size:20px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:10px;">Enter your reference number above</div>'
            '<div style="font-size:15px;color:#7A90A8;">'
            'Your reference number was given to you when you registered '
            'at the hospital or submitted your test online.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    pid = pid_input.strip()

    if pid not in st.session_state.patients:
        st.markdown(
            '<div style="background:rgba(255,59,59,0.08);'
            'border:1.5px solid rgba(255,59,59,0.25);border-radius:12px;'
            'padding:24px 28px;margin-top:16px;">'
            '<div style="font-size:17px;font-weight:700;color:#FF3B3B;'
            'margin-bottom:8px;">Reference number not found</div>'
            '<div style="font-size:15px;color:#7A90A8;">'
            'We could not find a record for '
            '<b style="color:#F0F6FF;font-family:monospace;">' + pid + '</b>. '
            'Please check the number and try again, or contact the hospital.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    p      = st.session_state.patients[pid]
    status = p.get('status','PENDING')

    if status == 'PENDING':
        st.markdown(
            '<div style="background:rgba(255,184,0,0.08);'
            'border:1.5px solid rgba(255,184,0,0.25);'
            'border-radius:16px;padding:48px;text-align:center;margin-top:16px;">'
            '<div style="font-size:52px;margin-bottom:18px;">⏳</div>'
            '<div style="font-size:24px;font-weight:800;color:#F0F6FF;'
            'margin-bottom:12px;">Your report is being reviewed</div>'
            '<div style="font-size:16px;color:#7A90A8;margin-bottom:24px;">'
            'Dr. <b style="color:#F0F6FF;">' +
            p.get('doctor_name','') + '</b> is currently reviewing your results.</div>'
            '<div style="background:rgba(255,184,0,0.12);'
            'border:1.5px solid rgba(255,184,0,0.3);border-radius:10px;'
            'padding:14px 28px;display:inline-block;font-size:15px;'
            'color:#FFB800;font-weight:600;">'
            'You will be notified once approved — no hospital visit needed</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    if status == 'REJECTED':
        st.markdown(
            '<div style="background:rgba(255,59,59,0.08);'
            'border:1.5px solid rgba(255,59,59,0.25);'
            'border-radius:16px;padding:48px;text-align:center;margin-top:16px;">'
            '<div style="font-size:52px;margin-bottom:18px;">📞</div>'
            '<div style="font-size:24px;font-weight:800;color:#F0F6FF;'
            'margin-bottom:12px;">Please contact your doctor</div>'
            '<div style="font-size:16px;color:#7A90A8;">'
            'Your doctor has reviewed your report and would like to '
            'discuss the findings with you directly.<br><br>'
            'Please contact <b style="color:#F0F6FF;">' +
            p.get('doctor_name','your doctor') + '</b> at your earliest convenience.'
            '</div></div>',
            unsafe_allow_html=True
        )
        return

    # ── APPROVED ─────────────────────────────────────────────
    fus      = p.get('fusion_label', p.get('severity_label','Unknown'))
    fus_clr  = SEV_COLOR.get(fus,'#8892A4')
    fus_bg   = SEV_BG.get(fus,'rgba(136,146,164,0.08)')
    icon     = SEV_ICON.get(fus,'📋')
    headline = SEV_HEADLINE.get(fus,'Your report is ready')
    msgs     = SEV_MSG.get(fus, SEV_MSG['Unknown'])

    # Big result hero card
    st.markdown(
        '<div style="background:' + fus_bg + ';border:2px solid ' + fus_clr + '33;'
        'border-radius:20px;padding:44px 56px;text-align:center;margin:16px 0 32px;">'
        '<div style="font-size:60px;margin-bottom:16px;">' + icon + '</div>'
        '<div style="font-size:32px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-0.8px;margin-bottom:12px;">' + headline + '</div>'
        '<div style="font-size:16px;color:#7A90A8;margin-bottom:24px;">'
        'Patient: <b style="color:#F0F6FF;">' + p.get('name','') + '</b>  ·  '
        'Ref: <b style="color:#F0F6FF;font-family:monospace;">' + pid + '</b>'
        '</div>'
        '<div style="background:' + fus_bg + ';border:2.5px solid ' + fus_clr + '66;'
        'border-radius:50px;padding:14px 44px;display:inline-block;margin-bottom:30px;">'
        '<span style="font-size:28px;font-weight:800;color:' + fus_clr + ';'
        'letter-spacing:-0.5px;">' + fus + '</span>'
        '</div>'
        '<div style="max-width:600px;margin:0 auto;text-align:left;'
        'background:rgba(0,0,0,0.2);border-radius:14px;padding:26px 30px;">'
        '<div style="font-size:17px;color:#F0F6FF;font-weight:600;'
        'margin-bottom:12px;line-height:1.5;">' + msgs[0] + '</div>'
        '<div style="font-size:15px;color:#94A3B8;margin-bottom:10px;line-height:1.7;">'
        + msgs[1] + '</div>'
        '<div style="font-size:15px;color:' + fus_clr + ';margin-bottom:10px;'
        'line-height:1.7;font-weight:600;">📅 ' + msgs[2] + '</div>'
        '<div style="font-size:14px;color:#4A6080;padding-top:12px;'
        'border-top:1px solid rgba(255,255,255,0.06);line-height:1.7;">'
        + msgs[3] + '</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    # Details + SMS
    dc1, dc2 = st.columns([3, 2])

    with dc1:
        # Prescription
        prescription = p.get('prescription','')
        if prescription:
            st.markdown(
                '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:14px;">Doctor\'s Prescription</div>',
                unsafe_allow_html=True
            )
            rx_lines = [l.strip() for l in prescription.strip().split('\n')
                        if l.strip()]
            rx_html  = ''.join([
                '<div style="display:flex;gap:12px;padding:12px 0;'
                'border-bottom:1px solid #1E3250;">'
                '<span style="color:#2563EB;font-weight:700;font-size:16px;'
                'flex-shrink:0;min-width:24px;">' + str(i+1) + '.</span>'
                '<span style="font-size:15px;color:#E8EDF5;line-height:1.5;">'
                + line + '</span>'
                '</div>'
                for i, line in enumerate(rx_lines)
            ])
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-left:5px solid #2563EB;border-radius:12px;'
                'padding:18px 22px;margin-bottom:18px;">'
                + rx_html + '</div>',
                unsafe_allow_html=True
            )

        # Doctor notes
        if p.get('doctor_notes'):
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:16px 20px;margin-bottom:16px;">'
                '<div style="font-size:12px;font-weight:600;color:#4A6080;'
                'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">'
                'Doctor\'s Note</div>'
                '<div style="font-size:15px;color:#94A3B8;font-style:italic;'
                'line-height:1.6;">"' + p.get('doctor_notes','') + '"</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # Approved by
        st.markdown(
            '<div style="background:#112033;border:1.5px solid #1E3250;'
            'border-radius:10px;padding:16px 20px;margin-bottom:16px;">'
            '<div style="font-size:12px;font-weight:600;color:#4A6080;'
            'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">'
            'Reviewed & Approved by</div>'
            '<div style="font-size:17px;font-weight:700;color:#F0F6FF;">'
            + p.get('reviewed_by', p.get('doctor_name','')) + '</div>'
            '<div style="font-size:14px;color:#7A90A8;margin-top:4px;">'
            + p.get('reviewed_at','')[:16] + '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # Full report
        if p.get('final_report'):
            with st.expander('📄  View Full Clinical Report'):
                st.markdown(
                    '<div style="background:#0D1B2E;border-radius:10px;'
                    'padding:18px 22px;font-size:14px;line-height:1.85;'
                    'color:#94A3B8;white-space:pre-wrap;">'
                    + p.get('final_report','') + '</div>',
                    unsafe_allow_html=True
                )

    with dc2:
        st.markdown(
            '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
            'margin-bottom:14px;">SMS Notification</div>',
            unsafe_allow_html=True
        )

        rx_short = (p.get('prescription','').split('\n')[0]
                    if p.get('prescription') else msgs[2])

        sms = (
            '[MedAI Hospital]\n\n'
            'Dear ' + p.get('name','Patient') + ',\n\n'
            'Your medical report is ready.\n\n'
            'Result: ' + fus + ' ' + icon + '\n\n'
            + msgs[0] + '\n\n'
            'Prescription:\n' + rx_short + '\n\n'
            'Doctor: ' + p.get('reviewed_by', p.get('doctor_name','')) + '\n'
            'Ref: ' + str(pid) + '\n\n'
            'View report:\nmedai.streamlit.app\n\n'
            'MedAI Clinical System'
        )

        st.markdown(
            '<div style="display:flex;justify-content:center;">'
            '<div style="background:#0A1628;border:2px solid #1E3250;'
            'border-radius:28px;padding:22px 18px;width:270px;">'
            '<div style="text-align:center;margin-bottom:16px;">'
            '<div style="background:#1E3250;height:4px;width:44px;'
            'border-radius:2px;margin:0 auto 10px;"></div>'
            '<div style="font-size:12px;color:#4A6080;font-weight:500;">'
            + p.get('phone','Not provided') + '</div>'
            '<div style="font-size:11px;color:#263A55;margin-top:2px;">'
            + datetime.now().strftime('%H:%M') + '</div>'
            '</div>'
            '<div style="background:rgba(0,196,140,0.1);'
            'border:1.5px solid rgba(0,196,140,0.25);'
            'border-radius:16px 16px 16px 0;padding:16px;">'
            '<div style="font-size:11px;color:#00C48C;font-weight:700;'
            'margin-bottom:10px;letter-spacing:0.05em;">MedAI Hospital</div>'
            '<div style="font-size:12px;color:#D1FAE5;'
            'white-space:pre-wrap;line-height:1.7;">' + sms + '</div>'
            '</div>'
            '<div style="text-align:right;font-size:11px;color:#263A55;'
            'margin-top:8px;">✓✓ Delivered</div>'
            '</div></div>',
            unsafe_allow_html=True
        )

        st.markdown('<br>', unsafe_allow_html=True)
        if st.button('📱  Send SMS Notification',
                     use_container_width=True,
                     type='primary', key='send_sms'):
            with st.spinner('Sending...'):
                time.sleep(1.5)
            st.success('✅  SMS sent to ' + p.get('phone','patient') + '!')

    # Footer
    st.markdown(
        '<div style="background:#112033;border:1.5px solid #1E3250;'
        'border-radius:14px;padding:22px 28px;text-align:center;margin-top:28px;">'
        '<div style="font-size:16px;color:#F0F6FF;font-weight:600;'
        'margin-bottom:6px;">Thank you for using MedAI Clinical System</div>'
        '<div style="font-size:14px;color:#7A90A8;">'
        'This report was reviewed and approved by '
        '<b style="color:#94A3B8;">' +
        p.get('reviewed_by', p.get('doctor_name','your doctor')) + '</b>. '
        'For any questions, please contact your doctor directly.</div>'
        '</div>',
        unsafe_allow_html=True
    )
