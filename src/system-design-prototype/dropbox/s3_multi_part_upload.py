import boto3
import os
import sys
import math
from botocore.exceptions import ClientError

# --- Configuration ---
AWS_REGION = "us-east-1" 
S3_BUCKET_NAME = "your-bucket-name"
FILE_TO_UPLOAD_PATH = "/path/to/your/large_file.zip"
S3_OBJECT_KEY = "uploads/large_file.zip" 

PART_SIZE_BYTES = 8 * 1024 * 1024
# ---------------------

def upload_large_file_multipart(bucket_name, object_key, file_path, part_size):
    """Uploads a large file to S3 using multipart upload."""

    s3_client = boto3.client("s3", region_name=AWS_REGION)
    upload_id = None # Initialize upload_id outside try block

    try:
        # 1. Initiate Upload
        print(f"Initiating multipart upload for {object_key}...")
        response = s3_client.create_multipart_upload(
            Bucket=bucket_name,
            Key=object_key
            # Add other parameters like ACL, ContentType if needed
            # ContentType= 'application/octet-stream' # Example
        )
        upload_id = response['UploadId']
        print(f"Upload initiated successfully. Upload ID: {upload_id}")

        # --- Calculate total parts ---
        file_size = os.path.getsize(file_path)
        total_parts = math.ceil(file_size / part_size)
        print(f"File size: {file_size} bytes, Part size: {part_size} bytes, Total parts: {total_parts}")

        # --- 2. Upload Parts ---
        parts_info = [] # List to store {PartNumber, ETag} dicts
        uploaded_bytes = 0

        with open(file_path, 'rb') as f:
            for part_number in range(1, total_parts + 1):
                print(f"Reading part {part_number}/{total_parts}...")
                part_data = f.read(part_size)
                if not part_data:
                    break # Should not happen if total_parts calculation is correct

                print(f"Uploading part {part_number}/{total_parts}...")
                try:
                    part_response = s3_client.upload_part(
                        Bucket=bucket_name,
                        Key=object_key,
                        UploadId=upload_id,
                        PartNumber=part_number,
                        Body=part_data
                    )
                    etag = part_response['ETag']
                    parts_info.append({'PartNumber': part_number, 'ETag': etag})
                    uploaded_bytes += len(part_data)
                    print(f"Part {part_number} uploaded. ETag: {etag}. Progress: {uploaded_bytes}/{file_size} bytes")

                except ClientError as e:
                    print(f"Error uploading part {part_number}: {e}")
                    # Consider adding retry logic here for transient errors
                    raise # Re-raise to trigger the abort

        # --- 3. Complete Upload ---
        if len(parts_info) == total_parts:
             print("\nCompleting multipart upload...")
             complete_response = s3_client.complete_multipart_upload(
                 Bucket=bucket_name,
                 Key=object_key,
                 UploadId=upload_id,
                 MultipartUpload={'Parts': parts_info}
             )
             print("Multipart upload completed successfully!")
             print(f"Object URL: s3://{bucket_name}/{object_key}")
             print(f"Full response: {complete_response}")
        else:
            # This case should ideally not be reached if logic is correct
            # but acts as a safeguard
            raise Exception(f"Mismatch in uploaded parts count. Expected {total_parts}, got {len(parts_info)}. Aborting.")


    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if upload_id:
            try:
                print(f"Aborting multipart upload (ID: {upload_id})...")
                s3_client.abort_multipart_upload(
                    Bucket=bucket_name,
                    Key=object_key,
                    UploadId=upload_id
                )
                print("Upload aborted successfully.")
            except ClientError as abort_e:
                print(f"Could not abort upload {upload_id}. Error: {abort_e}")
        return False # Indicate failure

    return True # Indicate success


if __name__ == "__main__":

    if not os.path.exists(FILE_TO_UPLOAD_PATH):
        print(f"Error: File not found at {FILE_TO_UPLOAD_PATH}")
        sys.exit(1)
    if PART_SIZE_BYTES < 5 * 1024 * 1024:
         print(f"Error: Part size must be at least 5MB.")
         sys.exit(1)

    print("Starting S3 large file upload...")
    success = upload_large_file_multipart(
        S3_BUCKET_NAME,
        S3_OBJECT_KEY,
        FILE_TO_UPLOAD_PATH,
        PART_SIZE_BYTES
    )

    if success:
        print("\nUpload finished successfully.")
    else:
        print("\nUpload failed.")
        sys.exit(1)