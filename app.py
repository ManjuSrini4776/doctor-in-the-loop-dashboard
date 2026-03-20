# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  NB09 — RAG PIPELINE (RECREATED)                                        ║
# ║  Baseline · Hierarchical · PageIndex comparison + 50 Patient Summaries  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ═══════════════════════════════════════════════════════════════════════════
# CELL 1 — Install dependencies
# ═══════════════════════════════════════════════════════════════════════════
# !pip install -q langchain langchain-community faiss-cpu sentence-transformers openai ragas

# ═══════════════════════════════════════════════════════════════════════════
# CELL 2 — Mount Drive + Paths
# ═══════════════════════════════════════════════════════════════════════════
import os
from google.colab import drive
if not os.path.isdir('/content/drive/MyDrive'):
    drive.mount('/content/drive')
else:
    print("✅ Drive already mounted")

# ── ALL CONFIRMED PATHS ───────────────────────────────────────────────────
LAB_PATH      = '/content/drive/MyDrive/MIMIC_DOCTOR_IN_LOOP_PROJECT/checkpoints/NB06_MULTIMODAL_SEVERITY_FUSION.parquet'
CT_PATH       = '/content/drive/MyDrive/Medical_AI_Project/ct_module/results/CT_SEVERITY_FOR_FUSION.csv'
US_PATH       = '/content/drive/MyDrive/Medical_AI_Project/ultrasound_module/results/US_SEVERITY_FOR_FUSION.csv'
SAVE_DIR      = '/content/drive/MyDrive/dashboard_data'

# RAG vector DB paths
BASELINE_PATH     = '/content/drive/MyDrive/Medical_AI_Project/rag_output/baseline_vector_db'
HIERARCHICAL_PATH = '/content/drive/MyDrive/Medical_AI_Project/rag_output/hierarchical_vector_db'
PAGEINDEX_PATH    = '/content/drive/MyDrive/Medical_AI_Project/rag_output/pageindex_vector_db'

# Saved outputs
RAG_METRICS_PATH  = '/content/drive/MyDrive/Medical_AI_Project/rag_output/rag_comparison_metrics.csv'
BEST_CONFIG_PATH  = '/content/drive/MyDrive/Medical_AI_Project/rag_output/best_rag_config.json'
RAG_OUTPUT_PATH   = '/content/drive/MyDrive/Medical_AI_Project/rag_output/rag_final_outputs.json'

os.makedirs(SAVE_DIR, exist_ok=True)
print("✅ Paths configured")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 3 — Load RAG Vector DBs
# ═══════════════════════════════════════════════════════════════════════════
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import numpy as np

print("Loading embedding model (all-MiniLM-L6-v2)...")
emb = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
print("✅ Embedding model loaded  |  Dimension: 384")

print("\nLoading RAG vector databases...")
baseline_db     = FAISS.load_local(BASELINE_PATH,     emb, allow_dangerous_deserialization=True)
hierarchical_db = FAISS.load_local(HIERARCHICAL_PATH, emb, allow_dangerous_deserialization=True)
pageindex_db    = FAISS.load_local(PAGEINDEX_PATH,    emb, allow_dangerous_deserialization=True)

print(f"✅ Baseline DB     loaded  |  Size: {os.path.getsize(BASELINE_PATH+'/index.faiss')//1024} KB")
print(f"✅ Hierarchical DB loaded  |  Size: {os.path.getsize(HIERARCHICAL_PATH+'/index.faiss')//1024} KB")
print(f"✅ PageIndex DB    loaded  |  Size: {os.path.getsize(PAGEINDEX_PATH+'/index.faiss')//1024} KB")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 4 — SHOW 5 SAMPLE CHUNKS (what the RAG knows)
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("STEP 1 — SAMPLE CHUNKS FROM KNOWLEDGE BASE")
print("How clinical guidelines are stored in the RAG vector database")
print("=" * 70)

# Use diverse queries to show different document types
sample_queries = [
    ("CKD — Renal",      "chronic kidney disease eGFR management KDIGO"),
    ("Diabetes — Endo",  "diabetes mellitus glucose HbA1c ADA guidelines"),
    ("Thyroid — Endo",   "hypothyroidism TSH levothyroxine treatment"),
    ("CT — Neuro",       "brain tumour glioma meningioma neurosurgery"),
    ("US — Obstetric",   "fetal ultrasound obstetric antenatal guidelines"),
]

