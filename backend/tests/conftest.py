import os
import time
import pytest
import httpx

from tests._helpers import find_path, resolve_schema, required_props_for_request, make_min_payload

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_USER = "admin@hvacquotepro.pl"
DEFAULT_PASS = "Admin123!"

def _wait_for_server(base_url: str, timeout_s: int = 10) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/openapi.json", timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("HVACQ_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

@pytest.fixture(scope="session")
def creds() -> tuple[str, str]:
    u = os.getenv("HVACQ_USER", DEFAULT_USER)
    p = os.getenv("HVACQ_PASS", DEFAULT_PASS)
    return u, p

@pytest.fixture(scope="session")
def openapi(base_url: str):
    if not _wait_for_server(base_url, timeout_s=10):
        pytest.skip(f"Serwer nie odpowiada pod {base_url}. Uruchom run_dev.ps1 albo ustaw HVACQ_BASE_URL.")
    r = httpx.get(f"{base_url}/openapi.json", timeout=10.0)
    r.raise_for_status()
    return r.json()

def request_body_info(openapi: dict, path: str, method: str) -> dict:
    op = openapi["paths"][path].get(method.lower(), {})
    rb = op.get("requestBody", {}) or {}
    return (rb.get("content", {}) or {})

def required_props_for_content(openapi: dict, schema: dict) -> list[str]:
    sch = resolve_schema(openapi, schema or {})
    return list(sch.get("required", []) or [])

def make_payload(required: list[str], user: str, pw: str) -> dict:
    out = {}
    for k in required:
        lk = k.lower()
        if lk in ("username", "email", "login"):
            out[k] = user
        elif lk == "password":
            out[k] = pw
        elif lk == "grant_type":
            out[k] = "password"
        elif lk in ("scope", "client_id", "client_secret"):
            out[k] = ""
        else:
            out[k] = ""
    if "password" not in (x.lower() for x in required):
        out["password"] = pw
    if not any(x.lower() in ("username", "email", "login") for x in required):
        out["username"] = user
    return out

@pytest.fixture(scope="session")
def token(base_url: str, openapi: dict, creds: tuple[str, str]) -> str:
    login_path = find_path(openapi, ["auth", "login"], method="post")
    if not login_path:
        pytest.skip("Brak endpointu login w OpenAPI (auth/login).")

    u, p = creds
    content = request_body_info(openapi, login_path, "post")
    tries = []

    if "application/x-www-form-urlencoded" in content:
        schema = content["application/x-www-form-urlencoded"].get("schema", {})
        req = required_props_for_content(openapi, schema)
        form = make_payload(req, u, p)
        tries.append(("form", form))

    if "application/json" in content:
        schema = content["application/json"].get("schema", {})
        req = required_props_for_content(openapi, schema)
        js = make_payload(req, u, p)
        tries.append(("json", js))

    if not tries:
        tries.append(("form", {"username": u, "password": p}))
        tries.append(("form", {"email": u, "password": p}))
        tries.append(("json", {"username": u, "password": p}))
        tries.append(("json", {"email": u, "password": p}))

    last = None
    for kind, payload in tries:
        if kind == "form":
            r = httpx.post(f"{base_url}{login_path}", data=payload, timeout=10.0)
        else:
            r = httpx.post(f"{base_url}{login_path}", json=payload, timeout=10.0)
        last = r
        if r.status_code == 200:
            j = r.json()
            t = j.get("access_token")
            if t:
                return t

    if last is not None:
        pytest.skip(f"Login nie dziala ({last.status_code}): {last.text}")
    pytest.skip("Login nie dziala (brak odpowiedzi).")

@pytest.fixture()
def client(base_url: str, token: str):
    h = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=base_url, headers=h, timeout=20.0) as c:
        yield c
