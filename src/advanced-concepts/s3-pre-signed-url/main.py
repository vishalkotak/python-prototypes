import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = 'my-signed-url-test-bucket'

def main(file_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': file_name,
                'ContentType': 'text/plain'
            },
            ExpiresIn=3600   
        )
        print(f"url: {response}")
    except Exception as e:
        print(f"Error getting presigned url: {e}")


FILE_NAME = 'test.txt'

main(FILE_NAME)