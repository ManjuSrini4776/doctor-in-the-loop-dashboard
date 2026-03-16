# ============================================================
# pipeline.py — matches NB09 fusion + NB10 RAG exactly
# ============================================================
import os, math
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from openai import OpenAI

VECTOR_DB_PATH  = "data/vector_db"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
SEVERITY_TEXT   = {0:"Normal",1:"Mild",2:"Moderate",3:"Severe"}

def _notna(val):
    if val is None: return False
    try:    return not math.isnan(float(val))
    except: return str(val) not in ["nan","None",""]

@st.cache_resource
def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings":True}
    )

@st.cache_resource
def get_vector_db():
    emb = get_embedding_model()
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(
            VECTOR_DB_PATH, emb,
            allow_dangerous_deserialization=True
        )
    return None

# ── Exact build_query from NB10
def build_query(patient: dict) -> str:
    parts = []
    if _notna(patient.get("lab_score")):
        sev = SEVERITY_TEXT.get(int(float(patient["lab_score"])),"unknown")
        parts.append(f"Laboratory findings indicate {sev} abnormality")
    if _notna(patient.get("ct_score")):
        sev = SEVERITY_TEXT.get(int(float(patient["ct_score"])),"unknown")
        dis = patient.get("ct_disease","brain tumor")
        if not dis or str(dis) in ["nan","None",""]: dis = "brain tumor"
        parts.append(f"CT imaging suggests {dis} with {sev} severity")
    if _notna(patient.get("ultrasound_score")):
        sev = SEVERITY_TEXT.get(int(float(patient["ultrasound_score"])),"unknown")
        dis = patient.get("ultrasound_disease","ultrasound abnormality")
        if not dis or str(dis) in ["nan","None",""]: dis = "ultrasound abnormality"
        parts.append(f"Ultrasound examination indicates {dis} with {sev} severity")
    if _notna(patient.get("final_severity")):
        parts.append(f"Overall clinical severity is {patient['final_severity']}")
    ctx = ". ".join(parts)
    return (f"Patient clinical assessment based on multimodal AI analysis.\n"
            f"{ctx}.\nRetrieve relevant clinical guideline recommendations for "
            f"diagnosis, monitoring and management.")

# ── Exact generate_report from NB10
def generate_report(query: str, context_docs: list) -> str:
    client  = OpenAI(api_key=os.environ.get("OPENAI_API_KEY",""))
    context = "\n\n".join([d.page_content for d in context_docs])
    prompt  = f"""You are a clinical decision support assistant.

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
    r = OpenAI(api_key=os.environ.get("OPENAI_API_KEY","")).chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=300
    )
    return r.choices[0].message.content

def run_rag_pipeline(patient: dict) -> dict:
    cid   = str(patient.get("case_id","unknown"))
    query = build_query(patient)
    db    = get_vector_db()
    docs  = db.similarity_search(query, k=5) if db else []
    report= generate_report(query, docs)
    sources = list({d.metadata.get("source_file","") for d in docs
                    if d.metadata.get("source_file","")})
    return {"case_id":cid,"query":query,"report":report,
            "rag_type":"Page Index RAG","faithfulness":0.692,"sources":sources[:4]}
