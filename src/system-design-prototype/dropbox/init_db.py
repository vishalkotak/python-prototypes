import psycopg2
import os
from dotenv import load_dotenv
import sys

load_dotenv() # Load environment variables from .env file

DB_NAME = os.getenv("DB_NAME", "filesync")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
# Use 'localhost' if running this script OUTSIDE docker,
# use 'postgres-db' if running INSIDE docker network
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Establishes connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Database connection successful")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}", file=sys.stderr)
        sys.exit(1) # Exit if DB connection fails

def initialize_database():
    """Creates the file_metadata table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_id UUID PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL,
                minio_path VARCHAR(1024) NOT NULL,
                last_modified TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                size_bytes BIGINT
            );
        """)
        conn.commit()
        print("Table 'file_metadata' checked/created successfully.")

        # Optional: Create an index for faster timestamp lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_modified ON file_metadata (last_modified);
        """)
        conn.commit()
        print("Index 'idx_last_modified' checked/created successfully.")

    except Exception as e:
        print(f"Error initializing database table: {e}", file=sys.stderr)
        conn.rollback() # Rollback changes on error
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    print("Initializing database...")
    initialize_database()
    print("Database initialization complete.")