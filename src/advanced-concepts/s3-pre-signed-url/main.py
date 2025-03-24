import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = 'my-signed-url-test-bucket'

def generate_presigned_url(file_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(
            # put_object for uploading file.
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_name,
                # Content type is needed to upload file
                # 'ContentType': 'text/plain'
            },
            ExpiresIn=3600   
        )
        return response
    except Exception as e:
        print(f"Error getting presigned url: {e}")


def upload_file_to_presigned_url(url, file_path):
    try:
        with open(file_path, 'r') as f:
            headers = {'Content-Type': 'text/plain'}
            response = requests.put(url, data=f, headers=headers)
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print(f"❌ Upload failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error uploading file: {e}")

def read_file_from_presigned_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ Reading successful!")
            print(f"File contents: {response.content}")
            print(response.text)  # or response.content for binary
        else:
            print(f"❌ Reading failed! Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error reading file: {e}")

FILE_NAME = 'data/test.txt'

presigned_url = generate_presigned_url(FILE_NAME)
if presigned_url:
    print(f"Generated URL: {presigned_url}")
    # upload_file_to_presigned_url(presigned_url, FILE_NAME)
    read_file_from_presigned_url(presigned_url)