from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)

db = client["ai_pdf_reader"]

#collections
users_collection = db["users"] 
files_collection = db["files"] 

#indexes
try:
    users_collection.create_index("uid", unique=True)
    files_collection.create_index("user_id")
    files_collection.create_index([("user_id", 1), ("uploaded_at", -1)])
    print("Database indexes created successfully")
except Exception as e:
    print(f"Index creation warning: {e}")