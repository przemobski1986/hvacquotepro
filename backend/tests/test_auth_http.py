def test_openapi_available(openapi):
    assert "paths" in openapi and len(openapi["paths"]) > 0

def test_login_token_present(token):
    assert isinstance(token, str) and len(token) > 20
