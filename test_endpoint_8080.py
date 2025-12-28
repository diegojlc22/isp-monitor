import requests
try:
    print("Testing GET http://127.0.0.1:8080/api/settings/network-defaults...")
    # Not creating separate session, just simple get
    # Note: frontend performs GET /api/settings/network-defaults via proxy /api/...
    # Backend router has prefix="/settings" inside APP which includes router with prefix="/api"
    # Wait, main.py: app.include_router(settings.router, prefix="/api")
    # settings.py: router = APIRouter(prefix="/settings")
    # So final path is /api/settings/network-defaults
    r = requests.get("http://127.0.0.1:8080/api/settings/network-defaults", timeout=2)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
