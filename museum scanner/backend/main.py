from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from pymongo import MongoClient
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import os, json, random, time
from bson import ObjectId  # Import this to handle MongoDB ObjectIds

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

        # Ask Gemini for description in JSON format
        prompt = """Please analyze the artwork and provide a JSON object with the following keys:
        - "artist": string or null
        - "time_period": string or null
        - "style": string or null
        - "historical_context": string or null
        - "description": string

        The JSON object:"""

        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=[
                prompt,
                uploaded
            ]
        )

        # Try to parse the response as JSON
        try:
            # Extract JSON from the response
            start = response.text.find('{')
            end = response.text.rfind('}') + 1
            json_str = response.text[start:end]
            data = json.loads(json_str)
        except Exception as e:
            # If parsing fails, use the entire response as description
            data = {
                "artist": None,
                "time_period": None,
                "style": None,
                "historical_context": None,
                "description": response.text
            }

        # Store result in MongoDB
        record = {
            "filename": file.filename,
            "artist": data.get("artist"),
            "time_period": data.get("time_period"),
            "style": data.get("style"),
            "historical_context": data.get("historical_context"),
            "description": data.get("description"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        result = collection.insert_one(record)

        # Convert ObjectId to string for JSON
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
