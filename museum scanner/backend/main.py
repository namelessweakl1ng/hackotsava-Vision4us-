from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import os, json, random, time
from bson import ObjectId  #  Import this to handle MongoDB ObjectIds

# ------------------------------
#  Setup
# ------------------------------
load_dotenv()
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# MongoDB connection
mongo_uri = "mongodb://localhost:27017"
mongo_client = MongoClient(mongo_uri)
db = mongo_client["passmgr"]
collection = db["museum"]

# ------------------------------
#  Analyze Painting Endpoint
# ------------------------------
@app.post("/api/analyze-painting")
async def analyze_painting(file: UploadFile = File(...)):
    try:
        # Read image
        image_data = await file.read()
        img = Image.open(BytesIO(image_data))
        temp_path = f"temp_{int(time.time())}.png"
        img.save(temp_path)

        # Upload to Gemini
        uploaded = client.files.upload(file=temp_path)
        os.remove(temp_path)

        # Ask Gemini for description
        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=[
                "Describe this artwork in detail — artist, time period, style, and historical/cultural background if identifiable.",
                uploaded
            ]
        )

        description = response.text or "No description found."

        # Mock YouTube video link


        # Store result in MongoDB
        record = {
            "filename": file.filename,
            "description": description,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        result = collection.insert_one(record)

        # ✅ Convert ObjectId to string for JSON
        record["_id"] = str(result.inserted_id)

        return JSONResponse({
            "status": "success",
            "message": "Painting analyzed and stored successfully.",
            "data": record
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
