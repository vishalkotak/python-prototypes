import os
import uuid
import io
import logging
from datetime import datetime

import psycopg2
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, Path
from fastapi.responses import StreamingResponse
from minio import Minio
from minio.error import S3Error
from psycopg2.extras import RealDictCursor

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


@app.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file sent.")
    if not file.filename:
         raise HTTPException(status_code=400, detail="File name is missing.")
    conn = None
    cursor = None
    file_id = uuid.uuid4()
    original_filename = file.filename
    minio_object_name = f"uploads/{file_id}/{original_filename}"
    try:
        contents = await file.read()
        file_size = len(contents)
        file_stream = io.BytesIO(contents)
        logging.info(f"Uploading {original_filename} ({file_size} bytes) to MinIO as {minio_object_name}")
        minio_client.put_object(
            MINIO_BUCKET,
            minio_object_name,
            file_stream,
            length=file_size,
            content_type=file.content_type
        )
        logging.info(f"Successfully uploaded to MinIO.")
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now(datetime.now().astimezone().tzinfo)
        cursor.execute(
            """
            INSERT INTO file_metadata (file_id, file_name, minio_path, last_modified, size_bytes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(file_id), original_filename, minio_object_name, timestamp, file_size)
        )
        conn.commit()
        logging.info(f"Metadata stored in DB for file_id: {file_id}")
        return {
            "message": "File uploaded successfully",
            "file_id": str(file_id),
            "filename": original_filename,
            "size": file_size
        }
    except Exception as e:
        logging.error(f"Generic error during upload: {e}")
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        await file.close()


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