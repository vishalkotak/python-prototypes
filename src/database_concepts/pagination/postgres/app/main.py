import os
import psycopg2
import psycopg2.extras 
from fastapi import FastAPI, Query, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import math
import datetime
from dotenv import load_dotenv


load_dotenv()

DB_NAME = os.getenv("DB_NAME", "mydatabase")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to database: {e}")
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    

class Item(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime.datetime


class PaginatedOffsetResponse(BaseModel):
    items: List[Item]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedKeysetResponse(BaseModel):
    items: List[Item]
    # Assuming 'id' is the cursor
    next_cursor: Optional[int]


app = FastAPI(title="Postgres Pagination Demo")


@app.get(
    "/items_offset",
    response_model=PaginatedOffsetResponse,
    summary="Get items using Offset Pagination",
    tags=["Pagination"]
)
def get_items_offset(
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    conn = get_db_connection()
    items_list = []
    total_items = 0
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM items;")
            total_items = cur.fetchone()[0]
            if total_items == 0:
                return PaginatedOffsetResponse(items=[], page=page,
                    page_size=page_size, total_items=0, total_pages=0
                )
            offset = (page - 1) * page_size
            total_pages = math.ceil(total_items / page_size)
            query = """
                SELECT id, name, description, created_at
                FROM items
                ORDER BY id ASC
                LIMIT %s OFFSET %s;
            """
            cur.execute(query, (page_size, offset))
            print(f"Page Size {page_size} and Offset: {offset}")
            results = cur.fetchall()
            print(f"{results}")
            items_list = [Item(**row) for row in results]
    except psycopg2.Error as e:
        print(f"Database error fetching items (offset): {e}")
        # Consider more specific error handling based on the exception type
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close() 
    return PaginatedOffsetResponse(
        items=items_list,
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', host="127.0.0.1", port=8000, reload=True)