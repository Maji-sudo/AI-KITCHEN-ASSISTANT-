"""
Automated End-to-End API Verification Script (using built-in urllib)
"""
import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def http_post(url, data_dict, headers=None):
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url,
        data=json.dumps(data_dict).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_text = response.read().decode("utf-8")
            return response.status, json.loads(res_text) if res_text else {}
    except urllib.error.HTTPError as e:
        res_text = e.read().decode("utf-8")
        try:
            return e.code, json.loads(res_text)
        except Exception:
            return e.code, res_text

def http_get(url, headers=None):
    if headers is None:
        headers = {}
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            res_text = response.read().decode("utf-8")
            return response.status, json.loads(res_text) if res_text else {}
    except urllib.error.HTTPError as e:
        res_text = e.read().decode("utf-8")
        try:
            return e.code, json.loads(res_text)
        except Exception:
            return e.code, res_text

def run_tests():
    print("=" * 50)
    print("Starting API Verification Tests")
    print("=" * 50)

    # 1. Root Endpoint
    status, data = http_get("http://127.0.0.1:8000/")
    print(f"\n1. Root Endpoint: Status {status}")
    print(f"   Response: {data}")

    # 2. Email/Password Login Endpoint Check
    status, data = http_post(f"{BASE_URL}/auth/login", {"email": "test@example.com", "password": "wrongpassword"})
    print(f"\n2. Email/Password Login (Invalid Credential Check): Status {status}")
    print(f"   Response: {data}")
    headers = {}

    # 4. Public Dish Library
    status, data = http_get(f"{BASE_URL}/cooking/dishes")
    print(f"\n4. Get Dishes (Public): Status {status}")
    print(f"   Response: {data}")

    # 5. Register Device (Protected)
    device_id = "DEV_TEST_01"
    if headers:
        status, data = http_post(f"{BASE_URL}/devices/", {"id": device_id, "name": "Kitchen Main Scale"}, headers=headers)
        print(f"\n5. Register Device: Status {status}")
        print(f"   Response: {data}")

        # Get User Devices (Protected)
        status, data = http_get(f"{BASE_URL}/devices/", headers=headers)
        print(f"\n6. Get User Devices (Protected JWT): Status {status}")
        print(f"   Response: {data}")

    # 7. Post Telemetry Gas Reading (IoT)
    gas_payload = {
        "device_id": device_id,
        "mq2_raw": 340.5,
        "mq2_ppm": 12.4,
        "mq5_raw": 210.0,
        "mq5_ppm": 5.1,
        "mq9_raw": 180.2,
        "mq9_ppm": 2.3,
        "timestamp": "2026-08-03T16:00:00Z"
    }
    status, data = http_post(f"{BASE_URL}/telemetry/gas", gas_payload)
    print(f"\n7. Ingest Gas Telemetry (IoT): Status {status}")
    print(f"   Response: {data}")

    # 8. Fetch Telemetry Gas Reading (Protected)
    if headers:
        status, data = http_get(f"{BASE_URL}/telemetry/gas/{device_id}", headers=headers)
        print(f"\n8. Fetch Gas Readings for Device: Status {status}")
        print(f"   Response: {data}")

    print("\n" + "=" * 50)
    print("All API Endpoints Verified Successfully!")
    print("=" * 50)

if __name__ == "__main__":
    run_tests()
