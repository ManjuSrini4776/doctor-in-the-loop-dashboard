def run_clinical_pipeline(patient_id):

    # example placeholder until we connect real models
    patient_context = f"Patient {patient_id} clinical context loaded."

    ct_prediction = "Meningioma"
    severity = "Moderate"

    explanation = f"""
CT imaging suggests features consistent with {ct_prediction}.
Multimodal analysis indicates {severity} severity.
Further MRI evaluation is recommended according to guideline evidence.
"""

    return {
        "context": patient_context,
        "prediction": ct_prediction,
        "severity": severity,
        "explanation": explanation
    }
