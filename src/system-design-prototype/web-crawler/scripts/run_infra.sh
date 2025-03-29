#!/bin/bash
# scripts/run_infra.sh

# Load environment variables
set -a # automatically export all variables
source ../.env
set +a

NETWORK_NAME="webcrawler-net"
MINIO_DATA_DIR="$(pwd)/minio_data" # Create a local dir for persistence
MONGO_DATA_DIR="$(pwd)/mongo_data" # Create a local dir for persistence
REDIS_DATA_DIR="$(pwd)/redis_data" # Create a local dir for persistence

# Create network if it doesn't exist
docker network inspect $NETWORK_NAME >/dev/null 2>&1 || \
    docker network create $NETWORK_NAME

# Ensure data directories exist
mkdir -p $MINIO_DATA_DIR $MONGO_DATA_DIR $REDIS_DATA_DIR

echo "Starting infrastructure containers..."

# RabbitMQ (for URL Queue & Parsing Queue)
echo "Starting RabbitMQ..."
docker run -d --rm \
  --network $NETWORK_NAME \
  --hostname $RABBITMQ_HOST \
  --name $RABBITMQ_HOST \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=$RABBITMQ_DEFAULT_USER \
  -e RABBITMQ_DEFAULT_PASS=$RABBITMQ_DEFAULT_PASS \
  rabbitmq:3.11-management-alpine

# MongoDB (for URL Metadata)
echo "Starting MongoDB..."
docker run -d --rm \
  --network $NETWORK_NAME \
  --name $MONGO_HOST \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=$MONGO_INITDB_ROOT_USERNAME \
  -e MONGO_INITDB_ROOT_PASSWORD=$MONGO_INITDB_ROOT_PASSWORD \
  -v $MONGO_DATA_DIR:/data/db \
  mongo:6.0

# Redis (for Rate Limiting / Caching / Politeness)
echo "Starting Redis..."
docker run -d --rm \
  --network $NETWORK_NAME \
  --name $REDIS_HOST \
  -p 6379:6379 \
  -v $REDIS_DATA_DIR:/data \
  redis:7-alpine redis-server --save 60 1 --loglevel warning

# MinIO (for HTML Storage)
echo "Starting MinIO..."
docker run -d --rm \
  --network $NETWORK_NAME \
  --name $MINIO_HOST \
  -p $MINIO_PORT:9000 \
  -p 9090:9090 \
  -e MINIO_ROOT_USER=$MINIO_ROOT_USER \
  -e MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD \
  -e MINIO_DEFAULT_BUCKETS=$MINIO_BUCKET \
  -v $MINIO_DATA_DIR:/data \
  minio/minio server /data --console-address ":9090"

echo "Infrastructure containers should be starting."
echo "MinIO Console: http://localhost:9090"
echo "RabbitMQ Console: http://localhost:15672 (user: $RABBITMQ_DEFAULT_USER)"

# Optional: Wait for services (basic check)
echo "Waiting a few seconds for services to initialize..."
sleep 15

echo "Infrastructure setup complete."