import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_pdf_to_cloudinary(file_path: str) -> str:
    response = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        folder="pdf_uploads/"
    )
    return response.get("secure_url")
