# integration tets useing real routes through flasks test client
from app import app

def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_bad_page_returns_400():
    r = client().get("/api/crossings?page=0")
    assert r.status_code == 400
    assert "page" in r.get_json()["error"]

def test_unknown_status_returns_400():
    r = client().get("/api/crossings?status=flying")
    assert r.status_code == 400

def test_create_without_body_returns_400():
    r = client().post("/api/crossings", data="not json")
    assert r.status_code == 400

def test_unknown_api_path_returns_json_404():
    r = client().get("/api/nothing-here")
    assert r.status_code == 404
    assert r.get_json()["error"]

# test with mysql   
def test_missing_crossing_returns_404():
    r = client().get("/api/crossings/999999")
    assert r.status_code == 404
