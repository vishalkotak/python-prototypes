import os
import uuid
import io
import logging
from datetime import datetime, timedelta, timezone

import psycopg2
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, Path
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(title="File Service")

DB_NAME = os.getenv("DB_NAME", "filesync")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "rawfiles")
MINIO_SECURE = False
PRESIGNED_URL_EXPIRY_MINUTES = 15

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )
    found = minio_client.bucket_exists(MINIO_BUCKET)
    if not found:
        logging.warning(f"MinIO bucket '{MINIO_BUCKET}' not found. Please create it.")
        try:
            minio_client.make_bucket(MINIO_BUCKET)
            logging.info(f"Bucket '{MINIO_BUCKET}' created successfully.")
        except Exception as e:
            logging.error(f"Could not automatically create bucket '{MINIO_BUCKET}': {e}")
    else:
        logging.info(f"Connected to MinIO bucket '{MINIO_BUCKET}'")
except Exception as e:
    logging.error(f"MinIO client initialization error: {e}")
    raise HTTPException(status_code=500, detail=f"MinIO client initialization error: {e}")


class GenerateUploadUrlRequest(BaseModel):
    filename: str
    content_type: Optional[str] = 'application/octet-stream'


class CommitUploadRequest(BaseModel):
    file_id: uuid.UUID
    filename: str
    size_bytes: int


@app.post("/generate_upload_url")
async def generate_upload_url(request_data: GenerateUploadUrlRequest):
    try:
        file_id = uuid.uuid4()
        original_filename = request_data.filename
        minio_object_name = f"uploads/{file_id}/{original_filename}"
        presigned_url = minio_client.presigned_put_object(
            MINIO_BUCKET,
            minio_object_name,
            expires=timedelta(minutes=PRESIGNED_URL_EXPIRY_MINUTES)
        )
        logging.info(f"Generated pre-signed PUT URL for file_id: {file_id}, object: {minio_object_name}")
        return {
            "file_id": str(file_id),
            "upload_url": presigned_url,
            "object_name": minio_object_name
        }
    except Exception as e:
        logging.error(f"Generic error generating pre-signed URL: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/commit_upload", status_code=201) 
async def commit_upload(commit_data: CommitUploadRequest):
    conn = None
    cursor = None
    file_id = commit_data.file_id
    filename = commit_data.filename
    size_bytes = commit_data.size_bytes
    minio_object_name = f"uploads/{file_id}/{filename}"
    try:
        stat = minio_client.stat_object(MINIO_BUCKET, minio_object_name)
        if stat.size != size_bytes:
            logging.warning(f"Committed size ({size_bytes}) differs from MinIO size ({stat.size}) for {file_id}")
        logging.info(f"Verified object {minio_object_name} exists in MinIO before DB commit.")
    except S3Error as e:
        logging.error(f"Failed to verify object {minio_object_name} exists in MinIO before commit: {e}")
        raise HTTPException(status_code=400, detail=f"Upload commit failed: Object not found in storage or verification error ({e})")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now(timezone.utc)
        cursor.execute(
            """
            INSERT INTO file_metadata (file_id, file_name, minio_path, last_modified, size_bytes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(file_id), filename, minio_object_name, timestamp, size_bytes)
        )
        conn.commit()
        logging.info(f"Metadata committed to DB for file_id: {file_id}")

        return {
            "message": "Upload committed successfully",
            "file_id": str(file_id)
        }
    except HTTPException as http_exc:
         raise http_exc
    except Exception as e:
        logging.error(f"Generic error during commit: {e}")
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during commit: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@app.get("/get_file/{file_id}")
async def get_file(file_id: uuid.UUID = Path(...)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT file_name, minio_path, size_bytes FROM file_metadata WHERE file_id = %s", (str(file_id),))
        metadata = cursor.fetchone()
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        minio_path = metadata['minio_path']
        file_name = metadata['file_name']
        logging.info(f"Streaming file {file_name} (ID: {file_id}) from MinIO path: {minio_path}")
        try:
            data_stream = minio_client.get_object(MINIO_BUCKET, minio_path)

            return StreamingResponse(
                data_stream.stream(32*1024),
                media_type='application/octet-stream',
                headers={'Content-Disposition': f'attachment; filename="{file_name}"'}
            )
        except S3Error as s3e:
             logging.error(f"MinIO Error retrieving object {minio_path}: {s3e}")
             if "NoSuchKey" in str(s3e):
                 raise HTTPException(status_code=404, detail="File data not found in storage")
             else:
                 raise HTTPException(status_code=500, detail=f"Storage Error: {s3e}")
        finally:
            if 'data_stream' in locals() and hasattr(data_stream, 'release_conn'):
                data_stream.release_conn()
    except Exception as e:
        logging.error(f"Generic error during download: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


if __name__ == "__main__":
    uvicorn.run("file_service:app", host="0.0.0.0", port=8000, reload=True)