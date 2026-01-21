import pytest
from tests._helpers import find_path

def _assert_shape(j: dict):
    assert "total_minutes" in j
    assert "date_from" in j
    assert "date_to" in j
    assert "days" in j and isinstance(j["days"], list)
    assert "employees" in j and isinstance(j["employees"], list)
    assert "sites" in j and isinstance(j["sites"], list)
    assert "vehicles" in j and isinstance(j["vehicles"], list)

def test_report_range_shape(client, openapi):
    path = find_path(openapi, ["timekeeping", "reports", "range"], method="get")
    if not path:
        pytest.skip("Brak endpointu /timekeeping/reports/range w OpenAPI.")
    r = client.get(path, params={"date_from": "2026-01-01", "date_to": "2026-01-31"})
    assert r.status_code == 200, r.text
    _assert_shape(r.json())

def test_report_weekly_shape(client, openapi):
    path = find_path(openapi, ["timekeeping", "reports", "weekly"], method="get")
    if not path:
        pytest.skip("Brak endpointu /timekeeping/reports/weekly w OpenAPI.")
    r = client.get(path, params={"week_start": "2026-01-19"})
    assert r.status_code == 200, r.text
    _assert_shape(r.json())

def test_report_monthly_shape(client, openapi):
    path = find_path(openapi, ["timekeeping", "reports", "monthly"], method="get")
    if not path:
        pytest.skip("Brak endpointu /timekeeping/reports/monthly w OpenAPI.")
    r = client.get(path, params={"year": 2026, "month": 1})
    assert r.status_code == 200, r.text
    _assert_shape(r.json())
