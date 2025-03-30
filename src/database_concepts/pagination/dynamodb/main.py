import os
import boto3
import json
import base64
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError
from dotenv import load_dotenv 

load_dotenv()

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = "my-paginated-table"

app = FastAPI(title="DynamoDB Pagination Demo")

try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    table.load()
    print(f"Successfully connected to DynamoDB table: {DYNAMODB_TABLE_NAME}")
except Exception as e:
    print(f"An unexpected error occurred during DynamoDB initialization: {e}")
    table = None


class Item(BaseModel):
    id: str
    name: Optional[str] = None
    value: Optional[int] = None


class PaginatedResponse(BaseModel):
    items: List[Item]
    next_page_token: Optional[str]


def encode_key(key: Dict[str, Any]) -> str:
    json_key = json.dumps(key)
    return base64.urlsafe_b64encode(json_key.encode('utf-8')).decode('utf-8')


def decode_key(encoded_key: str) -> Optional[Dict[str, Any]]:
    print(f"Encoded Key {encoded_key}")
    if not encoded_key:
        return None
    try:
        json_key = base64.urlsafe_b64decode(encoded_key.encode('utf-8')).decode('utf-8')
        print(f"JSON Key {json_key}")
        return json.loads(json_key)
    except (TypeError, ValueError, json.JSONDecodeError, base64.binascii.Error) as e:
        print(f"Error decoding key: {e}")
        return None


@app.get("/items", response_model=PaginatedResponse)
def list_items(
    limit: int = Query(5, ge=1, le=100, description="Number of items per page"),
    next_page_token: Optional[str] = Query(None, description="Token from previous page response")
):
    if table is None:
         raise HTTPException(status_code=503, detail="DynamoDB service unavailable or table not found.")
    scan_kwargs = {
        'Limit': limit
    }
    exclusive_start_key = decode_key(next_page_token)
    print(f"Exclusive start key: {exclusive_start_key}")
    if exclusive_start_key is None and next_page_token is not None:
         raise HTTPException(status_code=400, detail="Invalid next_page_token format.")
    if exclusive_start_key:
        scan_kwargs['ExclusiveStartKey'] = exclusive_start_key
    try:
        response = table.scan(**scan_kwargs)
    except Exception as e:
        print(f"Unexpected error during scan: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    items_data = response.get('Items', [])
    validated_items = []
    for item_data in items_data:
        try:
            validated_items.append(Item(**item_data))
        except Exception as pydantic_error:
            print(f"Warning: Skipping item due to validation error: {item_data}. Error: {pydantic_error}")
    next_token = None
    
    last_evaluated_key = response.get('LastEvaluatedKey')
    print(f"Last Evaluated Key {last_evaluated_key}")
    if last_evaluated_key:
        next_token = encode_key(last_evaluated_key)
    
    return PaginatedResponse(
        items=validated_items,
        next_page_token=next_token
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
