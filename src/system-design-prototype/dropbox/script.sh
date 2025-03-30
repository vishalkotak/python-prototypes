# Create a docker network (if you haven't already)
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

# --- Wait a few seconds for DB and MinIO to start ---

# REMINDER: Manually create the MinIO bucket 'rawfiles' via the console
# Access MinIO console at http://localhost:9001 (use minioadmin/minioadmin)