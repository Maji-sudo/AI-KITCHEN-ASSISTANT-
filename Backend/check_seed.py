import urllib.request, json

def get(url, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

BASE = "http://127.0.0.1:8000/api/v1"

post(f"{BASE}/auth/request-otp", {"phone": "+919876543210"})
auth = post(f"{BASE}/auth/verify-otp", {"phone": "+919876543210", "otp": "123456"})
token = auth["access_token"]
name = auth["name"]
print(f"Auth OK - user: {name}")

dishes = get(f"{BASE}/cooking/dishes")
print(f"Dishes in DB: {len(dishes)} e.g. {dishes[0]['dish_name']}")

devices = get(f"{BASE}/devices/", token)
print(f"Devices: {[d['id'] for d in devices]}")

recs = get(f"{BASE}/recommendations/", token)
print(f"Recommendations: {len(recs)}")

notifs = get(f"{BASE}/notifications/", token)
print(f"Notifications: {len(notifs)}")

print("\nAll live data verified!")
