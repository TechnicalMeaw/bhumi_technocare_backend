from fastapi import UploadFile, HTTPException
import firebase_admin
from firebase_admin import credentials, storage
import uuid
from ..config import settings

# Initialize Firebase Admin SDK
_cred = credentials.Certificate("./venv/serviceAccountKey.json")
firebase_admin.initialize_app(_cred, {
    'storageBucket': settings.firebase_storage_bucket_name
})

async def upload_file(file: UploadFile):
    # Create a bucket object
    bucket = storage.bucket()

    # Create a blob object from the file name
    blob = bucket.blob(f"uploads/{uuid.uuid4()}-{file.filename}")

    # Read the file content and upload it
    contents = await file.read()  # Read the contents of the file
    blob.upload_from_string(contents, content_type=file.content_type)

    # Make the file publicly accessible (optional)
    blob.make_public()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "firebase_url": blob.public_url
    }

async def delete_file(firebase_url: str):
    # Parse the file path from the Firebase URL
    if not firebase_url.startswith(f"https://storage.googleapis.com/{settings.firebase_storage_bucket_name}/"):
        raise HTTPException(status_code=400, detail="Invalid Firebase URL")

    # Extract the file path from the URL
    file_path = firebase_url.replace(f"https://storage.googleapis.com/{settings.firebase_storage_bucket_name}/", '')

    # Create a bucket object
    bucket = storage.bucket()

    # Create a blob object with the file path
    blob = bucket.blob(file_path)

    # Check if the file exists
    if not blob.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Delete the file
    blob.delete()

    return True