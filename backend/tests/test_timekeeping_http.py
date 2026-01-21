import re
import pytest
from tests._helpers import find_path, required_props_for_request, make_min_payload

def _ensure_entity(client, openapi, words):
    list_path = find_path(openapi, words, method="get", no_params=True)
    if not list_path:
        return None

    r = client.get(list_path)
    if r.status_code != 200:
        return None
    items = r.json()
    if isinstance(items, list) and len(items) > 0:
        return items[0]

    create_path = find_path(openapi, words, method="post", no_params=True)
    if not create_path:
        return None

    req = required_props_for_request(openapi, create_path, "post")
    payload = make_min_payload(req)

    r2 = client.post(create_path, json=payload)
    if r2.status_code not in (200, 201):
        return None
    return r2.json()

def _extract_id_from_conflict(text: str) -> int | None:
    m = re.search(r"\bid\s*=\s*(\d+)\b", text)
    if m:
        return int(m.group(1))
    return None

def test_timekeeping_close_does_not_500(client, openapi):
    crew_logs_list_path = find_path(openapi, ["timekeeping", "crew-logs"], method="get", no_params=True)
    crew_logs_create_path = find_path(openapi, ["timekeeping", "crew-logs"], method="post", no_params=True)

    if not crew_logs_list_path or not crew_logs_create_path:
        pytest.skip("Brak crew-logs GET/POST w OpenAPI.")

    site = _ensure_entity(client, openapi, ["timekeeping", "sites"])
    vehicle = _ensure_entity(client, openapi, ["timekeeping", "vehicles"])
    employee = _ensure_entity(client, openapi, ["timekeeping", "employees"])

    if not vehicle or not employee:
        pytest.skip("Brak vehicle/employee i nie da sie ich pobrac/utworzyc przez API.")

    req = required_props_for_request(openapi, crew_logs_create_path, "post")
    payload = make_min_payload(req)

    vehicle_id = vehicle.get("id", 1)
    employee_id = employee.get("id", 1)

    for k in list(payload.keys()):
        if k.lower() == "vehicle_id":
            payload[k] = vehicle_id
        if k.lower() in ("created_by_employee_id", "employee_id"):
            payload[k] = employee_id

    r = client.post(crew_logs_create_path, json=payload)

    log_id = None

    if r.status_code in (200, 201):
        j = r.json()
        log_id = j.get("id")
    elif r.status_code == 409:
        log_id = _extract_id_from_conflict(r.text)
        if not log_id:
            rlist = client.get(crew_logs_list_path)
            if rlist.status_code == 200 and isinstance(rlist.json(), list):
                logs = rlist.json()
                wanted_date = payload.get("work_date")
                for item in logs:
                    if item.get("vehicle_id") == vehicle_id and str(item.get("work_date")) == str(wanted_date):
                        log_id = item.get("id")
                        break
    else:
        pytest.skip(f"Nie udalo sie utworzyc crew log ({r.status_code}): {r.text}")

    if not log_id:
        pytest.skip("Nie udalo sie ustalic id crew log.")

    add_seg_path = find_path(openapi, ["timekeeping", "crew-logs", "segments"], method="post")
    close_path = find_path(openapi, ["timekeeping", "crew-logs", "segments", "close"], method="patch")

    if not add_seg_path or not close_path:
        pytest.skip("Brak endpointow segments POST lub segments close PATCH w OpenAPI.")

    add_seg_url = add_seg_path.replace("{logId}", str(log_id)).replace("{log_id}", str(log_id)).replace("{crew_log_id}", str(log_id))

    req2 = required_props_for_request(openapi, add_seg_path, "post")
    seg_payload = make_min_payload(req2)

    if site:
        for k in list(seg_payload.keys()):
            if k.lower() == "site_id":
                seg_payload[k] = site.get("id", seg_payload[k])

    r2 = client.post(add_seg_url, json=seg_payload)
    if r2.status_code not in (200, 201):
        pytest.skip(f"Nie udalo sie dodac segmentu ({r2.status_code}): {r2.text}")

    seg = r2.json()
    seg_id = seg.get("id")
    if not seg_id:
        pytest.skip("Brak id segmentu w odpowiedzi.")

    close_url = (
        close_path
        .replace("{logId}", str(log_id)).replace("{log_id}", str(log_id)).replace("{crew_log_id}", str(log_id))
        .replace("{segmentId}", str(seg_id)).replace("{segment_id}", str(seg_id))
    )

    r3 = client.patch(close_url, json={})
    assert r3.status_code != 500, f"HTTP 500 na close: {r3.text}"
