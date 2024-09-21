from fastapi import UploadFile
import firebase_admin
from firebase_admin import credentials, storage
import uuid

# Initialize Firebase Admin SDK
_cred = credentials.Certificate("./venv/serviceAccountKey.json")
firebase_admin.initialize_app(_cred, {
    'storageBucket': 'bhumi-infocare.appspot.com'
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