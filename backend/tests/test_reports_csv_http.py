import pytest
from tests._helpers import find_path

def _assert_csv_response(r):
    assert r.status_code == 200, r.text
    ct = (r.headers.get("content-type") or "").lower()
    assert "text/csv" in ct
    txt = r.text
    assert "minutes" in txt and "segments" in txt

def test_csv_range_employees(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "range", "employees.csv"], method="get")
    if not p:
        pytest.skip("Brak range employees.csv")
    r = client.get(p, params={"date_from": "2026-01-01", "date_to": "2026-01-31"})
    _assert_csv_response(r)

def test_csv_range_vehicles(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "range", "vehicles.csv"], method="get")
    if not p:
        pytest.skip("Brak range vehicles.csv")
    r = client.get(p, params={"date_from": "2026-01-01", "date_to": "2026-01-31"})
    _assert_csv_response(r)

def test_csv_range_sites(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "range", "sites.csv"], method="get")
    if not p:
        pytest.skip("Brak range sites.csv")
    r = client.get(p, params={"date_from": "2026-01-01", "date_to": "2026-01-31"})
    _assert_csv_response(r)

def test_csv_weekly_employees(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "weekly", "employees.csv"], method="get")
    if not p:
        pytest.skip("Brak weekly employees.csv")
    r = client.get(p, params={"week_start": "2026-01-19"})
    _assert_csv_response(r)

def test_csv_weekly_vehicles(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "weekly", "vehicles.csv"], method="get")
    if not p:
        pytest.skip("Brak weekly vehicles.csv")
    r = client.get(p, params={"week_start": "2026-01-19"})
    _assert_csv_response(r)

def test_csv_weekly_sites(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "weekly", "sites.csv"], method="get")
    if not p:
        pytest.skip("Brak weekly sites.csv")
    r = client.get(p, params={"week_start": "2026-01-19"})
    _assert_csv_response(r)

def test_csv_monthly_employees(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "monthly", "employees.csv"], method="get")
    if not p:
        pytest.skip("Brak monthly employees.csv")
    r = client.get(p, params={"year": 2026, "month": 1})
    _assert_csv_response(r)

def test_csv_monthly_vehicles(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "monthly", "vehicles.csv"], method="get")
    if not p:
        pytest.skip("Brak monthly vehicles.csv")
    r = client.get(p, params={"year": 2026, "month": 1})
    _assert_csv_response(r)

def test_csv_monthly_sites(client, openapi):
    p = find_path(openapi, ["timekeeping", "reports", "monthly", "sites.csv"], method="get")
    if not p:
        pytest.skip("Brak monthly sites.csv")
    r = client.get(p, params={"year": 2026, "month": 1})
    _assert_csv_response(r)
