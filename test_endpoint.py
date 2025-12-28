import requests
try:
    print("Testing GET /settings/network-defaults...")
    r = requests.get("http://localhost:8000/settings/network-defaults", timeout=2)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
