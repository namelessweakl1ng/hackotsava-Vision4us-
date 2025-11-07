from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "museum_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "artworks")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col = db[COLLECTION_NAME]

# Clear & seed
col.delete_many({})

docs = [
    {
        "label": "monalisa",
        "title": "Mona Lisa",
        "artist": "Leonardo da Vinci",
        "year": 1503,
        "description": "Portrait of Lisa Gherardini, famed for the enigmatic smile.",
        "location": "Louvre Museum, Paris",
        "style": "Renaissance"
    },
    {
        "label": "the_last_supper",
        "title": "The Last Supper",
        "artist": "Leonardo da Vinci",
        "year": 1498,
        "description": "Jesus with the Twelve Apostles, the betrayal moment.",
        "location": "Santa Maria delle Grazie, Milan",
        "style": "Renaissance"
    },
    {
        "label": "the_scream",
        "title": "The Scream",
        "artist": "Edvard Munch",
        "year": 1893,
        "description": "Expressionist depiction of anxiety and existential dread.",
        "location": "National Gallery, Oslo",
        "style": "Expressionism"
    },
    {
        "label": "the_starry_night",
        "title": "The Starry Night",
        "artist": "Vincent van Gogh",
        "year": 1889,
        "description": "Swirling night sky painted from memory at Saint-Rémy.",
        "location": "MoMA, New York",
        "style": "Post-Impressionism"
    }
]

col.insert_many(docs)
print("✅ Database initialized with 4 artworks.")
