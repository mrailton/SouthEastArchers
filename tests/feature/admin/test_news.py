"""Admin news routes — permissions and CRUD redirects."""

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


def test_create_news_page(admin_client):
    response = admin_client.get("/admin/news/create")
    assert response.status_code == 200


def test_edit_news_success(admin_client):
    admin_client.post(
        "/admin/news/create",
        data={
            "title": "Editable Article",
            "summary": "Summary",
            "content": "Article content with enough characters.",
        },
        follow_redirects=False,
    )
    article = News.query.filter_by(title="Editable Article").first()
    response = admin_client.get(f"/admin/news/{article.id}/edit")
    assert response.status_code == 200

    response = admin_client.post(
        f"/admin/news/{article.id}/edit",
        data={
            "title": "Updated Article",
            "summary": "New summary",
            "content": "Updated article content with enough characters.",
            "published": "on",
        },
        follow_redirects=True,
    )
    assert b"News article updated" in response.content
