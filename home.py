import streamlit as st
from datetime import datetime


def render():
    # Hero section
    st.markdown("""
    <div style="background:linear-gradient(135deg,#111827 0%,#0F1E35 100%);
                border:1px solid #1E2D40;border-radius:16px;
                padding:40px 48px;margin-bottom:32px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:13px;font-weight:600;color:#3B82F6;
                            letter-spacing:0.1em;text-transform:uppercase;
                            margin-bottom:10px;font-family:'JetBrains Mono',monospace;">
                    Doctor-in-the-Loop AI System
                </div>
                <div style="font-size:32px;font-weight:700;color:#F1F5F9;
                            letter-spacing:-0.5px;line-height:1.2;margin-bottom:12px;">
                    AI-Powered Clinical<br>Report Generation
                </div>
                <div style="font-size:16px;color:#94A3B8;line-height:1.6;
                            max-width:520px;margin-bottom:24px;">
                    Multimodal medical AI that analyses lab reports, CT scans, 
                    and ultrasound together — then helps your doctor review and 
                    approve findings before you receive them.
                </div>
                <div style="display:flex;gap:10px;flex-wrap:wrap;">
                    <span style="background:rgba(59,130,246,0.15);
                                 border:1px solid rgba(59,130,246,0.3);
                                 color:#60A5FA;font-size:13px;font-weight:500;
                                 padding:6px 14px;border-radius:20px;">
                        Lab Report Analysis
                    </span>
                    <span style="background:rgba(139,92,246,0.15);
                                 border:1px solid rgba(139,92,246,0.3);
                                 color:#A78BFA;font-size:13px;font-weight:500;
                                 padding:6px 14px;border-radius:20px;">
                        CT Scan Classification
                    </span>
                    <span style="background:rgba(16,185,129,0.15);
                                 border:1px solid rgba(16,185,129,0.3);
                                 color:#34D399;font-size:13px;font-weight:500;
                                 padding:6px 14px;border-radius:20px;">
                        Ultrasound Assessment
                    </span>
                    <span style="background:rgba(249,115,22,0.15);
                                 border:1px solid rgba(249,115,22,0.3);
                                 color:#FB923C;font-size:13px;font-weight:500;
                                 padding:6px 14px;border-radius:20px;">
                        Doctor Review & Approval
                    </span>
                </div>
            </div>
            <div style="text-align:center;padding:32px;background:rgba(59,130,246,0.08);
                        border:1px solid rgba(59,130,246,0.15);border-radius:16px;
                        min-width:200px;">
                <div style="font-size:48px;font-weight:700;color:#3B82F6;
                            line-height:1;">
                    99.7<span style="font-size:24px;">%</span>
                </div>
                <div style="font-size:13px;color:#64748B;margin-top:4px;">
                    Ultrasound accuracy
                </div>
                <div style="margin-top:16px;padding-top:16px;
                            border-top:1px solid #1E2D40;">
                    <div style="font-size:28px;font-weight:700;color:#8B5CF6;">
                        87%
                    </div>
                    <div style="font-size:13px;color:#64748B;margin-top:4px;">
                        CT scan accuracy
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown("""
    <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                margin-bottom:20px;letter-spacing:-0.3px;">
        How It Works
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ('#3B82F6', '01', 'Patient Submits Tests',
         'Patient visits the hospital for blood tests, CT scan, or ultrasound. Reports are automatically uploaded to the system.'),
        ('#8B5CF6', '02', 'AI Analyses Results',
         'Our AI models analyse each test — identifying chronic disease severity, brain tumours, and fetal health — within seconds.'),
        ('#F59E0B', '03', 'Doctor Reviews Report',
         'The assigned doctor receives the AI-generated report, reviews the findings, and approves, edits, or requests further tests.'),
        ('#10B981', '04', 'Patient Gets Results',
         'Once approved, the patient receives a clear, simple notification — no medical jargon. No need to revisit the hospital.'),
    ]

    cols = st.columns(4)
    for col, (color, num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-top:3px solid {color};border-radius:12px;
                        padding:24px 20px;height:220px;">
                <div style="font-size:28px;font-weight:700;color:{color};
                            opacity:0.4;font-family:'JetBrains Mono',monospace;
                            margin-bottom:10px;">{num}</div>
                <div style="font-size:15px;font-weight:600;color:#F1F5F9;
                            margin-bottom:10px;line-height:1.3;">{title}</div>
                <div style="font-size:13px;color:#94A3B8;line-height:1.6;">
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Quick access
    st.markdown("""
    <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                margin-bottom:20px;letter-spacing:-0.3px;">
        Quick Access
    </div>
    """, unsafe_allow_html=True)

    qa1, qa2, qa3 = st.columns(3)

    for col, (icon, title, desc, btn_label, page_id, color) in zip(
        [qa1, qa2, qa3],
        [
            ('👤', 'I am a Patient',
             'View your test results and check if your report has been approved by your doctor.',
             'Register or View Results', 'patient', '#3B82F6'),
            ('🩺', 'I am a Doctor',
             'Review AI-generated clinical reports assigned to you and approve or edit findings.',
             'Open Doctor Dashboard', 'doctor', '#8B5CF6'),
            ('📋', 'Check My Report',
             'Enter your case reference number to view your approved report and health status.',
             'View My Report', 'result', '#10B981'),
        ]
    ):
        with col:
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-radius:12px;padding:28px 24px;margin-bottom:8px;
                        min-height:180px;">
                <div style="font-size:28px;margin-bottom:12px;">{icon}</div>
                <div style="font-size:16px;font-weight:600;color:#F1F5F9;
                            margin-bottom:8px;">{title}</div>
                <div style="font-size:13px;color:#94A3B8;line-height:1.6;
                            margin-bottom:0px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(btn_label, key=f'qa_{page_id}',
                         use_container_width=True, type='primary'):
                st.session_state.page = page_id
                st.rerun()

    # Recent activity
    if st.session_state.patients:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:20px;font-weight:700;color:#F1F5F9;
                    margin-bottom:16px;letter-spacing:-0.3px;">
            Recent Activity
        </div>
        """, unsafe_allow_html=True)

        recent = sorted(
            st.session_state.patients.items(),
            key=lambda x: x[1].get('registered_at',''),
            reverse=True
        )[:8]

        status_colors = {
            'APPROVED': '#10B981', 'REJECTED': '#EF4444', 'PENDING': '#F59E0B'
        }
        sev_colors = {
            'Normal':'#10B981','Mild':'#F59E0B',
            'Moderate':'#F97316','Severe':'#EF4444','Unknown':'#94A3B8'
        }

        for pid, p in recent:
            status = p.get('status','PENDING')
            fus    = p.get('fusion_label', p.get('severity_label','Unknown'))
            sc     = status_colors.get(status,'#94A3B8')
            fc     = sev_colors.get(fus,'#94A3B8')
            mtype  = p.get('modality_type','Unknown')
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1E2D40;
                        border-radius:10px;padding:14px 20px;
                        margin-bottom:6px;display:flex;align-items:center;
                        justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:16px;">
                    <div style="font-size:14px;font-weight:600;color:#F1F5F9;
                                font-family:'JetBrains Mono',monospace;">
                        {pid}
                    </div>
                    <div style="font-size:13px;color:#64748B;">
                        {p.get('name','Patient')}
                    </div>
                    <div style="font-size:12px;color:#475569;">
                        {mtype}
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="background:rgba(0,0,0,0.3);
                                 border:1px solid {fc}33;color:{fc};
                                 font-size:12px;font-weight:500;
                                 padding:2px 10px;border-radius:20px;">
                        {fus}
                    </span>
                    <span style="color:{sc};font-size:12px;font-weight:600;
                                 font-family:'JetBrains Mono',monospace;">
                        {status}
                    </span>
                    <span style="font-size:11px;color:#334155;">
                        {p.get('registered_at','')[:16]}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
