def find_path(openapi: dict, must_contain: list[str], method: str | None = None, no_params: bool = False) -> str | None:
    paths = openapi.get("paths", {})
    for p, ops in paths.items():
        if no_params and "{" in p:
            continue
        s = p.lower()
        if all(x.lower() in s for x in must_contain):
            if method is None:
                return p
            if method.lower() in ops:
                return p
    return None

def resolve_schema(openapi: dict, schema: dict) -> dict:
    if not schema:
        return {}
    if "$ref" in schema:
        ref = schema["$ref"]
        name = ref.split("/")[-1]
        return openapi.get("components", {}).get("schemas", {}).get(name, {})
    return schema

def required_props_for_request(openapi: dict, path: str, method: str) -> list[str]:
    op = openapi["paths"][path].get(method.lower(), {})
    rb = op.get("requestBody", {}) or {}
    content = rb.get("content", {}) or {}
    app_json = content.get("application/json", {}) or {}
    schema = resolve_schema(openapi, app_json.get("schema", {}) or {})
    return list(schema.get("required", []) or [])

def make_min_payload(required: list[str]) -> dict:
    payload = {}
    for k in required:
        lk = k.lower()

        if lk.endswith("_id"):
            payload[k] = 1
            continue

        if lk in ("work_date", "date"):
            payload[k] = "2026-01-21"
            continue

        if lk.endswith("_date") or lk.endswith("date"):
            payload[k] = "2026-01-21"
            continue

        if lk.endswith("_at") or "datetime" in lk or "timestamp" in lk:
            payload[k] = "2026-01-21T08:00:00Z"
            continue

        payload[k] = "test"

    return payload
