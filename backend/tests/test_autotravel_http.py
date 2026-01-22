import pytest
from tests._helpers import find_path

def test_autotravel_gap_creates_travel_segment(client, openapi):
    # paths
    create_vehicle = find_path(openapi, ["timekeeping", "vehicles"], method="post", no_params=True)
    create_site_adhoc = find_path(openapi, ["timekeeping", "sites", "ad-hoc"], method="post", no_params=True)
    create_crewlog = find_path(openapi, ["timekeeping", "crew-logs"], method="post", no_params=True)
    add_member = find_path(openapi, ["timekeeping", "crew-logs", "members"], method="post")
    add_segment = find_path(openapi, ["timekeeping", "crew-logs", "segments"], method="post")
    list_segments = find_path(openapi, ["timekeeping", "crew-logs", "segments"], method="get")

    if not all([create_vehicle, create_site_adhoc, create_crewlog, add_member, add_segment, list_segments]):
        pytest.skip("Brak wymaganych endpointow w OpenAPI.")

    # create vehicle
    r = client.post(create_vehicle, json={"plate": "AUTO-TRAVEL-TEST", "make_model": "pytest"})
    if r.status_code not in (200, 201):
        # plate unique; fallback with suffix
        import time
        r = client.post(create_vehicle, json={"plate": f"AUTO-TRAVEL-{int(time.time())}", "make_model": "pytest"})
    assert r.status_code in (200, 201), r.text
    vehicle_id = r.json()["id"]

    # create sites
    rA = client.post(create_site_adhoc, json={"name": "PY SITE A", "lat": 50.0, "lng": 19.0, "radius_m": 200})
    rB = client.post(create_site_adhoc, json={"name": "PY SITE B", "lat": 50.0001, "lng": 19.0001, "radius_m": 200})
    assert rA.status_code in (200, 201), rA.text
    assert rB.status_code in (200, 201), rB.text
    siteA = rA.json()["id"]
    siteB = rB.json()["id"]

    # employee (take first from list endpoint)
    list_employees = find_path(openapi, ["timekeeping", "employees"], method="get", no_params=True)
    if not list_employees:
        pytest.skip("Brak employees list w OpenAPI.")
    emps = client.get(list_employees).json()
    if not emps:
        rc = client.post(find_path(openapi, ["timekeeping", "employees"], method="post", no_params=True), json={"full_name": "PY EMP"})
        assert rc.status_code in (200, 201), rc.text
        emps = [rc.json()]
    employee_id = emps[0]["id"]

    # crew log for today
    import datetime
    work_date = datetime.date.today().isoformat()
    rlog = client.post(create_crewlog, json={"work_date": work_date, "vehicle_id": vehicle_id, "created_by_employee_id": employee_id})
    if rlog.status_code == 409:
        # if conflict, fetch existing for that date+vehicle
        logs = client.get(find_path(openapi, ["timekeeping", "crew-logs"], method="get", no_params=True), params={"work_date": work_date, "vehicle_id": vehicle_id}).json()
        assert logs, "Brak crew log po 409"
        log_id = logs[0]["id"]
    else:
        assert rlog.status_code in (200, 201), rlog.text
        log_id = rlog.json()["id"]

    # add member
    add_member_url = add_member.replace("{log_id}", str(log_id)).replace("{logId}", str(log_id))
    client.post(add_member_url, json={"employee_id": employee_id})

    # add segment A 08-09
    add_seg_url = add_segment.replace("{log_id}", str(log_id)).replace("{logId}", str(log_id))
    startA = datetime.datetime.combine(datetime.date.today(), datetime.time(8,0)).isoformat()
    endA   = datetime.datetime.combine(datetime.date.today(), datetime.time(9,0)).isoformat()
    rsegA = client.post(add_seg_url, json={"site_id": siteA, "segment_type": "work", "start_at": startA, "end_at": endA})
    assert rsegA.status_code in (200, 201), rsegA.text

    # add segment B 10-11 -> should create travel 09-10 on siteB
    startB = datetime.datetime.combine(datetime.date.today(), datetime.time(10,0)).isoformat()
    endB   = datetime.datetime.combine(datetime.date.today(), datetime.time(11,0)).isoformat()
    rsegB = client.post(add_seg_url, json={"site_id": siteB, "segment_type": "work", "start_at": startB, "end_at": endB})
    assert rsegB.status_code in (200, 201), rsegB.text

    # list segments and verify travel exists
    list_url = list_segments.replace("{log_id}", str(log_id)).replace("{logId}", str(log_id))
    segs = client.get(list_url).json()

    def norm(x): return str(x).replace("Z","")
    has_travel = any(
        s.get("site_id") == siteB and s.get("segment_type") == "travel" and norm(s.get("start_at"))[:16] == norm(endA)[:16] and norm(s.get("end_at"))[:16] == norm(startB)[:16]
        for s in segs
    )
    assert has_travel, segs
