# client.py
import requests
import json

url = 'http://127.0.0.1:8000/submit'  # FastAPI URL

code = """
print("Hello, World!")
"""

data = {
    'code': code,
    'problem_id': 1,
    'user_id': 1
}

response = requests.post(url, json=data)
print(response.json())