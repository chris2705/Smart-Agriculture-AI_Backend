# backend/src/main.py
import os
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from . import auth, models, database, fields

# ===============================
# ENV + GEMINI CLIENT
# ===============================
load_dotenv(override=True)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ===============================
# DATABASE
# ===============================
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Smart-Agriculture Backend API")

app.include_router(auth.router)
app.include_router(fields.router)

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(BASE_DIR, "backend_models")
EXPL_DIR = os.path.join(BASE_DIR, "backend_explanations")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(EXPL_DIR, exist_ok=True)

# ===============================
# REQUEST MODELS
# ===============================

class CropFeatures(BaseModel):
    n: float
    p: float
    k: float
    temperature: float
    ph: float


class FertilizerFeatures(BaseModel):
    n: float
    p: float
    k: float
    temperature: float
    moisture: float
    crop_type: str
    soil_type: str


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


# ===============================
# MODEL LOADING
# ===============================

def load_models():
    try:
        crop_model = joblib.load(os.path.join(MODEL_DIR, "crop_recommendation.joblib"))
        fert_model = joblib.load(os.path.join(MODEL_DIR, "fertilizer_model.joblib"))
        crop_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_crop.joblib"))
        fert_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_fert.joblib"))
        crop_type_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_crop_type.joblib"))
        soil_type_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_soil_type.joblib"))

        return crop_model, fert_model, crop_le, fert_le, crop_type_le, soil_type_le

    except Exception as e:
        raise RuntimeError(f"Error loading models: {e}")


@app.on_event("startup")
def startup_event():
    global CROP_MODEL, FERT_MODEL, CROP_LE, FERT_LE, CROP_TYPE_LE, SOIL_TYPE_LE

    print("[backend] Loading models from disk...")

    (
        CROP_MODEL,
        FERT_MODEL,
        CROP_LE,
        FERT_LE,
        CROP_TYPE_LE,
        SOIL_TYPE_LE,
    ) = load_models()

    print("[backend] Models loaded successfully.")


# ===============================
# STATIC FILES
# ===============================
app.mount("/explanations", StaticFiles(directory=EXPL_DIR), name="explanations")

# ===============================
# 🌱 CROP PREDICTION
# ===============================

@app.post("/predict/crop")
def predict_crop(data: CropFeatures):
    try:
        features = [
            data.n,
            data.p,
            data.k,
            data.temperature,
            data.ph,
        ]

        pred_idx = int(CROP_MODEL.predict([features])[0])
        crop_name = str(CROP_LE.inverse_transform([pred_idx])[0])
        proba = CROP_MODEL.predict_proba([features])[0].tolist()

        return {
            "success": True,
            "prediction": crop_name,
            "probabilities": proba,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 🧪 FERTILIZER PREDICTION
# ===============================

@app.post("/predict/fertilizer")
def predict_fertilizer(data: FertilizerFeatures):
    try:
        crop_enc = CROP_TYPE_LE.transform([data.crop_type])[0]
        soil_enc = SOIL_TYPE_LE.transform([data.soil_type])[0]

        features = [
            data.n,
            data.p,
            data.k,
            data.temperature,
            data.moisture,
            crop_enc,
            soil_enc,
        ]

        pred_idx = int(FERT_MODEL.predict([features])[0])
        fert_name = str(FERT_LE.inverse_transform([pred_idx])[0])

        return {
            "success": True,
            "prediction": fert_name,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# 💬 CHAT (UPDATED FOR NEW SDK)
# ===============================

@app.post("/chat")
def chat(request: ChatRequest):

    msg = request.message
    context = request.context or {}

    crop = context.get("prediction", "Unknown")
    explanation = context.get("explanation", {})
    fert_rec = explanation.get("fertilizer_recommendation", "Unknown")

    language = context.get("language", "en-US")
    is_malayalam = language == "ml-IN"

    system_prompt = f"""
You are a helpful agricultural assistant.

Context:
- Predicted suitable crop: {crop}
- Recommended fertilizer: {fert_rec}

IMPORTANT:
- If Malayalam requested, reply fully in Malayalam.
- Keep answers short and farmer-friendly.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nUser: {msg}",
        )

        return {"response": response.text}

    except Exception as e:
        return {"response": f"AI service unavailable: {str(e)}"}


# ===============================
# HEALTH & SUPPORT ENDPOINTS
# ===============================

@app.get("/supported-crops")
def get_supported_crops():
    return {"crops": CROP_LE.classes_.tolist()}


@app.get("/supported-fert-crops")
def get_supported_fert_crops():
    return {"crops": CROP_TYPE_LE.classes_.tolist()}


@app.get("/supported-soil-types")
def get_supported_soil_types():
    return {"soil_types": SOIL_TYPE_LE.classes_.tolist()}


@app.get("/health")
def health():
    return {"status": "ok"}