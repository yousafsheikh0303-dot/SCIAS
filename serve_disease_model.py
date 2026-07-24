# serve_disease_model.py
from fastapi import FastAPI, UploadFile, File
import onnxruntime as ort
import numpy as np
from PIL import Image
import json
import io
import uvicorn

app = FastAPI()
session = ort.InferenceSession("models/leaf_disease_model.onnx")
class_names = json.load(open("models/class_names.json"))

def preprocess(image: Image.Image):
    image = image.resize((224, 224)).convert("RGB")
    arr = np.array(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    arr = (arr - mean) / std
    arr = arr.transpose(2, 0, 1)
    return np.expand_dims(arr, axis=0).astype(np.float32)

@app.post("/diagnose")
async def diagnose(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    input_tensor = preprocess(image)

    outputs = session.run(None, {"input": input_tensor})[0]
    probs = np.exp(outputs) / np.sum(np.exp(outputs))
    predicted_idx = int(np.argmax(probs))
    confidence = float(np.max(probs))

    return {
        "disease": class_names[predicted_idx],
        "confidence": round(confidence, 3)
    }

if __name__ == "__main__":
    print("Starting disease model server on http://localhost:8001 ...")
    uvicorn.run(app, host="0.0.0.0", port=8001)