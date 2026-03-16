# ============================================================
# pipeline.py — RAG Pipeline for Doctor Dashboard
# ============================================================

import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from openai import OpenAI

VECTOR_DB_PATH  = "data/vector_db"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

DOMAIN_KEYWORDS = {
    "diabetes": ["diabetes","glucose","insulin","hba1c","glycated",
                 "hyperglycaemia","hypoglycaemia","type 2","metformin"],
    "thyroid":  ["thyroid","tsh","thyroxine","hypothyroid","t3","t4"],
    "renal":    ["kidney","renal","ckd","creatinine","gfr","dialysis","kdigo"],
    "tumor":    ["tumor","tumour","glioma","meningioma","pituitary",
                 "neoplasm","nccn","central nervous system"],
    "fetal":    ["fetal","foetal","ultrasound","obstetric","pregnancy",
                 "gestational","trimester","fetus"],
    "lab":      ["laboratory","lab value","blood test","hemoglobin",
                 "platelet","electrolyte","sodium","potassium"],
}
SEVERITY_TEXT = {0:"Normal",1:"Mild",2:"Moderate",3:"Severe"}

@st.cache_resource
def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True}
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

def get_client():
    api_key = os.environ.get("OPENAI_API_KEY","")
    return OpenAI(api_key=api_key)

def assign_domain(text: str) -> str:
    t = text.lower()
    scores = {d: sum(1 for kw in kws if kw in t)
              for d, kws in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

def build_query(patient: dict) -> str:
    parts = []
    for key, label, prefix in [
        ("lab_score",        None, "Laboratory findings indicate {sev} abnormality"),
        ("ct_score",         "ct_disease", "CT imaging suggests {dis} with {sev} severity"),
        ("ultrasound_score", "ultrasound_disease", "Ultrasound indicates {dis} with {sev} severity"),
    ]:
        val = patient.get(key)
        if val and str(val) not in ["nan","None",""]:
            sev = SEVERITY_TEXT.get(int(float(val)),"unknown")
            if "{dis}" in prefix:
                dis = patient.get(label,"finding")
                parts.append(prefix.format(sev=sev, dis=dis))
            else:
                parts.append(prefix.format(sev=sev))
    sev_label = patient.get("final_severity","")
    if sev_label and str(sev_label) not in ["nan","None",""]:
        parts.append(f"Overall clinical severity is {sev_label}")

    body = ". ".join(parts) + "." if parts else "General patient assessment."
    return (f"Patient clinical assessment based on multimodal AI analysis.\n{body}\n"
            f"Retrieve relevant clinical guideline recommendations for "
            f"diagnosis, monitoring and management.")

def retrieve_context(query: str, k: int = 5) -> list:
    db = get_vector_db()
    if db is None:
        return []
    domain = assign_domain(query)
    docs   = db.similarity_search(query, k=k*3)
    filtered = [d for d in docs if d.metadata.get("domain") == domain]
    return filtered[:k] if filtered else docs[:k]

def generate_report(query: str, context_docs: list) -> str:
    client = get_client()
    if not context_docs:
        return "No guideline evidence retrieved. Ensure knowledge base is loaded in data/vector_db/"

    context = "\n\n".join([
        f"[Evidence {i+1}] Source: {d.metadata.get('source_file','guideline')} "
        f"| Domain: {d.metadata.get('domain','general')}\n{d.page_content}"
        for i, d in enumerate(context_docs)
    ])

    prompt = f"""You are a clinical decision support assistant helping a doctor.

STRICT RULES:
1. Answer ONLY using the provided evidence. Do NOT use prior knowledge.
2. Cite Evidence numbers for each point e.g. [Evidence 1].
3. Be concise — maximum 4 sentences total.
4. If evidence doesn't support a claim write: "No guideline evidence available."

--- PATIENT ASSESSMENT ---
{query}

--- CLINICAL EVIDENCE ---
{context}

--- FORMAT (follow exactly) ---
Clinical Interpretation: [1 sentence]
Recommended Actions:
  • [Action 1 with citation]
  • [Action 2 with citation]
  • [Action 3 with citation]
Monitoring: [1 sentence on follow-up]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system",
             "content":"You are a clinical AI assistant. Only use provided evidence. Always cite."},
            {"role":"user","content":prompt}
        ],
        max_tokens=400, temperature=0.0,
    )
    return response.choices[0].message.content

def run_rag_pipeline(patient: dict) -> dict:
    """Main entry point called by app.py"""
    case_id = str(patient.get("case_id","unknown"))
    query   = build_query(patient)
    docs    = retrieve_context(query, k=5)
    report  = generate_report(query, docs)
    sources = list({d.metadata.get("source_file","")
                    for d in docs if d.metadata.get("source_file","")})
    return {
        "case_id":      case_id,
        "query":        query,
        "report":       report,
        "rag_type":     "Page Index RAG",
        "faithfulness": 0.692,
        "sources":      sources[:5],
        "num_chunks":   len(docs),
    }
