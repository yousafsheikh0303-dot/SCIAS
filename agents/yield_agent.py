# agents/yield_agent.py
import json
import numpy as np
from xgboost import XGBRegressor

MODEL_PATH = "models/yield_model.json"
ENCODER_CLASSES_PATH = "models/encoder_classes.json"
SCALER_PARAMS_PATH = "models/scaler_params.json"

# Load model (native XGBoost format — no pickle)
_model = XGBRegressor()
_model.load_model(MODEL_PATH)

# Load encoder classes (plain JSON — no pickle)
with open(ENCODER_CLASSES_PATH, "r") as f:
    _encoder_classes = json.load(f)
# e.g. {"Region": ["East", "North", "South", "West"], ...}

# Load scaler parameters (plain JSON — no pickle)
with open(SCALER_PARAMS_PATH, "r") as f:
    _scaler_params = json.load(f)

FEATURE_ORDER = _scaler_params["feature_names"]
_MEAN = np.array(_scaler_params["mean"])
_SCALE = np.array(_scaler_params["scale"])

DEFAULT_INPUTS = {
    "Region": "North",
    "Soil_Type": "Loam",
    "Rainfall_mm": 500.0,
    "Temperature_Celsius": 28.0,
    "Fertilizer_Used": 1,
    "Irrigation_Used": 1,
    "Weather_Condition": "Sunny",
    "Days_to_Harvest": 120,
}


def _encode_label(column: str, value: str) -> int:
    """Replicates sklearn LabelEncoder: index of value in sorted class list."""
    classes = _encoder_classes[column]
    if value not in classes:
        raise ValueError(f"'{value}' not recognized for {column}. Valid options: {classes}")
    return classes.index(value)

def get_yield_options() -> dict:
    """Exposes valid categorical options for the frontend to build dropdowns."""
    return _encoder_classes

def _parse_crop(query: str) -> str:
    q = query.lower()
    for crop in _encoder_classes["Crop"]:
        if crop.lower() in q:
            return crop
    return "Wheat"


def yield_agent(query: str, **overrides) -> dict:
    crop = _parse_crop(query)
    inputs = {**DEFAULT_INPUTS, "Crop": crop, **overrides}

    try:
        encoded = {}
        for col in ["Region", "Soil_Type", "Crop", "Weather_Condition"]:
            encoded[col] = _encode_label(col, inputs[col])
    except ValueError as e:
        return {"answer": str(e), "agent": "yield"}

    row = {**inputs, **encoded}
    feature_values = np.array([row[col] for col in FEATURE_ORDER], dtype=float)

    # Manual StandardScaler replication: (x - mean) / scale
    features_scaled = (feature_values - _MEAN) / _SCALE
    features_scaled = features_scaled.reshape(1, -1)

    prediction = _model.predict(features_scaled)[0]

    return {
        "answer": (
            f"Estimated yield for {crop} under current conditions: "
            f"{round(float(prediction), 2)} tons/hectare.\n"
            f"(Model trained on generalized crop-yield relationships; "
            f"strongest influence from fertilizer and irrigation use.)"
        ),
        "agent": "yield",
    }