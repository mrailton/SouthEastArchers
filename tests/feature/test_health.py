def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_failure(client, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr("sqlalchemy.orm.Session.execute", _boom)
    response = client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"status": "error"}
