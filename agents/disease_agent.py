import requests
from agents.rag_agents import rag_query

DIAGNOSIS_API_URL = "http://localhost:8001/diagnose"


def _image_diagnosis(image_path: str) -> dict:
    """Confirmed diagnosis path: run the ONNX model on an actual photo."""
    with open(image_path, "rb") as f:
        response = requests.post(DIAGNOSIS_API_URL, files={"file": f})
    result = response.json()

    disease_name = result["disease"].replace("___", " - ").replace("_", " ")
    confidence = result["confidence"]

    treatment_query = f"treatment and management for {disease_name}"
    treatment_info = rag_query(treatment_query)

    return {
        "answer": (
            f"Diagnosis (from photo): {disease_name} (confidence: {confidence:.0%})\n\n"
            f"Treatment guidance:\n{treatment_info['answer']}"
        ),
        "agent": "disease",
        "diagnosis_type": "confirmed",
    }


def _symptom_based_guess(query: str) -> dict:
    """
    Fallback path: no photo provided. Search the knowledge base for symptom
    matches based on the described text. This is NOT a confirmed diagnosis —
    it's a best-guess based on symptom descriptions, which can overlap across
    multiple diseases. Always clearly labeled as such.
    """
    symptom_query = f"disease symptoms matching: {query}"
    rag_result = rag_query(symptom_query)

    return {
        "answer": (
            "No photo was provided, so this is a possible match based on your description only "
            "(not a confirmed diagnosis \u2014 many plant diseases share similar-sounding symptoms).\n\n"
            f"{rag_result['answer']}\n\n"
            "For a reliable diagnosis, please upload a clear photo of the affected leaf."
        ),
        "agent": "disease",
        "diagnosis_type": "symptom_guess",
    }


def disease_agent(query: str, image_path: str = None) -> dict:
    if image_path:
        try:
            return _image_diagnosis(image_path)
        except Exception as e:
            return {
                "answer": f"Could not process the uploaded photo ({e}). "
                          f"Falling back to a description-based guess instead.\n\n"
                          + _symptom_based_guess(query)["answer"],
                "agent": "disease",
                "diagnosis_type": "symptom_guess_fallback",
            }

    if not query or not query.strip():
        return {
            "answer": "Please upload a photo of the affected leaf for diagnosis, or describe the "
                      "symptoms you're seeing (e.g. 'brown spots on tomato leaves') for a general match.",
            "agent": "disease",
            "diagnosis_type": "none",
        }

    return _symptom_based_guess(query)