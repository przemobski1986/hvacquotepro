import pytest
from tests._helpers import find_path

def test_daily_report_returns_shape(client, openapi):
    path = find_path(openapi, ["timekeeping", "reports", "daily"], method="get")
    if not path:
        pytest.skip("Brak endpointu /timekeeping/reports/daily w OpenAPI.")

    r = client.get(path, params={"work_date": "2026-01-21"})
    assert r.status_code == 200, r.text

    j = r.json()
    assert "work_date" in j
    assert "total_minutes" in j
    assert "employees" in j and isinstance(j["employees"], list)
    assert "sites" in j and isinstance(j["sites"], list)
    assert "crew_logs" in j and isinstance(j["crew_logs"], list)
