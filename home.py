import streamlit as st
from utils import SEV_COLOR, load_lab, load_ct, load_us, load_fusion


def render():
    # Hero banner
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0F2444 0%,#0D1B2E 60%,'
        '#152338 100%);border:1.5px solid #1E3250;border-radius:16px;'
        'padding:40px 48px;margin-bottom:32px;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;">'
        '<div style="max-width:580px;">'
        '<div style="font-size:13px;font-weight:600;color:#4A9EFF;'
        'letter-spacing:0.12em;text-transform:uppercase;margin-bottom:12px;">'
        'Doctor-in-the-Loop AI System</div>'
        '<div style="font-size:36px;font-weight:800;color:#F0F6FF;'
        'letter-spacing:-1px;line-height:1.15;margin-bottom:16px;">'
        'AI-Powered Clinical<br>Report Generation</div>'
        '<div style="font-size:16px;color:#7A90A8;line-height:1.7;'
        'margin-bottom:28px;">'
        'Multimodal medical AI that analyses lab reports, CT scans and '
        'ultrasounds — automatically routes findings to your doctor for '
        'review and approval. Results delivered without a hospital visit.</div>'
        '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
        '<span style="background:rgba(74,158,255,0.15);border:1.5px solid '
        'rgba(74,158,255,0.3);color:#4A9EFF;font-size:13px;font-weight:600;'
        'padding:6px 16px;border-radius:20px;">🧪 Lab Reports</span>'
        '<span style="background:rgba(167,139,250,0.15);border:1.5px solid '
        'rgba(167,139,250,0.3);color:#A78BFA;font-size:13px;font-weight:600;'
        'padding:6px 16px;border-radius:20px;">🧠 CT Scans</span>'
        '<span style="background:rgba(52,211,153,0.15);border:1.5px solid '
        'rgba(52,211,153,0.3);color:#34D399;font-size:13px;font-weight:600;'
        'padding:6px 16px;border-radius:20px;">🔬 Ultrasound</span>'
        '<span style="background:rgba(251,191,36,0.15);border:1.5px solid '
        'rgba(251,191,36,0.3);color:#FBBF24;font-size:13px;font-weight:600;'
        'padding:6px 16px;border-radius:20px;">⚡ Multimodal Fusion</span>'
        '</div></div>'
        '<div style="text-align:center;">'
        '<div style="background:rgba(37,99,235,0.1);border:1.5px solid '
        'rgba(37,99,235,0.25);border-radius:14px;padding:28px 36px;">'
        '<div style="font-size:48px;font-weight:800;color:#4A9EFF;'
        'line-height:1;margin-bottom:4px;">99.7<span style="font-size:24px;">%</span>'
        '</div>'
        '<div style="font-size:13px;color:#4A6080;font-weight:500;">'
        'Ultrasound accuracy</div>'
        '<div style="height:1px;background:#1E3250;margin:16px 0;"></div>'
        '<div style="font-size:40px;font-weight:800;color:#A78BFA;'
        'line-height:1;margin-bottom:4px;">87%</div>'
        '<div style="font-size:13px;color:#4A6080;font-weight:500;">'
        'CT scan accuracy</div>'
        '</div></div></div></div>',
        unsafe_allow_html=True
    )

    # How it works
    st.markdown(
        '<div style="font-size:22px;font-weight:700;color:#F0F6FF;'
        'letter-spacing:-0.5px;margin-bottom:20px;">How It Works</div>',
        unsafe_allow_html=True
    )

    steps = [
        ('#2563EB', '01', '👤', 'Patient Submits',
         'Patient finds their record by ID, fills details and uploads their test report. Assigned to their doctor instantly.'),
        ('#7C3AED', '02', '🤖', 'AI Analyses',
         'Lab, CT and ultrasound results processed by trained models. Severity scored. RAG-powered clinical report generated.'),
        ('#D97706', '03', '🩺', 'Doctor Reviews',
         'Doctor sees only their department cases. Reviews AI findings, adds prescription, approves or edits.'),
        ('#059669', '04', '📱', 'Patient Notified',
         'Approved report with prescription delivered. Clear result shown. SMS sent. No hospital revisit needed.'),
    ]

    cols = st.columns(4)
    for col, (color, num, icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-radius:14px;padding:24px 20px;height:230px;'
                'border-top:3px solid ' + color + ';">'
                '<div style="display:flex;align-items:center;gap:10px;'
                'margin-bottom:14px;">'
                '<span style="font-size:24px;">' + icon + '</span>'
                '<span style="font-size:12px;font-weight:700;color:' + color + ';'
                'letter-spacing:0.1em;text-transform:uppercase;">STEP ' + num + '</span>'
                '</div>'
                '<div style="font-size:17px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:10px;letter-spacing:-0.3px;">' + title + '</div>'
                '<div style="font-size:13px;color:#7A90A8;line-height:1.65;">'
                + desc + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown('<br>', unsafe_allow_html=True)

    # Quick access
    st.markdown(
        '<div style="font-size:22px;font-weight:700;color:#F0F6FF;'
        'letter-spacing:-0.5px;margin-bottom:20px;">Quick Access</div>',
        unsafe_allow_html=True
    )

    qa1, qa2, qa3 = st.columns(3)
    for col, (icon, title, desc, label, pid, color) in zip(
        [qa1, qa2, qa3], [
            ('👤', 'I am a Patient',
             'Find your test results by ID and submit to your assigned doctor for review.',
             'Go to Patient Portal', 'patient', '#2563EB'),
            ('🩺', 'I am a Doctor',
             'Review AI-generated clinical reports for your patients. Approve, edit or reject.',
             'Open Doctor Dashboard', 'doctor', '#7C3AED'),
            ('📋', 'Check My Report',
             'Enter your patient reference number to view your approved report and prescription.',
             'View My Report', 'result', '#059669'),
        ]
    ):
        with col:
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-radius:14px;padding:28px 24px;margin-bottom:10px;'
                'min-height:180px;">'
                '<div style="font-size:32px;margin-bottom:14px;">' + icon + '</div>'
                '<div style="font-size:18px;font-weight:700;color:#F0F6FF;'
                'margin-bottom:8px;letter-spacing:-0.3px;">' + title + '</div>'
                '<div style="font-size:14px;color:#7A90A8;line-height:1.6;">'
                + desc + '</div>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button(label, key='home_' + pid,
                         use_container_width=True, type='primary'):
                st.session_state.page = pid
                st.rerun()

    # Live dataset stats
    lab = load_lab(); ct = load_ct(); us = load_us(); fus = load_fusion()
    if any(df is not None for df in [lab, ct, us, fus]):
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:22px;font-weight:700;color:#F0F6FF;'
            'letter-spacing:-0.5px;margin-bottom:20px;">Live System Data</div>',
            unsafe_allow_html=True
        )
        sc = st.columns(4)
        for col, (icon, lbl, df, color) in zip(sc, [
            ('🧪', 'Lab Patients',    lab, '#4A9EFF'),
            ('🧠', 'CT Scans',        ct,  '#A78BFA'),
            ('🔬', 'Ultrasound',      us,  '#34D399'),
            ('⚡', 'Combined Cases',  fus, '#FBBF24'),
        ]):
            cnt    = len(df) if df is not None else 0
            severe = int(df['_sev'].eq('Severe').sum()) if df is not None else 0
            with col:
                st.markdown(
                    '<div style="background:#112033;border:1.5px solid #1E3250;'
                    'border-top:3px solid ' + color + ';border-radius:12px;'
                    'padding:20px;text-align:center;">'
                    '<div style="font-size:28px;margin-bottom:8px;">' + icon + '</div>'
                    '<div style="font-size:32px;font-weight:800;color:' + color + ';'
                    'line-height:1;">' + str(cnt) + '</div>'
                    '<div style="font-size:14px;color:#7A90A8;margin-top:6px;'
                    'font-weight:500;">' + lbl + '</div>'
                    + ('<div style="font-size:13px;color:#FF3B3B;margin-top:6px;'
                       'font-weight:600;">' + str(severe) + ' severe</div>'
                       if severe > 0 else '') +
                    '</div>',
                    unsafe_allow_html=True
                )

    # Recent activity
    if st.session_state.patients:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:22px;font-weight:700;color:#F0F6FF;'
            'letter-spacing:-0.5px;margin-bottom:16px;">Recent Activity</div>',
            unsafe_allow_html=True
        )
        recent = sorted(
            st.session_state.patients.items(),
            key=lambda x: x[1].get('registered_at',''), reverse=True
        )[:8]
        status_color = {
            'APPROVED':'#00C48C', 'REJECTED':'#FF3B3B', 'PENDING':'#FFB800'
        }
        for pid, p in recent:
            s   = p.get('status','PENDING')
            fus_l = p.get('fusion_label', p.get('severity_label','Unknown'))
            fc  = SEV_COLOR.get(fus_l,'#8892A4')
            sc  = status_color.get(s,'#4A6080')
            st.markdown(
                '<div style="background:#112033;border:1.5px solid #1E3250;'
                'border-radius:10px;padding:14px 20px;margin-bottom:8px;'
                'display:flex;align-items:center;justify-content:space-between;">'
                '<div style="display:flex;align-items:center;gap:16px;">'
                '<span style="font-size:15px;font-weight:700;color:#F0F6FF;'
                'font-family:monospace;">' + str(pid) + '</span>'
                '<span style="font-size:14px;color:#7A90A8;">'
                + p.get('name','') + '</span>'
                '<span style="background:' + fc + '22;border:1px solid ' + fc + '44;'
                'color:' + fc + ';font-size:12px;font-weight:600;'
                'padding:3px 12px;border-radius:20px;">' + fus_l + '</span>'
                '</div>'
                '<div style="display:flex;align-items:center;gap:14px;">'
                '<span style="font-size:13px;color:' + sc + ';font-weight:700;">'
                + s + '</span>'
                '<span style="font-size:12px;color:#4A6080;">'
                + p.get('registered_at','')[:16] + '</span>'
                '</div></div>',
                unsafe_allow_html=True
            )
