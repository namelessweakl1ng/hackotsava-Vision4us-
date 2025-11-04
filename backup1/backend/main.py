from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import os, json, time, re
from bson import ObjectId

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["database1"]
collection = db["artworks"]

def extract_json_from_text(text: str):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return None

@app.post("/api/analyze-painting")
async def analyze_painting(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        img = Image.open(BytesIO(image_data))
        temp_path = f"temp_{int(time.time())}.png"
        img.save(temp_path)
        uploaded = client.files.upload(file=temp_path)
        os.remove(temp_path)
        prompt = """
        You are an expert art historian. Analyze the provided artwork image and return ONLY a valid JSON object with these keys:
        {
          "artist": "Full name of the artist if identifiable, or 'Unknown'",
          "time_period": "Approximate century or movement (e.g., 'Renaissance, 15th century')",
          "style": "Artistic style or movement (e.g., Impressionism, Cubism)",
          "historical_context": "Brief paragraph about cultural and historical context",
          "medium": "Likely medium or material (e.g., oil on canvas, watercolor, fresco)",
          "description": "Detailed summary of the artwork’s composition, subject, colors, and features."
        }
        Respond ONLY with valid JSON and nothing else.
        """
        response = client.models.generate_content(model="models/gemini-2.0-flash", contents=[prompt, uploaded])
        data = extract_json_from_text(response.text.strip())
        if not data:
            fallback = client.models.generate_content(model="models/gemini-2.0-flash", contents=["Describe this artwork with details on artist, period, style, medium, and meaning.", uploaded])
            data = {"artist": "Unknown", "time_period": "Unknown", "style": "Unknown", "historical_context": "Unknown", "medium": "Unknown", "description": fallback.text.strip()}
        for key in ["artist", "time_period", "style", "historical_context", "medium", "description"]:
            if not data.get(key): data[key] = "Unknown"
        record = {"filename": file.filename, **data, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        result = collection.insert_one(record)
        record["_id"] = str(result.inserted_id)
        return JSONResponse({"status": "success", "message": "Painting analyzed and stored successfully.", "data": record})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
