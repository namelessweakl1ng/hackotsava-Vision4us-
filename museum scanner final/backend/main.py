import os
import io
import cv2
import numpy as np
from datetime import datetime
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from PIL import Image

from dotenv import load_dotenv
from db.database import get_collection
from utils.image_matcher import ORBMatcher

# -------------------- setup --------------------
load_dotenv()

app = FastAPI(title="Museum ORB Scanner", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # lock down to your frontend origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REFERENCE_DIR = os.path.join("data", "reference")
matcher = ORBMatcher(REFERENCE_DIR)
collection = get_collection()

# Fallback info if DB missing a record
fallback_info = {
    "monalisa": {
        "title": "Mona Lisa",
        "artist": "Leonardo da Vinci",
        "year": 1503,
        "description": "Portrait known for its enigmatic smile."
    },
    "the_last_supper": {
        "title": "The Last Supper",
        "artist": "Leonardo da Vinci",
        "year": 1498,
        "description": "Jesus and the Twelve Apostles at the betrayal moment."
    },
    "the_scream": {
        "title": "The Scream",
        "artist": "Edvard Munch",
        "year": 1893,
        "description": "Iconic expressionist portrayal of anxiety."
    },
    "the_starry_night": {
        "title": "The Starry Night",
        "artist": "Vincent van Gogh",
        "year": 1889,
        "description": "Swirling sky over Saint-Rémy-de-Provence."
    }
}

# -------------------- routes --------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>🎨 Museum ORB Scanner Backend</h1>
    <p>Server is running. Try <a href="/docs">/docs</a> to test the API.</p>
    """

@app.get("/api/labels")
async def labels():
    return {"labels": list(matcher.index.keys())}

@app.post("/api/scan")
async def scan(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        # PIL → numpy BGR (OpenCV)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img_np = np.array(img)[:, :, ::-1]  # RGB -> BGR

        best_label, score, top = matcher.match(img_np)

        # simple confidence threshold (tune as needed)
        MIN_SCORE = 0.05  # with 4 references this is usually fine; adjust with your images
        if not best_label or score < MIN_SCORE:
            return {
                "artwork_id": None,
                "matched_label": None,
                "score": float(score),
                "message": "No confident match. Try a clearer photo."
            }

        # get details from DB if present
        record = collection.find_one({"label": best_label}, {"_id": 0}) or fallback_info.get(best_label, {})
        response = {
            "artwork_id": best_label,
            "matched_label": best_label,
            "score": float(score),
            "details": record,
            "alternatives": [{"label": l, "score": float(s)} for l, s in top]
        }

        # basic analytics log (optional)
        try:
            collection.database["scan_logs"].insert_one({
                "label": best_label,
                "score": float(score),
                "top": top,
                "ts": datetime.utcnow()
            })
        except Exception:
            pass

        return response

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# For local run:  uvicorn main:app --reload
