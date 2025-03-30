import os
import logging
from datetime import datetime, timezone
from typing import Optional, List
import uuid

import psycopg2
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(title="Sync Service")

DB_NAME = os.getenv("DB_NAME", "filesync")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")
    
class FileMetadataChange(BaseModel):
    file_id: uuid.UUID
    file_name: str
    last_modified: datetime
    size_bytes: Optional[int] = None
    class Config:
        orm_mode = True

    
class ChangesResponse(BaseModel):
    changes: List[FileMetadataChange]


@app.get("/changes", response_model=ChangesResponse)
async def get_changes(
    timestamp: Optional[datetime] = Query(None, description="ISO 8601 timestamp (UTC/Zulu 'Z' preferred). Returns changes since this time.")
):
    if timestamp is None:
        timestamp = datetime.fromtimestamp(0, tz=timezone.utc)
        logging.warning("No timestamp provided, defaulting to epoch.")
    else:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logging.info(f"Checking for changes since: {timestamp.isoformat()}")
        cursor.execute(
            """
            SELECT file_id, file_name, last_modified, size_bytes
            FROM file_metadata
            WHERE last_modified > %s
            ORDER BY last_modified ASC
            """,
            (timestamp,)
        )
        changed_files_data = cursor.fetchall()
        logging.info(f"Found {len(changed_files_data)} change(s) since {timestamp.isoformat()}")
        return ChangesResponse(changes=changed_files_data)
    except Exception as e:
        logging.error(f"Generic error querying changes: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


if __name__ == "__main__":
    uvicorn.run("sync_service:app", host="0.0.0.0", port=8001, reload=True)