for i, (label, query) in enumerate(sample_queries, 1):
    docs = baseline_db.similarity_search(query, k=1)
    d    = docs[0]
    src  = d.metadata.get('source_file', d.metadata.get('source','unknown'))
    dom  = d.metadata.get('domain', 'general')
    pg   = d.metadata.get('page_number', d.metadata.get('page','?'))

    print(f"\n{'─'*70}")
    print(f"CHUNK {i}  [{label}]")
    print(f"  Source : {src}  |  Domain: {dom}  |  Page: {pg}")
    print(f"  Content: {d.page_content[:400].strip()}")

print(f"\n{'─'*70}")
print("✅ These chunks are retrieved at query time and passed to GPT as context")
print("   Each chunk = one page/section of a clinical guideline PDF")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 5 — SHOW 5 EMBEDDINGS (how text becomes a vector)
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("STEP 2 — CHUNK → EMBEDDING CONVERSION")
print("How text is converted to 384-dimensional vectors for similarity search")
print("=" * 70)

# Use the 5 chunks retrieved above
embed_queries = [
    "chronic kidney disease eGFR management KDIGO",
    "diabetes mellitus glucose HbA1c ADA guidelines",
    "hypothyroidism TSH levothyroxine treatment",
    "brain tumour glioma meningioma neurosurgery",
    "fetal ultrasound obstetric antenatal guidelines",
]

chunk_texts = []
for q in embed_queries:
    docs = baseline_db.similarity_search(q, k=1)
    chunk_texts.append(docs[0].page_content[:120])

embeddings_list = emb.embed_documents(chunk_texts)

print(f"\n  Embedding model : all-MiniLM-L6-v2")
print(f"  Dimensions      : 384 (each chunk → 384 float values)")
print(f"  Similarity      : cosine similarity (higher = more relevant)")

for i, (text, vec) in enumerate(zip(chunk_texts, embeddings_list), 1):
    vec_arr = np.array(vec)
    print(f"\n  {'─'*66}")
    print(f"  EMBEDDING {i}")
    print(f"  Text   : \"{text[:90].strip()}...\"")
    print(f"  Vector : [{', '.join(f'{v:.4f}' for v in vec_arr[:8])}, ...]  (384 total)")
    print(f"  Stats  : min={vec_arr.min():.4f}  max={vec_arr.max():.4f}  mean={vec_arr.mean():.4f}  norm={np.linalg.norm(vec_arr):.4f}")

print(f"\n  {'─'*66}")
print("✅ Each chunk is permanently stored as a 384-dim vector in the FAISS index")
print("   At query time: patient query → vector → find nearest chunks → send to GPT")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 6 — RAG ARCHITECTURE COMPARISON
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import json

print("=" * 70)
print("STEP 3 — RAG ARCHITECTURE COMPARISON")
print("Baseline vs Hierarchical vs PageIndex — 6 configurations tested")
print("=" * 70)

# Load saved metrics
metrics_df = pd.read_csv(RAG_METRICS_PATH)
with open(BEST_CONFIG_PATH) as f:
    best_config = json.load(f)

print("\n  Results from your NB09 evaluation:")
print(f"  {'─'*66}")
print(f"  {'Config':20} {'Type':14} {'Version':14} {'Faithfulness':13} {'Relevancy':10} {'Latency(s)':11} {'Context Len':11}")
print(f"  {'─'*66}")

for _, row in metrics_df.iterrows():
    is_best = "⭐" if row['RAG_Name'] == best_config['best_rag_name'] else "  "
    print(f"  {is_best} {row['RAG_Name']:18} {row['RAG_Type']:14} {row['Version']:14} "
          f"{row['Faithfulness']:.4f}{'':8} {row['Answer_Relevancy']:.4f}{'':5} "
          f"{row['Avg_Latency_s']:.3f}{'':7} {int(row['Avg_Context_Len'])}")

print(f"\n  {'─'*66}")
print(f"\n  🏆 WINNER: {best_config['best_rag_name']}  ({best_config['best_rag_type']})")
print(f"  Faithfulness    : {best_config['faithfulness']:.4f}")
print(f"  Answer Relevancy: {best_config['answer_relevancy']:.4f}")
print(f"  Avg Latency     : {best_config['avg_latency']:.3f}s")
print(f"\n  Selection Reason:")
print(f"  \"{best_config['selection_reason']}\"")

