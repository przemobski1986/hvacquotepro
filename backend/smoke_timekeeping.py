import json
import urllib.request
from datetime import date

import os; BASE = os.getenv("SMOKE_BASE", "http://127.0.0.1:8000")
EMAIL = "admin@hvacquotepro.pl"
PASSWORD = "Admin123!"
SITE_ID = 1
VEHICLE_ID = 3
CREATED_BY_EMPLOYEE_ID = 3

def request(method, path, body=None, token=None):
    url = BASE + path
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8")
        raise SystemExit(f"HTTP {e.code} {method} {path}\n{payload}")
    except Exception as e:
        raise SystemExit(f"CONNECT ERROR {method} {path}\n{e!r}")

_, login = request("POST", "/api/v1/auth/login", {"email": EMAIL, "password": PASSWORD})
token = login["access_token"]

work_date = date.today().isoformat()

_, logs = request("GET", "/api/v1/timekeeping/crew-logs", token=token)

log_id = None
for l in logs:
    if l.get("work_date") == work_date and l.get("vehicle_id") == VEHICLE_ID and l.get("created_by_employee_id") == CREATED_BY_EMPLOYEE_ID:
        log_id = l.get("id")
        break

if log_id is None:
    _, created = request(
        "POST",
        "/api/v1/timekeeping/crew-logs",
        {"work_date": work_date, "vehicle_id": VEHICLE_ID, "created_by_employee_id": CREATED_BY_EMPLOYEE_ID},
        token=token,
    )
    log_id = created["id"]

_, seg = request("POST", f"/api/v1/timekeeping/crew-logs/{log_id}/segments/start", {"site_id": SITE_ID}, token=token)
seg_id = seg["id"]

_, closed = request("PATCH", f"/api/v1/timekeeping/crew-logs/{log_id}/segments/{seg_id}/close", {}, token=token)

if closed.get("end_at") is None:
    raise SystemExit("FAIL: end_at is null after close {}")

print("OK")
print("crew_log_id:", log_id)
print("segment_id:", seg_id)
print("work_date:", work_date)
print("start_at:", seg.get("start_at"))
print("end_at:", closed.get("end_at"))




