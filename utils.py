"""
Shared utilities — data loading, helpers, constants
"""
import streamlit as st
import pandas as pd
import numpy as np
import os

# ── Constants ─────────────────────────────────────────────────
SEV_COLORS = {
    'Normal':   '#10B981',
    'Mild':     '#F59E0B',
    'Moderate': '#F97316',
    'Severe':   '#EF4444',
    'Unknown':  '#94A3B8'
}
SEV_BG = {
    'Normal':   'rgba(16,185,129,0.1)',
    'Mild':     'rgba(245,158,11,0.1)',
    'Moderate': 'rgba(249,115,22,0.1)',
    'Severe':   'rgba(239,68,68,0.1)',
    'Unknown':  'rgba(148,163,184,0.1)'
}
SEV_ICON = {
    'Normal':'✅', 'Mild':'⚠️',
    'Moderate':'🔶', 'Severe':'🚨', 'Unknown':'📋'
}
CT_NAMES = {
    'notumor':   'No Brain Tumour Detected',
    'pituitary': 'Pituitary Adenoma',
    'meningioma':'Meningioma',
    'glioma':    'Glioma'
}
US_NAMES = {
    'Fetal abdomen':'Fetal Abdomen — Normal',
    'Fetal brain':  'Fetal Brain Plane',
    'Fetal femur':  'Fetal Femur — Normal Growth',
    'Fetal thorax': 'Fetal Thorax Plane'
}
SCORE_TO_LABEL = {0:'Normal', 1:'Mild', 2:'Moderate', 3:'Severe'}

# Doctor definitions + what they can see
DOCTORS = {
    'DR001': {
        'name':      'Dr. Priya Sharma',
        'dept':      'Internal Medicine',
        'specialty': 'Nephrology & Chronic Disease',
        'sees':      ['Lab Report'],
        'color':     '#3B82F6'
    },
    'DR002': {
        'name':      'Dr. Arjun Mehta',
        'dept':      'Neurology',
        'specialty': 'Neuro-Oncology',
        'sees':      ['CT Scan', 'Combined Assessment'],
        'color':     '#8B5CF6'
    },
    'DR003': {
        'name':      'Dr. Kavitha Rajan',
        'dept':      'Obstetrics & Gynaecology',
        'specialty': 'Fetal Medicine',
        'sees':      ['Ultrasound', 'Combined Assessment'],
        'color':     '#10B981'
    },
    'DR004': {
        'name':      'Dr. Suresh Kumar',
        'dept':      'General Medicine',
        'specialty': 'Multimodal Assessment',
        'sees':      ['Lab Report', 'CT Scan', 'Ultrasound', 'Combined Assessment'],
        'color':     '#F59E0B'
    },
}


# ── File loader — handles data/ folder or root ────────────────
def find_file(filename):
    """Find CSV file in data/ folder or root."""
    candidates = [
        f'data/{filename}',
        filename,
        f'data/{filename.replace(" ", "_")}',
        # Handle (1) suffix from GitHub duplicate uploads
        f'data/{filename.replace(".csv", " (1).csv")}',
        filename.replace('.csv', ' (1).csv'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@st.cache_data
def load_lab():
    path = find_file('lab_data.csv')
    if path:
        df = pd.read_csv(path)
        df['_id']    = df['hadm_id'].astype(str)
        df['_sev']   = df['final_severity_label'].fillna('Unknown')
        df['_mtype'] = 'Lab Report'
        return df
    return None


@st.cache_data
def load_ct():
    path = find_file('ct_data.csv')
    if path:
        df = pd.read_csv(path)
        df['_id']    = df['image_id'].astype(str)
        df['_sev']   = df['ct_severity_label'].fillna('Unknown')
        df['_mtype'] = 'CT Scan'
        return df
    return None


@st.cache_data
def load_us():
    path = find_file('us_data.csv')
    if path:
        df = pd.read_csv(path)
        df['_id']    = df['patient_id'].astype(str)
        df['_sev']   = df['us_severity_label'].fillna('Unknown')
        df['_mtype'] = 'Ultrasound'
        return df
    return None


@st.cache_data
def load_fusion():
    path = find_file('fusion_data.csv')
    if path:
        df = pd.read_csv(path)
        df['_id']    = df['case_id'].astype(str)
        df['_sev']   = df['fusion_label'].fillna('Unknown')
        df['_mtype'] = 'Combined Assessment'
        return df
    return None


def get_all_data():
    """Load all datasets."""
    return {
        'lab':    load_lab(),
        'ct':     load_ct(),
        'us':     load_us(),
        'fusion': load_fusion(),
    }


# ── HTML helpers ──────────────────────────────────────────────
def sev_badge(label, size=13):
    c = SEV_COLORS.get(label, '#94A3B8')
    b = SEV_BG.get(label, 'rgba(148,163,184,0.1)')
    return (
        f'<span style="background:{b};border:1px solid {c}55;'
        f'color:{c};font-size:{size}px;font-weight:600;'
        f'padding:3px 12px;border-radius:20px;">{label}</span>'
    )


def card(content, border_color=None, padding='16px 20px'):
    border = f'border-left:4px solid {border_color};' if border_color else ''
    return (
        f'<div style="background:#111827;border:1px solid #1E2D40;'
        f'{border}border-radius:10px;padding:{padding};margin-bottom:10px;">'
        f'{content}</div>'
    )


def section_title(text):
    return (
        f'<div style="font-size:13px;font-weight:600;color:#94A3B8;'
        f'text-transform:uppercase;letter-spacing:0.08em;'
        f'margin:20px 0 12px;">{text}</div>'
    )


def stat_block(label, value, color='#F1F5F9', sub=None):
    sub_html = (f'<div style="font-size:12px;color:#64748B;margin-top:3px;">'
                f'{sub}</div>') if sub else ''
    return (
        f'<div style="background:#0B1120;border:1px solid #1E2D40;'
        f'border-radius:10px;padding:14px;text-align:center;">'
        f'<div style="font-size:11px;color:#64748B;text-transform:uppercase;'
        f'letter-spacing:0.06em;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{color};">{value}</div>'
        f'{sub_html}</div>'
    )