print(f"\n  Architecture Summary:")
print(f"  ┌─────────────────┬──────────────────────────────────────────────┐")
print(f"  │ Baseline        │ Fixed chunk size, simple similarity search   │")
print(f"  │ Hierarchical    │ Parent-child chunks, multi-level retrieval   │")
print(f"  │ PageIndex       │ Full page context + index for navigation     │")
print(f"  └─────────────────┴──────────────────────────────────────────────┘")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 7 — RAG COMPARISON VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('RAG Architecture Comparison — NB09 Evaluation Results',
             fontsize=15, fontweight='bold', y=1.02)

colors = {
    'Baseline':     ['#3B82F6','#60A5FA'],
    'Hierarchical': ['#7C3AED','#A78BFA'],
    'Pageindex':    ['#059669','#34D399'],
}
versions = ['V1 (Baseline)', 'V2 (Improved)']

# Plot 1 — Faithfulness
ax = axes[0]
for i, (rag_type, grp) in enumerate(metrics_df.groupby('RAG_Type')):
    clrs = colors.get(rag_type, ['#gray','#lightgray'])
    for j, (_, row) in enumerate(grp.iterrows()):
        x = i + j * 0.3 - 0.15
        bar = ax.bar(x, row['Faithfulness'], width=0.25,
                     color=clrs[j], alpha=0.9, edgecolor='white')
        ax.text(x, row['Faithfulness']+0.01, f"{row['Faithfulness']:.3f}",
                ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_title('Faithfulness ↑', fontweight='bold', fontsize=12)
ax.set_ylabel('Score (0–1)')
ax.set_xticks([0,1,2])
ax.set_xticklabels(['Baseline','Hierarchical','PageIndex'])
ax.set_ylim(0, 0.85)
ax.axhline(y=best_config['faithfulness'], color='red', linestyle='--',
           alpha=0.5, label=f'Best: {best_config["faithfulness"]:.3f}')
ax.legend(fontsize=8)
ax.grid(axis='y', alpha=0.3)

# Plot 2 — Answer Relevancy
ax = axes[1]
for i, (rag_type, grp) in enumerate(metrics_df.groupby('RAG_Type')):
    clrs = colors.get(rag_type, ['#gray','#lightgray'])
    for j, (_, row) in enumerate(grp.iterrows()):
        x = i + j * 0.3 - 0.15
        ax.bar(x, row['Answer_Relevancy'], width=0.25,
               color=clrs[j], alpha=0.9, edgecolor='white')
        ax.text(x, row['Answer_Relevancy']+0.01, f"{row['Answer_Relevancy']:.3f}",
                ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_title('Answer Relevancy ↑', fontweight='bold', fontsize=12)
ax.set_ylabel('Score (0–1)')
ax.set_xticks([0,1,2])
ax.set_xticklabels(['Baseline','Hierarchical','PageIndex'])
ax.set_ylim(0, 0.75)
ax.grid(axis='y', alpha=0.3)

# Plot 3 — Latency
ax = axes[2]
for i, (rag_type, grp) in enumerate(metrics_df.groupby('RAG_Type')):
    clrs = colors.get(rag_type, ['#gray','#lightgray'])
    for j, (_, row) in enumerate(grp.iterrows()):
        x = i + j * 0.3 - 0.15
        ax.bar(x, row['Avg_Latency_s'], width=0.25,
               color=clrs[j], alpha=0.9, edgecolor='white')
        ax.text(x, row['Avg_Latency_s']+0.05, f"{row['Avg_Latency_s']:.2f}s",
                ha='center', va='bottom', fontsize=8, fontweight='bold')
ax.set_title('Avg Latency ↓ (seconds)', fontweight='bold', fontsize=12)
ax.set_ylabel('Latency (s)')
ax.set_xticks([0,1,2])
ax.set_xticklabels(['Baseline','Hierarchical','PageIndex'])
ax.grid(axis='y', alpha=0.3)

# Legend
v1_patch = mpatches.Patch(color='#3B82F6', label='V1 (Baseline config)')
v2_patch = mpatches.Patch(color='#60A5FA', label='V2 (Improved config)')
fig.legend(handles=[v1_patch, v2_patch], loc='lower center',
           ncol=2, fontsize=10, bbox_to_anchor=(0.5, -0.08))

plt.tight_layout()
plt.savefig(f'{SAVE_DIR}/rag_comparison_chart.png', dpi=150,
            bbox_inches='tight', facecolor='white')
plt.show()
print("✅ RAG comparison chart saved")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 8 — GENERATE 50 PATIENTS (same as COMPLETE_NOTEBOOK Cell 5)
# ═══════════════════════════════════════════════════════════════════════════
import pandas as pd
import numpy as np
import json

np.random.seed(42)
LABEL_TO_SCORE = {'Normal':0,'Mild':1,'Moderate':2,'Severe':3}

print("Loading source data...")
lab_full = pd.read_parquet(LAB_PATH)
lab_full['final_severity_label'] = lab_full['final_severity_label'].replace('Stable','Normal')
lab_full = lab_full[lab_full['final_severity_label'].isin(['Normal','Mild','Moderate','Severe'])].copy()
lab_full['hadm_id'] = lab_full['hadm_id'].astype(str)
for col in ['ckd_severity','diabetes_severity_final','thyroid_severity_final']:
    lab_full[col] = lab_full[col].fillna('Not tested').replace({'Unknown':'Not tested'})

ct_full = pd.read_csv(CT_PATH)
us_full = pd.read_csv(US_PATH)
print(f"✅ Lab: {len(lab_full)} | CT: {len(ct_full)} | US: {len(us_full)}")

def clean(v):
    try:
        f = float(v)
        return None if f != f else round(f,3)
    except: return None

def safe_str(v):
    s = str(v).strip() if v is not None else ''
    return s if s not in ['nan','None','','Not tested','not tested','NaN'] else 'Not tested'

def egfr_to_sev(e):
    if e is None: return None
    return 'Normal' if e>=60 else 'Mild' if e>=45 else 'Moderate' if e>=15 else 'Severe'

def glucose_to_sev(g):
    if g is None: return None
    return 'Normal' if g<100 else 'Mild' if g<126 else 'Severe'

def tsh_to_sev(t):
    if t is None: return None
    return 'Normal' if 0.4<=t<=4.0 else 'Mild' if t<=10 else 'Severe'

patients    = {}
used_hadm   = set()
used_ct_ids = set()
used_us_ids = set()

# LAB — 20 patients (CKD×8 + Diabetes×6 + Thyroid×6)
LAB_PLAN = [
    ('CKD','Normal',4), ('CKD','Mild',2), ('CKD','Severe',2),
    ('Diabetes','Normal',3), ('Diabetes','Mild',1), ('Diabetes','Severe',2),
    ('Thyroid','Normal',3), ('Thyroid','Mild',1), ('Thyroid','Severe',2),
]

for disease, sev, count in LAB_PLAN:
    if disease == 'CKD':
        base = lab_full[lab_full['ckd_severity'] != 'Not tested'].copy()
        def sev_fn(row, s=sev):
            d = egfr_to_sev(clean(row.get('egfr')))
            if d: return d == s
            ckd = str(row.get('ckd_severity','')).upper()
            if s=='Normal': return 'G1' in ckd or 'G2' in ckd
            if s=='Mild':   return 'G3A' in ckd
            if s=='Severe': return 'G4' in ckd or 'G5' in ckd
            return False
    elif disease == 'Diabetes':
        base = lab_full[lab_full['diabetes_severity_final'] != 'Not tested'].copy()
        def sev_fn(row, s=sev):
            d = glucose_to_sev(clean(row.get('glucose')))
            if d: return d == s
            return s.lower() in str(row.get('diabetes_severity_final','')).lower()
    elif disease == 'Thyroid':
        base = lab_full[lab_full['thyroid_severity_final'] != 'Not tested'].copy()
        def sev_fn(row, s=sev):
            d = tsh_to_sev(clean(row.get('tsh')))
            if d: return d == s
            t = str(row.get('thyroid_severity_final','')).lower()
            if s=='Normal': return 'normal' in t
            if s=='Mild':   return 'mild' in t or 'subclinical' in t
            if s=='Severe': return 'severe' in t or 'overt' in t
            return False

    mask  = base.apply(sev_fn, axis=1)
    avail = base[mask & ~base['hadm_id'].isin(used_hadm)]
    if len(avail) < count: avail = base[mask]
    samp  = avail.sample(n=min(count,max(len(avail),1)),
                         replace=len(avail)<count, random_state=42)

    for _, row in samp.iterrows():
        used_hadm.add(str(row['hadm_id']))
        pid = f'LAB-{row["hadm_id"]}-{np.random.randint(100,999)}'
        ckd='Not tested'; dia='Not tested'; thy='Not tested'
        egfr=None; glucose=None; tsh=None; t4=None
        if disease=='CKD':      ckd=safe_str(row.get('ckd_severity')); egfr=clean(row.get('egfr'))
        elif disease=='Diabetes': dia=safe_str(row.get('diabetes_severity_final')); glucose=clean(row.get('glucose'))
        elif disease=='Thyroid':  thy=safe_str(row.get('thyroid_severity_final')); tsh=clean(row.get('tsh')); t4=clean(row.get('free_t4'))
        patients[pid] = {
            'patient_id':pid,'department':'Internal Medicine','doctor_id':'DR001',
            'doctor_name':'Dr. Priya Sharma','modality_type':'Lab Report',
            'disease_type':disease,'_sev':sev,
            'ckd_severity':ckd,'diabetes_severity_final':dia,'thyroid_severity_final':thy,
            'egfr':egfr,'glucose':glucose,'tsh':tsh,'free_t4':t4,
            'lab_score':LABEL_TO_SCORE.get(sev,0),
            'rag_class_key':f'lab_{disease.lower()}_{sev.lower()}',
        }

# CT — 12 patients
CT_PLAN = [('notumor','Normal',0,5),('meningioma','Moderate',2,3),
           ('pituitary','Mild',1,2),('glioma','Severe',3,2)]
for cls, sev, score, count in CT_PLAN:
    df = ct_full[ct_full['ct_predicted_class']==cls].copy()
    av = df[~df['image_id'].isin(used_ct_ids)]
    if len(av)<count: av=df
    s  = av.sample(n=min(count,len(av)), replace=False, random_state=42)
    for _, r in s.iterrows():
        used_ct_ids.add(str(r['image_id']))
        pid = f'CT-{r["image_id"]}-{np.random.randint(100,999)}'
        patients[pid] = {
            'patient_id':pid,'department':'Neurology','doctor_id':'DR002',
            'doctor_name':'Dr. Arjun Mehta','modality_type':'CT Scan',
            'disease_type':cls,'_sev':sev,
            'ct_predicted_class':cls,'ct_confidence':clean(r.get('ct_confidence')),
            'ct_score':clean(r.get('ct_score')) if 'ct_score' in r.index else float(score),
            'rag_class_key':f'ct_{cls}',
        }

# US — 10 patients
US_PLAN = [('Fetal abdomen','Normal',0,4,'us_abdomen'),
           ('Fetal femur','Normal',0,3,'us_femur'),
           ('Fetal thorax','Mild',1,2,'us_thorax'),
           ('Fetal brain','Severe',3,1,'us_brain')]
for cls, sev, score, count, rk in US_PLAN:
    df = us_full[us_full['predicted_class']==cls].copy()
    av = df[~df['patient_id'].isin(used_us_ids)]
    if len(av)<count: av=df
    s  = av.sample(n=min(count,len(av)), replace=False, random_state=42)
    for _, r in s.iterrows():
        used_us_ids.add(str(r['patient_id']))
        pid = f'US-{r["patient_id"]}-{np.random.randint(100,999)}'
        patients[pid] = {
            'patient_id':pid,'department':'Obstetrics','doctor_id':'DR003',
            'doctor_name':'Dr. Kavitha Rajan','modality_type':'Ultrasound',
            'disease_type':cls,'_sev':sev,
            'predicted_class':cls,'confidence':clean(r.get('confidence')),
            'us_score':clean(r.get('us_score')) if 'us_score' in r.index else float(score),
            'rag_class_key':rk,
        }

# Combined — 8 patients
ct_cls_list = ['notumor','glioma','meningioma','pituitary','notumor','meningioma','pituitary','glioma']
us_cls_list = ['Fetal abdomen','Fetal brain','Fetal femur','Fetal thorax',
               'Fetal thorax','Fetal abdomen','Fetal brain','Fetal femur']
ct_sc = {'notumor':0,'pituitary':1,'meningioma':2,'glioma':3}
us_sc = {'Fetal abdomen':0,'Fetal femur':0,'Fetal thorax':1,'Fetal brain':3}
sev_m = {0:'Normal',1:'Mild',2:'Moderate',3:'Severe'}

mm_base = lab_full[
    (lab_full['ckd_severity']!='Not tested') |
    (lab_full['diabetes_severity_final']!='Not tested') |
    (lab_full['thyroid_severity_final']!='Not tested')
].copy()
mm_base   = mm_base[~mm_base['hadm_id'].isin(used_hadm)]
mm_sample = mm_base.sample(n=min(8,len(mm_base)), replace=False, random_state=99)

for i, (_, lr) in enumerate(mm_sample.iterrows()):
    used_hadm.add(str(lr['hadm_id']))
    pid=f'MM-{i+1:03d}'; ct_c=ct_cls_list[i]; us_c=us_cls_list[i]
    lab_score = LABEL_TO_SCORE.get(safe_str(lr.get('final_severity_label','Moderate')),2)
    fusion    = max(lab_score, ct_sc[ct_c], us_sc[us_c])
    fsev      = sev_m[fusion]
    patients[pid] = {
        'patient_id':pid,'department':'General Medicine','doctor_id':'DR004',
        'doctor_name':'Dr. Suresh Kumar','modality_type':'Combined Assessment',
        'disease_type':'Multi-Disease','_sev':fsev,
        'ckd_severity':safe_str(lr.get('ckd_severity')),
        'diabetes_severity_final':safe_str(lr.get('diabetes_severity_final')),
        'thyroid_severity_final':safe_str(lr.get('thyroid_severity_final')),
        'egfr':clean(lr.get('egfr')),'glucose':clean(lr.get('glucose')),
        'tsh':clean(lr.get('tsh')),'free_t4':clean(lr.get('free_t4')),
        'ct_predicted_class':ct_c,'ct_confidence':round(np.random.uniform(0.78,0.99),3),
        'ct_score':float(ct_sc[ct_c]),'us_predicted_class':us_c,
        'confidence':round(np.random.uniform(0.78,0.99),3),
        'us_score':float(us_sc[us_c]),'lab_score':float(lab_score),
        'fusion_score':float(fusion),'fusion_label':fsev,
        'rag_class_key':f'mm_{fsev.lower()}',
    }

from collections import Counter
print(f"\n✅ Generated {len(patients)} patients")
print(f"\n  By Department:")
for k,v in sorted(Counter(p['modality_type'] for p in patients.values()).items()):
    print(f"    {k:25}: {v}")
print(f"\n  By Severity:")
for k in ['Normal','Mild','Moderate','Severe']:
    print(f"    {k:10}: {Counter(p['_sev'] for p in patients.values()).get(k,0)}")
print(f"\n  By Disease:")
for k,v in sorted(Counter(p['disease_type'] for p in patients.values()).items()):
    print(f"    {k:20}: {v}")


# ═══════════════════════════════════════════════════════════════════════════
# CELL 9 — GENERATE RAG SUMMARIES USING BEST RAG (baseline_v1)
# ═══════════════════════════════════════════════════════════════════════════
from google.colab import userdata
from openai import OpenAI
import time

client = OpenAI(api_key=userdata.get('OPENAI_API_KEY'))

SYSTEM_PROMPT = """You are a senior clinical decision support assistant.
Write a structured clinical summary for ONE specific patient.
ONLY discuss the patient's stated disease. Do NOT mention other diseases.
Always use the patient's actual values in your summary.

Use EXACTLY this format:

CLINICAL SUMMARY:
[2-3 sentences using the patient's actual values]

KEY FINDINGS:
• [finding 1]
• [finding 2]
• [finding 3]

RECOMMENDATIONS:
• [action 1]
• [action 2]
• [action 3]

FOLLOW-UP PLAN:
[specific timeline and tests]

URGENCY: [ROUTINE / SEMI-URGENT / URGENT]"""

def build_query(p):
    mtype=p['modality_type']; sev=p['_sev']
    if mtype=='Lab Report':
        d=p['disease_type']
        if d=='CKD':      return f"chronic kidney disease {sev} eGFR {p.get('egfr')} mL/min {p.get('ckd_severity','')} KDIGO management"
        elif d=='Diabetes': return f"diabetes mellitus {sev} fasting glucose {p.get('glucose')} mg/dL ADA glycemic control"
        elif d=='Thyroid':  return f"thyroid disorder hypothyroidism {sev} TSH {p.get('tsh')} mIU/L free T4 {p.get('free_t4')} levothyroxine"
    elif mtype=='CT Scan':
        cls=p.get('ct_predicted_class','')
        labels={'notumor':'normal brain scan no tumour','pituitary':'pituitary adenoma endocrinology',
                'meningioma':'meningioma neurosurgery referral','glioma':'glioma malignant oncology urgent'}
        return f"{labels.get(cls,cls)} {sev} CT brain management"
    elif mtype=='Ultrasound':
        cls=p.get('predicted_class','')
        labels={'Fetal abdomen':'fetal abdominal biometry gestational age',
                'Fetal femur':'fetal femur length growth chart',
                'Fetal thorax':'fetal thorax cardiac pulmonary echocardiography',
                'Fetal brain':'fetal brain neurosonography anomaly scan'}
        return f"{labels.get(cls,cls)} {sev} obstetric ultrasound"
    return f"multimodal combined assessment {sev} management"

def build_prompt(p, context):
    mtype=p['modality_type']; disease=p['disease_type']; sev=p['_sev']
    lines=[]
    if mtype=='Lab Report':
        lines.append(f"Disease  : {disease} — Severity: {sev}")
        if disease=='CKD':
            egfr=p.get('egfr'); ckd=p.get('ckd_severity','Not recorded')
            lines.append(f"eGFR     : {egfr} mL/min/1.73m²" if egfr else "eGFR     : Not measured this visit")
            lines.append(f"CKD Stage: {ckd}")
            lines.append("NOTE: KIDNEY DISEASE ONLY. Do NOT mention diabetes, glucose, or thyroid.")
        elif disease=='Diabetes':
            gluc=p.get('glucose'); dia=p.get('diabetes_severity_final','Not recorded')
            lines.append(f"Glucose  : {gluc} mg/dL (fasting)" if gluc else "Glucose  : Not measured this visit")
            lines.append(f"Diabetes : {dia}")
            lines.append("NOTE: DIABETES ONLY. Do NOT mention kidney disease, CKD, eGFR, or thyroid.")
        elif disease=='Thyroid':
            tsh=p.get('tsh'); t4=p.get('free_t4'); thy=p.get('thyroid_severity_final','Not recorded')
            lines.append(f"TSH      : {tsh} mIU/L" if tsh else "TSH      : Not measured this visit")
            lines.append(f"Free T4  : {t4} ng/dL"  if t4  else "Free T4  : Not measured this visit")
            lines.append(f"Thyroid  : {thy}")
            lines.append("NOTE: THYROID ONLY. Do NOT mention kidney disease, CKD, diabetes, or glucose.")
    elif mtype=='CT Scan':
        cls=p.get('ct_predicted_class','')
        conf=round((p.get('ct_confidence') or 0)*100,1)
        names={'notumor':'No Brain Tumour Detected','pituitary':'Pituitary Adenoma',
               'meningioma':'Meningioma','glioma':'Glioma (High-Grade)'}
        lines+=[f"Scan      : CT Brain",f"Class     : {names.get(cls,cls)}",
                f"Confidence: {conf}%",f"Severity  : {sev}",
                "NOTE: BRAIN IMAGING ONLY. Do NOT mention eGFR, glucose, TSH, or lab values.",
                f"NOTE: Discuss ONLY {names.get(cls,cls)}. Do NOT mention any other tumour type."]
    elif mtype=='Ultrasound':
        cls=p.get('predicted_class','')
        conf=round((p.get('confidence') or 0)*100,1)
        names={'Fetal abdomen':'Fetal Abdomen','Fetal femur':'Fetal Femur',
               'Fetal thorax':'Fetal Thorax','Fetal brain':'Fetal Brain'}
        lines+=[f"Scan      : Obstetric Ultrasound",f"View      : {names.get(cls,cls)}",
                f"Confidence: {conf}%",f"Severity  : {sev}",
                "NOTE: OBSTETRIC ULTRASOUND ONLY. Do NOT mention lab values."]
    elif mtype=='Combined Assessment':
        ct=p.get('ct_predicted_class',''); us=p.get('us_predicted_class','')
        egfr=p.get('egfr'); gluc=p.get('glucose'); tsh=p.get('tsh')
        lines+=[f"Assessment: Multimodal (Lab + CT Brain + Obstetric Ultrasound)",
                f"Fusion Severity: {p.get('fusion_label','Moderate')}",
                f"eGFR    : {egfr} mL/min" if egfr else "eGFR    : Not measured",
                f"CKD     : {p.get('ckd_severity','Not tested')}",
                f"Glucose : {gluc} mg/dL"  if gluc else "Glucose : Not measured",
                f"Diabetes: {p.get('diabetes_severity_final','Not tested')}",
                f"TSH     : {tsh} mIU/L"   if tsh  else "TSH     : Not measured",
                f"Thyroid : {p.get('thyroid_severity_final','Not tested')}",
                f"CT Brain: {ct}  |  Obstetric US: {us}"]
    block="\n".join(f"  {l}" for l in lines)
    return f"""Patient: {p['patient_id']}\n\nPATIENT VALUES:\n{block}\n\nCLINICAL GUIDELINES:\n{context}\n\nWrite the clinical summary using the patient's actual values."""

# Generate summaries
rag_summaries = {}
failed        = []
total         = len(patients)

print(f"Generating RAG summaries for {total} patients using baseline_v1 (faithfulness=0.703)")
print(f"RAG DB: {BASELINE_PATH}")
print("=" * 65)

for i, (pid, p) in enumerate(patients.items(), 1):
    try:
        query       = build_query(p)
        docs        = baseline_db.similarity_search(query, k=3)
        context     = "\n\n---\n\n".join(d.page_content for d in docs)
        user_prompt = build_prompt(p, context)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":SYSTEM_PROMPT},
                      {"role":"user","content":user_prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        summary = resp.choices[0].message.content.strip()
        rag_summaries[pid] = summary

        disease = p.get('disease_type','')
        sev     = p['_sev']
        print(f"  [{i:02d}/{total}] ✅ {pid[:28]:28} | {disease:15} | {sev}")

        # Print first 3 full summaries to verify quality
        if i <= 3:
            print(f"\n  ── PREVIEW {pid} ──")
            print(summary)
            print()

        if i % 10 == 0:
            time.sleep(1)

    except Exception as e:
        print(f"  [{i:02d}/{total}] ❌ {pid} — {e}")
        rag_summaries[pid] = "Summary unavailable"
        failed.append(pid)


# ═══════════════════════════════════════════════════════════════════════════
# CELL 10 — QUALITY CHECK + SAVE ALL FILES
# ═══════════════════════════════════════════════════════════════════════════
SECTIONS = ['CLINICAL SUMMARY','KEY FINDINGS','RECOMMENDATIONS','FOLLOW-UP','URGENCY']

print("=" * 65)
print("QUALITY CHECK")
print("=" * 65)

print("\n  Section coverage:")
for sec in SECTIONS:
    n   = sum(1 for s in rag_summaries.values()
              if sec in str(s) and str(s) != 'Summary unavailable')
    pct = round(n/len(rag_summaries)*100)
    bar = "✅" if pct >= 80 else "⚠️ "
    print(f"  {bar} {sec:20}: {n}/{len(rag_summaries)} ({pct}%)")

print("\n  Cross-contamination check:")
contam = [
    ("CKD + 'no glucose in urine'",
     [pid for pid,p in patients.items() if p.get('disease_type')=='CKD'
      and 'no indications of glucose in the urine' in rag_summaries.get(pid,'').lower()]),
    ("CT + lab values (eGFR/glucose)",
     [pid for pid,p in patients.items() if p.get('modality_type')=='CT Scan'
      and any(w in rag_summaries.get(pid,'').lower() for w in ['egfr','glucose level','tsh level'])]),
    ("Glioma + 'meningioma' text",
     [pid for pid,p in patients.items() if p.get('ct_predicted_class')=='glioma'
      and 'meningioma' in rag_summaries.get(pid,'').lower()]),
]
total_issues = 0
for label, pids in contam:
    status = "✅" if len(pids)==0 else "⚠️ "
    print(f"  {status} {label}: {len(pids)}")
    total_issues += len(pids)

print(f"\n  Failed summaries: {len(failed)}")
if total_issues == 0 and len(failed) == 0:
    print("\n✅ ALL CHECKS PASSED — saving files!")
else:
    print(f"\n⚠️  {total_issues} issues found — saving anyway (app.py will filter)")

# Save both files
PAT_FILE = f'{SAVE_DIR}/patients.json'
RAG_FILE = f'{SAVE_DIR}/rag_summaries.json'

with open(PAT_FILE, 'w') as f: json.dump(patients, f, indent=2)
with open(RAG_FILE, 'w') as f: json.dump(rag_summaries, f, indent=2)

pat_size = os.path.getsize(PAT_FILE)/1024
rag_size = os.path.getsize(RAG_FILE)/1024

print("=" * 65)
print("✅ FILES SAVED")
print("=" * 65)
print(f"\n  patients.json      → {PAT_FILE}")
print(f"  Size               : {pat_size:.0f} KB  ({len(patients)} patients)")
print(f"\n  rag_summaries.json → {RAG_FILE}")
print(f"  Size               : {rag_size:.0f} KB  ({len(rag_summaries)} summaries)")
print()
print("  Run: streamlit run app.py")
print("=" * 65)
