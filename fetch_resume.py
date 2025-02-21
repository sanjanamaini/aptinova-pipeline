import os
import requests
from pymongo import MongoClient

# MongoDB connection details
MONGO_URI = "mongodb+srv://ayonsarkar380:ayon78965432@cluster0.pqlngl0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Update with your actual MongoDB URI
DB_NAME = "aptinova"
COLLECTION_NAME = "resumes"

# Directory to save PDFs
SAVE_DIR = "resumeDownloads"
os.makedirs(SAVE_DIR, exist_ok=True)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["aptinova"]
collection = db["resumes"]

# Fetch all documents with URLs
for doc in collection.find({}, {"url": 1, "filename": 1}):
    url = doc.get("url")
    filename = doc.get("filename", f"{doc['_id']}.pdf")  # Use filename if available, else use _id

    if url:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_path = os.path.join(SAVE_DIR, filename)
                with open(file_path, "wb") as pdf_file:
                    for chunk in response.iter_content(1024):
                        pdf_file.write(chunk)
                print(f"Downloaded: {file_path}")
            else:
                print(f"Failed to download {url}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error downloading {url}: {e}")

print("Download completed.")