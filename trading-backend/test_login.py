#!/usr/bin/env python
"""Test login API"""

import requests
import json

url = "http://localhost:8001/api/v1/auth/login"
payload = {
    "email": "myid998877@gmail.com",
    "password": "Test1234!"
}

print("Testing login API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 50)

response = requests.post(url, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
