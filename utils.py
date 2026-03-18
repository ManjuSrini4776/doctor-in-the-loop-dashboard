import streamlit as st
import pandas as pd
import os

# ── Severity ──────────────────────────────────────────────────
SEV_COLOR = {
    'Normal':   '#00C48C',
    'Mild':     '#FFB800',
    'Moderate': '#FF6B35',
    'Severe':   '#FF3B3B',
    'Unknown':  '#8892A4',
}
SEV_BG = {
    'Normal':   'rgba(0,196,140,0.12)',
    'Mild':     'rgba(255,184,0,0.12)',
    'Moderate': 'rgba(255,107,53,0.12)',
    'Severe':   'rgba(255,59,59,0.12)',
    'Unknown':  'rgba(136,146,164,0.12)',
}
SEV_ICON = {
    'Normal':'✅', 'Mild':'⚠️',
    'Moderate':'🔶', 'Severe':'🚨', 'Unknown':'📋'
}
SEV_EMOJI = {
    'Normal':'🟢', 'Mild':'🟡',
    'Moderate':'🟠', 'Severe':'🔴', 'Unknown':'⚪'
}
SCORE_TO_LABEL = {0:'Normal', 1:'Mild', 2:'Moderate', 3:'Severe'}

CT_NAMES = {
    'notumor':   'No Brain Tumour',
    'pituitary': 'Pituitary Adenoma',
    'meningioma':'Meningioma',
    'glioma':    'Glioma'
}
CT_DESC = {
    'notumor':   'Normal brain scan. No suspicious lesion identified.',
    'pituitary': 'Benign pituitary gland tumour. Endocrinology review advised.',
    'meningioma':'Slow-growing meningeal tumour. Neurosurgery referral recommended.',
    'glioma':    'Malignant brain tumour. Urgent oncology referral required.'
}
CT_IMAGE = {
    'glioma':    'images/ct_glioma.png',
    'meningioma':'images/ct_meningioma.png',
    'pituitary': 'images/ct_pituitary.png',
    'notumor':   'images/ct_notumor.png',
}
US_NAMES = {
    'Fetal abdomen':'Fetal Abdomen — Normal',
    'Fetal brain':  'Fetal Brain Plane',
    'Fetal femur':  'Fetal Femur — Normal Growth',
    'Fetal thorax': 'Fetal Thorax Plane'
}
US_DESC = {
    'Fetal abdomen':'Abdominal measurements within expected range.',
    'Fetal brain':  'Neurosonography plane. Detailed anomaly scan recommended.',
    'Fetal femur':  'Femur length within normal range. Growth on track.',
    'Fetal thorax': 'Thoracic plane. Cardiac and pulmonary assessment indicated.'
}
US_IMAGE = {
    'Fetal abdomen':'images/us_abdomen.png',
    'Fetal brain':  'images/us_brain.png',
    'Fetal femur':  'images/us_femur.png',
    'Fetal thorax': 'images/us_thorax.png',
}

DOCTORS = {
    'DR001': {'name':'Dr. Priya Sharma',  'dept':'Internal Medicine',
              'specialty':'Nephrology & Chronic Disease',
              'sees':['Lab Report'], 'color':'#4A9EFF'},
    'DR002': {'name':'Dr. Arjun Mehta',   'dept':'Neurology',
              'specialty':'Neuro-Oncology',
              'sees':['CT Scan','Combined Assessment'], 'color':'#A78BFA'},
    'DR003': {'name':'Dr. Kavitha Rajan', 'dept':'Obstetrics',
              'specialty':'Fetal Medicine',
              'sees':['Ultrasound','Combined Assessment'], 'color':'#34D399'},
    'DR004': {'name':'Dr. Suresh Kumar',  'dept':'General Medicine',
              'specialty':'Multimodal Assessment',
              'sees':['Lab Report','CT Scan','Ultrasound','Combined Assessment'],
              'color':'#FBBF24'},
}

PRESCRIPTIONS = {
    'Normal':   ['Continue current medication as prescribed.',
                 'Maintain healthy diet and regular exercise.',
                 'Routine follow-up in 3 months.',
                 'No immediate intervention required.'],
    'Mild':     ['Monitor symptoms over next 2–4 weeks.',
                 'Review medication dosage with pharmacist.',
                 'Lifestyle modifications recommended.',
                 'Return if symptoms worsen.'],
    'Moderate': ['Specialist referral within 7 days.',
                 'Medication adjustment may be required.',
                 'Avoid strenuous activity until reviewed.',
                 'Repeat blood work in 2 weeks.'],
    'Severe':   ['Immediate specialist consultation required.',
                 'Consider hospital admission for monitoring.',
                 'Do not delay — early treatment is critical.',
                 'Emergency contact available 24/7.'],
}


# ── File finder ───────────────────────────────────────────────
def find_file(name):
    for p in [f'data/{name}', name,
              f'data/{name.replace(".csv"," (1).csv")}',
              name.replace('.csv',' (1).csv')]:
        if os.path.exists(p):
            return p
    return None


@st.cache_data
def load_lab():
    p = find_file('lab_data.csv')
    if p:
        df = pd.read_csv(p)
        df['_id']    = df['hadm_id'].astype(str)
        df['_sev']   = df['final_severity_label'].fillna('Unknown')
        df['_mtype'] = 'Lab Report'
        return df
    return None


@st.cache_data
def load_ct():
    p = find_file('ct_data.csv')
    if p:
        df = pd.read_csv(p)
        df['_id']    = df['image_id'].astype(str)
        df['_sev']   = df['ct_severity_label'].fillna('Unknown')
        df['_mtype'] = 'CT Scan'
        return df
    return None


@st.cache_data
def load_us():
    p = find_file('us_data.csv')
    if p:
        df = pd.read_csv(p)
        df['_id']    = df['patient_id'].astype(str)
        df['_sev']   = df['us_severity_label'].fillna('Unknown')
        df['_mtype'] = 'Ultrasound'
        return df
    return None


@st.cache_data
def load_fusion():
    p = find_file('fusion_data.csv')
    if p:
        df = pd.read_csv(p)
        df['_id']    = df['case_id'].astype(str)
        df['_sev']   = df['fusion_label'].fillna('Unknown')
        df['_mtype'] = 'Combined Assessment'
        return df
    return None
