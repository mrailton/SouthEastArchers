"""Admin news routes — permissions and CRUD redirects."""

from app import db
from app.models import News


def test_news_list(admin_client):
    response = admin_client.get("/admin/news")
    assert response.status_code == 200


def test_create_news_success_redirects(admin_client):
    response = admin_client.post(
        "/admin/news/create",
        data={
            "title": "New Article",
            "summary": "Article summary",
            "content": "Article content with enough characters.",
            "published": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert News.query.filter_by(title="New Article").first() is not None


def test_edit_news_not_found(admin_client):
    response = admin_client.get("/admin/news/99999/edit")
    assert response.status_code == 404


def test_news_requires_admin(member_client):
    response = member_client.get("/admin/news")
    assert response.status_code in (302, 403)
