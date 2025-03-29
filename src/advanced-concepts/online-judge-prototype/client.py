# client.py
import requests
import json

url = 'http://127.0.0.1:8000'

code = """
print("Hello, World!")
"""

data = {
    'code': code,
    'problem_id': 1,
    'user_id': 1
}

submit_response = requests.post(f'{url}/submit', json=data)
submission_data = submit_response.json()
submission_id = submission_data['submission_id']
print(f"Submission ID: {submission_id}")

status_response = requests.get(f'{url}/status/{submission_id}')
status_data = status_response.json()
status = status_data['status']
result = status_data.get('result')

print(f"Status: {status}")

if result:
    print(f"Result: {result}")