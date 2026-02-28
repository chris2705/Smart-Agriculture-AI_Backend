Backend FastAPI for Smart Agriculture

ENV VARS (recommended):
- MODEL_STORAGE: "local" or "firebase"
- FIREBASE_BUCKET: <bucket name> (if using firebase)
- MODEL_REMOTE_PREFIX: path inside bucket e.g. "models/"
- GOOGLE_APPLICATION_CREDENTIALS: path to service account json (for firebase)

Run locally (with local models present under ml/models/):
1. python -m venv .venv
2. .\.venv\Scripts\Activate.ps1
3. pip install -r requirements.txt
4. uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
