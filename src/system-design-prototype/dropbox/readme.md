# Simple File Sync Backend Prototype

This project prototypes the backend services for a simple file synchronization system, similar to Dropbox or Google Drive, based on the provided architecture diagram.

It uses Python, FastAPI, PostgreSQL, and MinIO (as an S3 alternative). Docker is used to run the backing services (PostgreSQL and MinIO). The upload mechanism uses pre-signed URLs for direct client-to-storage uploads.

## Architecture Overview

1.  **Client Application (`client_app.py`):** Simulates user actions like uploading, downloading, and checking for file changes.
2.  **File Service (`file_service.py`):** A FastAPI application responsible for:
    * Generating pre-signed URLs for uploads to MinIO.
    * Committing metadata to PostgreSQL after successful uploads.
    * Handling file download requests (streaming data from MinIO).
3.  **Sync Service (`sync_service.py`):** A FastAPI application responsible for:
    * Querying the PostgreSQL database for file metadata changes since a given timestamp.
4.  **PostgreSQL:** A relational database (run in Docker) storing file metadata (ID, name, path in MinIO, timestamp, size).
5.  **MinIO:** An S3-compatible object storage server (run in Docker) storing the raw file data.

**Workflow:**

* **Upload:**
    1.  Client requests an upload URL from the File Service (`/generate_upload_url`), providing the filename.
    2.  File Service generates a unique file ID and a pre-signed PUT URL from MinIO.
    3.  File Service returns the file ID and the pre-signed URL to the Client.
    4.  Client PUTs the file data directly to the received MinIO URL.
    5.  Upon successful upload to MinIO, the Client notifies the File Service (`/commit_upload`), providing the file ID, filename, and size.
    6.  File Service writes the file's metadata to the PostgreSQL database.
* **Check for Changes:**
    1.  Client calls the Sync Service (`/changes`), optionally providing a timestamp.
    2.  Sync Service queries PostgreSQL for metadata of files modified after the timestamp.
    3.  Sync Service returns the list of changed file metadata.
* **Download:**
    1.  Client requests a file download from the File Service (`/get_file/{file_id}`).
    2.  File Service retrieves metadata from PostgreSQL to find the file's path in MinIO.
    3.  File Service fetches the file object from MinIO and streams it back to the client.

## Prerequisites

* Docker Engine (or Docker Desktop)
* Python 3.8+
* `pip` (Python package installer)

## Setup Instructions

1.  **Clone Repository:** (Assuming the code is in a Git repository)
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create `.env` File:** (Optional but recommended)
    Create a file named `.env` in the project root for configuration. See `.env.example` or use the following template:
    ```text
    DB_NAME=filesync
    DB_USER=user
    DB_PASSWORD=mysecretpassword
    DB_HOST=localhost
    DB_PORT=5432

    MINIO_ENDPOINT=localhost:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin
    MINIO_BUCKET=rawfiles
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(`requirements.txt` should contain `fastapi`, `uvicorn[standard]`, `psycopg2-binary`, `minio`, `requests`, `python-dotenv`, `python-multipart`)*

4.  **Start Backing Services (Docker):**
    Open a terminal and run:
    ```bash
    # Create a docker network (if not already present)
    docker network create file-sync-net

    # Run PostgreSQL container
    docker run --name postgres-db \
      --network file-sync-net \
      -e POSTGRES_PASSWORD=mysecretpassword \
      -e POSTGRES_USER=user \
      -e POSTGRES_DB=filesync \
      -p 5432:5432 \
      -v postgres_data:/var/lib/postgresql/data \
      -d postgres:15

    # Run MinIO container
    docker run --name minio-storage \
      --network file-sync-net \
      -e MINIO_ROOT_USER=minioadmin \
      -e MINIO_ROOT_PASSWORD=minioadmin \
      -p 9000:9000 \
      -p 9001:9001 \
      -v minio_data:/data \
      -d minio/minio server /data --console-address ":9001"
    ```
    *Note:* Volumes `postgres_data` and `minio_data` are used for persistence.

5.  **Create MinIO Bucket:**
    * Access the MinIO Console in your browser: `http://localhost:9001`
    * Log in with Access Key `minioadmin` and Secret Key `minioadmin`.
    * Navigate to "Buckets" and click "Create Bucket".
    * Enter the bucket name `rawfiles` (as configured in `.env` and code) and create it.

6.  **Initialize Database Schema:**
    Run the initialization script once the PostgreSQL container is running:
    ```bash
    python init_db.py
    ```
    This script creates the `file_metadata` table.

## Running the Services

Open two separate terminals in the project root directory.

* **Terminal 1: Start File Service**
    ```bash
    poetry run python file_service.py
    ```

* **Terminal 2: Start Sync Service**
    ```bash
    poetry run python sync_service.py
    ```

## Running the Client Simulation

Open a third terminal in the project root directory.

```bash
python client_app.py