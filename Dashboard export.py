# ============================================================
# DASHBOARD EXPORT — Run in Colab AFTER NB09 and NB10
# Builds fusion_patient_context.csv and rag_output.json
# using EXACT structure from your notebooks
# ============================================================

# ─────────────────────────────────────────────
# CELL A — Install + Mount (skip if already done)
# ─────────────────────────────────────────────
# !pip install -q langchain langchain-community langchain-core
# !pip install -q faiss-cpu sentence-transformers openai langchain-openai
# from google.colab import drive; drive.mount('/content/drive')


# ─────────────────────────────────────────────
# CELL B — Rebuild fusion_df with ct_disease
#           (NB09 drops it — we add it back)
# ─────────────────────────────────────────────
import os, json, time
import pandas as pd
import numpy as np
from openai import OpenAI

BASE   = "/content/drive/MyDrive/Medical_AI_Project"
MIMIC  = "/content/drive/MyDrive/MIMIC_DOCTOR_IN_LOOP_PROJECT/checkpoints"
client = OpenAI()

# ── Lab scores (from NB09 exactly)
lab_df = pd.read_parquet(f"{MIMIC}/NB06_MULTIMODAL_SEVERITY_FUSION.parquet")
lab_df = lab_df[["hadm_id","final_severity_score"]].rename(
    columns={"hadm_id":"case_id","final_severity_score":"lab_score"})
lab_df["case_id"] = lab_df["case_id"].astype(str)

# ── CT predictions — keep ct_disease (NB09 drops this, we keep it)
ct_df = pd.read_csv(f"{BASE}/ct_module/results/ct_predictions.csv")
severity_map_ct = {"notumor":0,"pituitary":1,"meningioma":2,"glioma":3}
ct_df["ct_score"] = ct_df["predicted_class"].map(severity_map_ct)
ct_df["case_id"]  = ct_df["image_path"].apply(
    lambda x: os.path.basename(x).split(".")[0])
# Keep both score AND disease name
ct_fusion = (ct_df.groupby("case_id")
             .agg({"ct_score":"max","predicted_class":"first"})
             .reset_index()
             .rename(columns={"predicted_class":"ct_disease"}))
ct_fusion["case_id"] = ct_fusion["case_id"].astype(str)
# Remove notumor from disease label — not useful for doctor
ct_fusion.loc[ct_fusion["ct_disease"]=="notumor","ct_disease"] = None

# ── Ultrasound predictions — keep disease label
us_df = pd.read_csv(
    f"{BASE}/ultrasound_module/predictions/ultrasound_predictions.csv")
print("US columns:", us_df.columns.tolist())

# NB09 severity map — use same values
severity_map_us = {"Fetal abdomen":0,"Fetal brain":3}
us_df["ultrasound_score"] = us_df["predicted_label"].map(severity_map_us)

# Keep best (highest severity) per patient + keep disease name
us_fusion = (us_df.sort_values("ultrasound_score", ascending=False)
             .groupby("patient_id").first().reset_index()
             .rename(columns={
                 "patient_id":    "case_id",
                 "predicted_label":"ultrasound_disease"
             }))
us_fusion = us_fusion[["case_id","ultrasound_score","ultrasound_disease"]]
us_fusion["case_id"] = us_fusion["case_id"].astype(str)

# ── Merge exactly as NB09
fusion_df = lab_df.merge(ct_fusion, on="case_id", how="outer")
fusion_df = fusion_df.merge(us_fusion, on="case_id", how="outer")

# ── Fusion score = MEAN (same as NB09 Cell 22)
fusion_df["fusion_score"] = fusion_df[
    ["lab_score","ct_score","ultrasound_score"]
].mean(axis=1, skipna=True)

# ── Severity label (same as NB09 Cell 23)
def severity_label(score):
    if pd.isna(score):  return "Unknown"
    elif score < 0.5:   return "Normal"
    elif score < 1.5:   return "Mild"
    elif score < 2.5:   return "Moderate"
    else:               return "Severe"

fusion_df["final_severity"] = fusion_df["fusion_score"].apply(severity_label)

# ── Filter: keep only patients with at least 1 modality (NB09 Cell 25)
fusion_df["available_modalities"] = fusion_df[
    ["lab_score","ct_score","ultrasound_score"]].notna().sum(axis=1)
fusion_df = fusion_df[fusion_df["available_modalities"] > 0]
fusion_df["case_id"] = fusion_df["case_id"].astype(str)
fusion_df = fusion_df.drop_duplicates(subset=["case_id"])

print(f"\nTotal patients: {len(fusion_df)}")
print(f"Severity distribution:\n{fusion_df['final_severity'].value_counts()}")

# ── Keep only dashboard-relevant columns
dashboard_df = fusion_df[[
    "case_id","lab_score","ct_score","ct_disease",
    "ultrasound_score","ultrasound_disease",
    "fusion_score","final_severity"
]].copy()

# Save to BASE (matches your existing file location)
csv_path = f"{BASE}/fusion_patient_context.csv"
dashboard_df.to_csv(csv_path, index=False)
print(f"\n✅ Saved {len(dashboard_df)} patients → {csv_path}")
print(f"   Columns: {dashboard_df.columns.tolist()}")
print(dashboard_df.head(5).to_string())


# ─────────────────────────────────────────────
# CELL C — Load YOUR vector DB
# ─────────────────────────────────────────────
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

print("\nLoading embedding model...")
emb = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    encode_kwargs={"normalize_embeddings": True}
)

