# backend/src/main.py

import os
import joblib
import numpy as np
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai

from . import auth, models, database, fields

# ===============================
# ENVIRONMENT
# ===============================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    print("⚠ GEMINI_API_KEY not set. Chat disabled.")

# ===============================
# DATABASE
# ===============================
models.Base.metadata.create_all(bind=database.engine)

# ===============================
# FASTAPI INIT
# ===============================
app = FastAPI(title="Smart-Agriculture Backend API")

app.include_router(auth.router)
app.include_router(fields.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# MODEL DIRECTORY (Railway Safe)
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ===============================
# GOOGLE DRIVE DIRECT LINKS
# (REPLACE WITH YOUR LINKS)
# ===============================
CROP_MODEL_URL = "https://drive.google.com/uc?export=download&id=1ujgYFRPIHpi1E2Zg-oePAddC7-4PYpDN"
FERT_MODEL_URL = "https://drive.google.com/uc?export=download&id=1APYnk3VrMPwGEHz5jKftAUwJgutqhQ0J"
CROP_LE_URL = "https://drive.google.com/uc?export=download&id=11JyTimrKC2cddYzp6FpwoQrcgcw_nS0t"
FERT_LE_URL = "https://drive.google.com/uc?export=download&id=1OkPayypZxxDQmq1fe4c-jGX7qRUywvKA"
CROP_TYPE_LE_URL = "https://drive.google.com/uc?export=download&id=1w_i_BnCTOO3hYaw3uC0AKjpZr4bGKrwZ"
SOIL_TYPE_LE_URL = "https://drive.google.com/uc?export=download&id=1dKf0B9wE-KXZdzTVnNGosqptZ0e1Ly5W"

# ===============================
# DOWNLOAD HELPER
# ===============================
def download_file(url, save_path):
    print(f"Downloading {save_path} ...")
    r = requests.get(url)
    with open(save_path, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {save_path}")

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
    crop_model = joblib.load(os.path.join(MODEL_DIR, "crop_recommendation.joblib"))
    fert_model = joblib.load(os.path.join(MODEL_DIR, "fertilizer_model.joblib"))
    crop_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_crop.joblib"))
    fert_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_fert.joblib"))
    crop_type_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_crop_type.joblib"))
    soil_type_le = joblib.load(os.path.join(MODEL_DIR, "label_encoder_soil_type.joblib"))

    return crop_model, fert_model, crop_le, fert_le, crop_type_le, soil_type_le

@app.on_event("startup")
def startup_event():
    global CROP_MODEL, FERT_MODEL
    global CROP_LE, FERT_LE
    global CROP_TYPE_LE, SOIL_TYPE_LE

    print("Checking ML model files...")

    files = [
        ("crop_recommendation.joblib", CROP_MODEL_URL),
        ("fertilizer_model.joblib", FERT_MODEL_URL),
        ("label_encoder_crop.joblib", CROP_LE_URL),
        ("label_encoder_fert.joblib", FERT_LE_URL),
        ("label_encoder_crop_type.joblib", CROP_TYPE_LE_URL),
        ("label_encoder_soil_type.joblib", SOIL_TYPE_LE_URL),
    ]

    for filename, url in files:
        file_path = os.path.join(MODEL_DIR, filename)
        if not os.path.exists(file_path):
            download_file(url, file_path)

    print("Loading models...")
    (
        CROP_MODEL,
        FERT_MODEL,
        CROP_LE,
        FERT_LE,
        CROP_TYPE_LE,
        SOIL_TYPE_LE,
    ) = load_models()

    print("Models loaded successfully.")

# ===============================
# 🌱 CROP PREDICTION
# ===============================
@app.post("/predict/crop")
async def predict_crop(data: CropFeatures):
    try:
        features = [data.n, data.p, data.k, data.temperature, data.ph]
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
async def predict_fertilizer(data: FertilizerFeatures):
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

        return {"success": True, "prediction": fert_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# 💬 CHAT
# ===============================
@app.post("/chat")
async def chat(request: ChatRequest):
    if not client:
        return {"response": "AI service unavailable."}

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = await model.generate_content_async(request.message)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"AI service unavailable: {str(e)}"}

# ===============================
# HEALTH
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}
