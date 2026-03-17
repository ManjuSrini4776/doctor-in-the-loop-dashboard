# Doctor-in-the-Loop Medical AI Dashboard

A multimodal clinical decision support system combining Lab Report analysis, CT Tumor Classification, and Fetal Ultrasound assessment with RAG-powered AI report generation.

## Live Demo
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

## System Architecture

```
Lab Report (MIMIC-IV)     CT Tumor (Kaggle)      Ultrasound (Planes-DB)
CKD + Diabetes + Thyroid  EfficientNet-B0 87%    DenseNet121 99.7%
        ↓                        ↓                        ↓
        └──────────── Multimodal Fusion Engine ───────────┘
                              ↓
                    RAG Pipeline (Baseline V1)
                    Faithfulness: 0.703
                              ↓
                    GPT-4o-mini Report Generation
                              ↓
                    Doctor-in-the-Loop Review
                    Approve / Edit / Reject
```

## Modules

| Module | Dataset | Model | Accuracy |
|--------|---------|-------|----------|
| Lab Report | MIMIC-IV | CKD-EPI + ADA thresholds | Clinical rules |
| CT Tumor | Kaggle Brain Tumor | EfficientNet-B0 (2-stage fine-tune) | 87.03% |
| Ultrasound | Fetal Planes DB | DenseNet121 | 99.7% |
| RAG | WHO/ICMR guidelines | Baseline V1 (Faithfulness=0.703) | — |

## Setup

### Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud
1. Fork this repository
2. Go to share.streamlit.io
3. Deploy from your fork
4. Add `OPENAI_API_KEY` in Streamlit Cloud Secrets

## Project Structure

```
├── app.py                          # Streamlit dashboard
├── requirements.txt                # Dependencies
├── sample_data/                    # Demo data
│   └── fusion_sample.parquet
├── notebooks/
│   ├── NB01_OPD_Chronic_Cohort.ipynb
│   ├── NB02_Disease_Severity.ipynb
│   ├── NB03_Fusion_Visualization.ipynb
│   ├── CT_NB01_Setup_DataExploration.ipynb
│   ├── CT_NB02_Inference_Severity_Evaluation.ipynb
│   ├── CT_NB03_GradCAM_FusionOutput.ipynb
│   ├── US_NB01_DataPrep.ipynb
│   ├── US_NB02_ModelComparison_Inference.ipynb
│   ├── US_NB03_GradCAM_FusionOutput.ipynb
│   ├── NB08_Multimodal_Fusion.ipynb
│   ├── NB09_RAG_Pipeline.ipynb
│   └── NB10_Doctor_Dashboard.ipynb
└── .streamlit/
    └── secrets.toml                # API keys (not in git)
```

## Severity Scale

| Score | Label | Clinical Meaning |
|-------|-------|-----------------|
| 0 | Normal | No significant findings |
| 1 | Mild | Monitor, routine follow-up |
| 2 | Moderate | Specialist referral recommended |
| 3 | Severe | Urgent intervention required |

## Tech Stack

- **Frontend**: Streamlit
- **ML Models**: PyTorch (EfficientNet-B0, DenseNet121)
- **RAG**: LangChain + FAISS + all-MiniLM-L6-v2
- **LLM**: OpenAI GPT-4o-mini
- **Data**: MIMIC-IV, Kaggle Brain Tumor CT, Fetal Planes DB (Zenodo)

## Final Year Project
Built as part of a final year project on Doctor-in-the-Loop AI systems for multimodal medical report generation.
