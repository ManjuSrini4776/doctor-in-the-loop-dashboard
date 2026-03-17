import streamlit as st
import pandas as pd
from datetime import datetime


def render():
    # Header
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0D1621 0%,#111827 100%);
                border:1px solid #1E293B;border-radius:14px;
                padding:28px 36px;margin-bottom:28px;">
        <div style="font-family:'Playfair Display',serif;font-size:26px;
                    color:#F0F4FF;margin-bottom:6px;">
            Doctor-in-the-Loop Hospital AI System
        </div>
        <div style="font-size:13px;color:#64748B;
                    font-family:'IBM Plex Mono',monospace;">
            Automated Lab · CT · Ultrasound Report Processing &amp;
            Clinical Decision Support
        </div>
        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
            <span style="background:rgba(16,185,129,.12);
                         border:1px solid rgba(16,185,129,.25);
                         color:#10B981;font-size:11px;padding:3px 10px;
                         border-radius:20px;font-family:'IBM Plex Mono',monospace;">
                ● SYSTEM ONLINE
            </span>
            <span style="background:rgba(59,130,246,.12);
                         border:1px solid rgba(59,130,246,.25);
                         color:#3B82F6;font-size:11px;padding:3px 10px;
                         border-radius:20px;font-family:'IBM Plex Mono',monospace;">
                RAG · Baseline V1 · Faithfulness 0.703
            </span>
            <span style="background:rgba(139,92,246,.12);
                         border:1px solid rgba(139,92,246,.25);
                         color:#8B5CF6;font-size:11px;padding:3px 10px;
                         border-radius:20px;font-family:'IBM Plex Mono',monospace;">
                GPT-4o-mini · Clinical Reports
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                padding-bottom:10px;border-bottom:1px solid #1E293B;
                margin-bottom:20px;">
        ── How It Works
    </div>
    """, unsafe_allow_html=True)

    steps = [
        ('1', '#3B82F6', '👤', 'Patient Registers',
         'Patient visits hospital, provides sample. System registers patient with assigned doctor and test type.'),
        ('2', '#8B5CF6', '🤖', 'AI Processes Report',
         'Lab/CT/Ultrasound results auto-processed. Severity scored. GradCAM explainability generated.'),
        ('3', '#F59E0B', '🩺', 'Doctor Reviews',
         'Report auto-routed to ordering doctor. Doctor reviews AI findings, approves or edits.'),
        ('4', '#10B981', '📱', 'Patient Notified',
         'Patient receives friendly result — Normal/Mild/Moderate/Severe. Reduces queue and revisit burden.'),
    ]

    cols = st.columns(4)
    for col, (num, color, icon, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-top:3px solid {color};border-radius:10px;
                        padding:18px;height:200px;">
                <div style="font-size:24px;margin-bottom:8px;">{icon}</div>
                <div style="font-size:11px;color:{color};
                            font-family:'IBM Plex Mono',monospace;
                            margin-bottom:6px;">STEP {num}</div>
                <div style="font-size:13px;font-weight:600;
                            color:#F0F4FF;margin-bottom:6px;">{title}</div>
                <div style="font-size:12px;color:#64748B;
                            line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Quick actions
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                padding-bottom:10px;border-bottom:1px solid #1E293B;
                margin-bottom:20px;">── Quick Actions</div>
    """, unsafe_allow_html=True)

    qa1, qa2, qa3 = st.columns(3)

    with qa1:
        st.markdown("""
        <div style="background:#0D1621;border:1px solid #1E293B;
                    border-radius:10px;padding:20px;text-align:center;">
            <div style="font-size:32px;margin-bottom:10px;">👤</div>
            <div style="font-size:14px;font-weight:600;color:#F0F4FF;
                        margin-bottom:6px;">I'm a Patient</div>
            <div style="font-size:12px;color:#64748B;margin-bottom:14px;">
                Register for tests or check your report status
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Go to Patient Portal →',
                     use_container_width=True, key='home_patient'):
            st.session_state.page = 'patient'
            st.rerun()

    with qa2:
        st.markdown("""
        <div style="background:#0D1621;border:1px solid #1E293B;
                    border-radius:10px;padding:20px;text-align:center;">
            <div style="font-size:32px;margin-bottom:10px;">🩺</div>
            <div style="font-size:14px;font-weight:600;color:#F0F4FF;
                        margin-bottom:6px;">I'm a Doctor</div>
            <div style="font-size:12px;color:#64748B;margin-bottom:14px;">
                Review AI-generated reports and approve findings
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Go to Doctor Dashboard →',
                     use_container_width=True, key='home_doctor'):
            st.session_state.page = 'doctor'
            st.rerun()

    with qa3:
        st.markdown("""
        <div style="background:#0D1621;border:1px solid #1E293B;
                    border-radius:10px;padding:20px;text-align:center;">
            <div style="font-size:32px;margin-bottom:10px;">📋</div>
            <div style="font-size:14px;font-weight:600;color:#F0F4FF;
                        margin-bottom:6px;">Check My Report</div>
            <div style="font-size:12px;color:#64748B;margin-bottom:14px;">
                Enter your patient ID to view approved report
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button('Check My Report →',
                     use_container_width=True, key='home_result'):
            st.session_state.page = 'result'
            st.rerun()

    # Recent activity
    if st.session_state.patients:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#3B82F6;letter-spacing:.1em;text-transform:uppercase;
                    padding-bottom:10px;border-bottom:1px solid #1E293B;
                    margin-bottom:16px;">── Recent Activity</div>
        """, unsafe_allow_html=True)

        recent = sorted(
            st.session_state.patients.items(),
            key=lambda x: x[1].get('registered_at', ''),
            reverse=True
        )[:5]

        for pid, p in recent:
            status     = p.get('status', 'PENDING')
            sev        = p.get('fusion_label', 'Processing...')
            status_clr = {'APPROVED': '#10B981', 'REJECTED': '#EF4444',
                          'PENDING': '#F59E0B'}.get(status, '#64748B')
            st.markdown(f"""
            <div style="background:#0D1621;border:1px solid #1E293B;
                        border-radius:8px;padding:10px 16px;
                        margin-bottom:6px;display:flex;
                        align-items:center;justify-content:space-between;">
                <div>
                    <span style="font-family:'IBM Plex Mono',monospace;
                                 font-size:13px;color:#F0F4FF;">
                        {pid}
                    </span>
                    <span style="font-size:12px;color:#64748B;
                                 margin-left:10px;">{p.get('name','')}</span>
                    <span style="font-size:12px;color:#64748B;
                                 margin-left:10px;">·
                        {p.get('test_type','')}</span>
                </div>
                <div style="display:flex;gap:10px;align-items:center;">
                    <span style="font-size:11px;color:{status_clr};
                                 font-family:'IBM Plex Mono',monospace;">
                        {status}
                    </span>
                    <span style="font-size:11px;color:#475569;">
                        {p.get('registered_at','')[:16]}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