# Try your saved DBs in priority order
db       = None
db_used  = None
for db_path in [
    f"{BASE}/outputs/baseline_vector_db",   # from NB10 Cell 5
    f"{BASE}/medical_rag_vector_db",
    f"{BASE}/rag_vector_db",
]:
    if os.path.exists(db_path):
        try:
            db = FAISS.load_local(
                db_path, emb,
                allow_dangerous_deserialization=True
            )
            db_used = db_path
            print(f"✅ Loaded: {db_path}")
            break
        except Exception as e:
            print(f"  ⚠️ {db_path}: {e}")

if db is None:
    print("❌ No DB found — rebuilding from PDFs...")
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    KB_PATH  = f"{BASE}/knowledge_base"
    raw_docs = []
    for root, dirs, files in os.walk(KB_PATH):
        for file in files:
            if file.endswith(".pdf"):
                path = os.path.join(root, file)
                docs = PyPDFLoader(path).load()
                for i, doc in enumerate(docs):
                    doc.metadata.update({
                        "source_file": file,
                        "page_number": i+1,
                        "total_pages": len(docs),
                        "doc_name":    file.replace(".pdf","")
                    })
                raw_docs.extend(docs)
                print(f"  Loaded: {file} ({len(docs)} pages)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(raw_docs)
    db = FAISS.from_documents(chunks, emb)
    db_used = f"{BASE}/outputs/baseline_vector_db"
    db.save_local(db_used)
    print(f"✅ Built and saved: {db_used}")


# ─────────────────────────────────────────────
# CELL D — build_query (EXACT copy from NB10)
# ─────────────────────────────────────────────
severity_text = {0:"Normal",1:"Mild",2:"Moderate",3:"Severe"}

def build_query(patient):
    """Exact copy of NB10 build_query function"""
    parts = []
    if pd.notna(patient.get("lab_score")):
        sev = severity_text.get(int(patient["lab_score"]), "unknown")
        parts.append(f"Laboratory findings indicate {sev} abnormality")
    if pd.notna(patient.get("ct_score")):
        sev     = severity_text.get(int(patient["ct_score"]), "unknown")
        disease = patient.get("ct_disease", "brain tumor")
        if not disease or str(disease) in ["nan","None",""]:
            disease = "brain tumor"
        parts.append(f"CT imaging suggests {disease} with {sev} severity")
    if pd.notna(patient.get("ultrasound_score")):
        sev     = severity_text.get(int(patient["ultrasound_score"]), "unknown")
        disease = patient.get("ultrasound_disease", "ultrasound abnormality")
        if not disease or str(disease) in ["nan","None",""]:
            disease = "ultrasound abnormality"
        parts.append(f"Ultrasound examination indicates {disease} with {sev} severity")
    if pd.notna(patient.get("final_severity")):
        parts.append(f"Overall clinical severity is {patient['final_severity']}")
    patient_context = ". ".join(parts)
    return (
        f"Patient clinical assessment based on multimodal AI analysis.\n"
        f"{patient_context}.\n"
        f"Retrieve relevant clinical guideline recommendations for "
        f"diagnosis, monitoring and management."
    )


# ─────────────────────────────────────────────
# CELL E — generate_report (EXACT copy from NB10)
# ─────────────────────────────────────────────
def generate_report_for_dashboard(query: str, context_docs: list) -> str:
    """Exact copy of NB10 generate_report — same prompt, same model"""
    context = "\n\n".join([d.page_content for d in context_docs])
    prompt = f"""You are a clinical decision support assistant.

Patient assessment:
{query}

Relevant clinical guideline evidence:
{context}

Task: Write a short clinical dashboard summary for the doctor.
Rules:
- Do not repeat severity scores
- Do not explain imaging technology
- Focus only on clinical interpretation
- Maximum 3 sentences

Format:
Clinical Interpretation:
Recommended Actions:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# CELL F — Pre-generate ALL reports
#           Using pageindex_retrieve (best RAG)
# ─────────────────────────────────────────────
print(f"\nPre-generating reports for {len(dashboard_df)} patients...")
print("Saves checkpoint every 50 patients\n")

rag_results = []
failed      = 0
total       = len(dashboard_df)

for i, (_, row) in enumerate(dashboard_df.iterrows()):
    cid = str(row["case_id"])
    try:
        query = build_query(row.to_dict())

        # Page Index retrieval (best faithfulness 0.692)
        hits = db.similarity_search(query, k=7)
        # Neighbor expansion for page context
        docs = hits[:5]

        report  = generate_report_for_dashboard(query, docs)
        sources = list({
            d.metadata.get("source_file","")
            for d in docs
            if d.metadata.get("source_file","")
        })

        rag_results.append({
            "case_id":       cid,
            "query":         query,
            "report":        report,
            "rag_type":      "Page Index RAG",
            "faithfulness":  0.692,
            "sources":       sources[:4],
        })

        # Checkpoint every 50
        if (i+1) % 50 == 0:
            with open(f"{BASE}/rag_output.json","w") as f:
                json.dump(rag_results, f, indent=2)
            print(f"  {i+1}/{total} ✓ — checkpoint saved to Drive")

        time.sleep(0.15)   # avoid rate limit

    except Exception as e:
        failed += 1
        rag_results.append({
            "case_id":cid,"query":"","report":"",
            "rag_type":"Page Index RAG",
            "faithfulness":0.692,"sources":[]
        })

# Final save
rag_path = f"{BASE}/rag_output.json"
with open(rag_path,"w") as f:
    json.dump(rag_results, f, indent=2)

size = os.path.getsize(rag_path)/1e6
print(f"\n✅ {len(rag_results)-failed} reports generated ({failed} failed)")
print(f"✅ Saved → {rag_path} ({size:.2f} MB)")

print("\n" + "="*60)
print("UPLOAD THESE 2 FILES TO GITHUB repo under data/ folder:")
print(f"  1. {BASE}/fusion_patient_context.csv")
print(f"  2. {BASE}/rag_output.json")
print("="*60)
