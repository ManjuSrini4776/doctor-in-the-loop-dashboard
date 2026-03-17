import streamlit as st
from utils import SEV_COLORS, load_lab, load_ct, load_us, load_fusion


def render():
    # Hero
    st.markdown(
        '<div style="background:linear-gradient(135deg,#111827 0%,#0F1E35 100%);'
        'border:1px solid #1E2D40;border-radius:16px;padding:36px 44px;'
        'margin-bottom:28px;">'
        '<div style="font-size:13px;font-weight:600;color:#3B82F6;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">'
        'Doctor-in-the-Loop AI</div>'
        '<div style="font-size:30px;font-weight:700;color:#F1F5F9;'
        'letter-spacing:-0.5px;line-height:1.2;margin-bottom:12px;">'
        'AI-Powered Clinical<br>Report Generation</div>'
        '<div style="font-size:15px;color:#94A3B8;line-height:1.7;'
        'max-width:560px;margin-bottom:24px;">'
        'Multimodal medical AI that analyses lab reports, CT scans and '
        'ultrasounds — then routes findings to your doctor for review '
        'before you receive them. No unnecessary hospital visits.</div>'
        '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
        '<span style="background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);'
        'color:#60A5FA;font-size:13px;font-weight:500;padding:5px 14px;border-radius:20px;">'
        'Lab Report Analysis</span>'
        '<span style="background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);'
        'color:#A78BFA;font-size:13px;font-weight:500;padding:5px 14px;border-radius:20px;">'
        'CT Scan Classification</span>'
        '<span style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);'
        'color:#34D399;font-size:13px;font-weight:500;padding:5px 14px;border-radius:20px;">'
        'Ultrasound Assessment</span>'
        '<span style="background:rgba(249,115,22,0.15);border:1px solid rgba(249,115,22,0.3);'
        'color:#FB923C;font-size:13px;font-weight:500;padding:5px 14px;border-radius:20px;">'
        'Doctor Review & Approval</span>'
        '</div></div>',
        unsafe_allow_html=True
    )

    # How it works
    st.markdown(
        '<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
        'margin-bottom:18px;">How It Works</div>',
        unsafe_allow_html=True
    )

    steps = [
        ('#3B82F6','01','Patient Submits',
         'Patient searches their ID, fills in details and uploads lab report. '
         'Routed to their assigned doctor instantly.'),
        ('#8B5CF6','02','AI Analyses',
         'Lab, CT and ultrasound results analysed by trained AI models. '
         'Severity scored. RAG-powered clinical report generated.'),
        ('#F59E0B','03','Doctor Reviews',
         'Doctor sees only their department\'s cases. Reviews AI report, '
         'adds prescription and approves or edits.'),
        ('#10B981','04','Patient Notified',
         'Patient receives approved report with prescription. '
         'Clear result — Normal, Mild, Moderate or Severe. '
         'SMS notification sent. No revisit needed for routine results.'),
    ]

    cols = st.columns(4)
    for col, (color, num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-top:3px solid {color};border-radius:12px;'
                f'padding:22px 18px;min-height:210px;">'
                f'<div style="font-size:28px;font-weight:700;color:{color};'
                f'opacity:0.4;font-family:monospace;margin-bottom:10px;">{num}</div>'
                f'<div style="font-size:15px;font-weight:600;color:#F1F5F9;'
                f'margin-bottom:10px;line-height:1.3;">{title}</div>'
                f'<div style="font-size:13px;color:#94A3B8;line-height:1.6;">'
                f'{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<br>', unsafe_allow_html=True)

    # Quick access
    st.markdown(
        '<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
        'margin-bottom:18px;">Quick Access</div>',
        unsafe_allow_html=True
    )

    qa1,qa2,qa3 = st.columns(3)
    for col,(icon,title,desc,label,pid) in zip([qa1,qa2,qa3],[
        ('👤','I am a Patient',
         'Search your test results and submit to your doctor.',
         'Go to Patient Portal','patient'),
        ('🩺','I am a Doctor',
         'Review AI-generated reports for your patients.',
         'Open Doctor Dashboard','doctor'),
        ('📋','Check My Report',
         'View your approved report and prescription.',
         'View My Report','result'),
    ]):
        with col:
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-radius:12px;padding:26px 22px;min-height:160px;'
                f'margin-bottom:8px;">'
                f'<div style="font-size:28px;margin-bottom:12px;">{icon}</div>'
                f'<div style="font-size:16px;font-weight:600;color:#F1F5F9;'
                f'margin-bottom:8px;">{title}</div>'
                f'<div style="font-size:13px;color:#94A3B8;line-height:1.6;">'
                f'{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button(label, key=f'home_{pid}',
                         use_container_width=True, type='primary'):
                st.session_state.page = pid
                st.rerun()

    # Dataset stats
    lab = load_lab(); ct = load_ct(); us = load_us(); fus = load_fusion()
    if any(df is not None for df in [lab, ct, us, fus]):
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
            'margin-bottom:18px;">System Data</div>',
            unsafe_allow_html=True
        )
        ds_cols = st.columns(4)
        icons   = ['🧪','🧠','🔬','⚡']
        labels  = ['Lab Patients','CT Scans','US Scans','Combined Cases']
        dfs     = [lab, ct, us, fus]
        colors  = ['#3B82F6','#8B5CF6','#10B981','#F59E0B']
        for col,(icon,lbl,df,clr) in zip(ds_cols, zip(icons,labels,dfs,colors)):
            with col:
                cnt    = len(df) if df is not None else 0
                severe = int(df['_sev'].eq('Severe').sum()) if df is not None else 0
                st.markdown(
                    f'<div style="background:#111827;border:1px solid #1E2D40;'
                    f'border-top:3px solid {clr};border-radius:10px;'
                    f'padding:16px;text-align:center;">'
                    f'<div style="font-size:22px;margin-bottom:6px;">{icon}</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{clr};">'
                    f'{cnt:,}</div>'
                    f'<div style="font-size:13px;color:#64748B;margin-top:3px;">'
                    f'{lbl}</div>'
                    f'{"<div style=font-size:12px;color:#EF4444;margin-top:4px;>" + str(severe) + " severe</div>" if severe > 0 else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # Recent activity
    if st.session_state.patients:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:20px;font-weight:700;color:#F1F5F9;'
            'margin-bottom:16px;">Recent Activity</div>',
            unsafe_allow_html=True
        )
        recent = sorted(
            st.session_state.patients.items(),
            key=lambda x: x[1].get('registered_at',''), reverse=True
        )[:6]
        status_clr = {'APPROVED':'#10B981','REJECTED':'#EF4444',
                      'PENDING':'#F59E0B'}
        for pid, p in recent:
            s    = p.get('status','PENDING')
            fus  = p.get('fusion_label', p.get('severity_label','Unknown'))
            fc   = SEV_COLORS.get(fus,'#94A3B8')
            sc   = status_clr.get(s,'#64748B')
            st.markdown(
                f'<div style="background:#111827;border:1px solid #1E2D40;'
                f'border-radius:10px;padding:12px 18px;margin-bottom:6px;'
                f'display:flex;align-items:center;justify-content:space-between;">'
                f'<div style="display:flex;align-items:center;gap:14px;">'
                f'<span style="font-family:monospace;font-size:13px;'
                f'font-weight:600;color:#F1F5F9;">{pid}</span>'
                f'<span style="font-size:13px;color:#64748B;">'
                f'{p.get("name","")}</span>'
                f'<span style="background:{fc}22;border:1px solid {fc}44;'
                f'color:{fc};font-size:11px;padding:2px 10px;border-radius:20px;">'
                f'{fus}</span>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:12px;">'
                f'<span style="color:{sc};font-size:12px;font-weight:600;'
                f'font-family:monospace;">{s}</span>'
                f'<span style="font-size:11px;color:#334155;">'
                f'{p.get("registered_at","")[:16]}</span>'
                f'</div></div>',
                unsafe_allow_html=True
            )
