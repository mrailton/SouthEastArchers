"""Tests for admin news management"""

from app.models import News


def test_news_list(client, admin_user):
    """Test viewing news list"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/news")
    assert response.status_code == 200


def test_create_news_page(client, admin_user):
    """Test accessing create news page"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/news/create")
    assert response.status_code == 200


def test_edit_news_page(client, admin_user, app):
    """Test accessing edit news page"""
    from app import db

    news = News(title="Test News", content="Test content here", published=False)
    db.session.add(news)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get(f"/admin/news/{news.id}/edit")
    assert response.status_code == 200
    assert b"Edit News" in response.data
    assert b"Test News" in response.data


def test_edit_news_success(client, admin_user, app):
    """Test updating news article"""
    from app import db

    news = News(title="Original Title", content="Original content", published=False)
    db.session.add(news)
    db.session.commit()
    news_id = news.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/news/{news_id}/edit",
        data={
            "title": "Updated Title",
            "summary": "Updated summary",
            "content": "Updated content here with more text",
            "published": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify changes
    updated_news = db.session.get(News, news_id)
    assert updated_news.title == "Updated Title"
    assert updated_news.published is True
    assert updated_news.published_at is not None


def test_edit_news_not_found(client, admin_user):
    """Test editing non-existent news"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/news/99999/edit")
    assert response.status_code == 404


def test_news_requires_admin(client, test_user):
    """Test that news requires admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/news")
    assert response.status_code in [302, 403]


def test_create_news_success_published(client, admin_user, app):
    """Test successfully creating a published news article"""

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/news/create",
        data={
            "title": "New Article",
            "summary": "Article summary",
            "content": "Article content here",
            "published": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify news was created
    news = News.query.filter_by(title="New Article").first()
    assert news is not None
    assert news.published is True
    assert news.published_at is not None


def test_create_news_success_unpublished(client, admin_user, app):
    """Test successfully creating an unpublished news article"""

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/news/create",
        data={
            "title": "Unpublished Article",
            "summary": "Article summary",
            "content": "Article content here",
            # Not setting published checkbox
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify news was created as unpublished
    news = News.query.filter_by(title="Unpublished Article").first()
    assert news is not None
    assert news.published is False
    assert news.published_at is None


def test_edit_news_publish(client, admin_user, app):
    """Test editing news to publish it sets published_at"""
    from app import db

    news = News(title="Draft Article", content="Draft content that is long enough to pass validation", published=False)
    db.session.add(news)
    db.session.commit()
    news_id = news.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/news/{news_id}/edit",
        data={
            "title": "Published Article",
            "summary": "Now published",
            "content": "Published content that is long enough to pass validation",
            "published": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify published_at was set
    updated_news = db.session.get(News, news_id)
    assert updated_news.published is True
    assert updated_news.published_at is not None


def test_edit_news_already_published_keeps_date(client, admin_user, app):
    """Test editing already published news keeps original published_at"""
    from app import db
    from app.utils.datetime_utils import utc_now

    original_published_at = utc_now()
    news = News(
        title="Already Published",
        content="Already published content",
        published=True,
        published_at=original_published_at,
    )
    db.session.add(news)
    db.session.commit()
    news_id = news.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/news/{news_id}/edit",
        data={
            "title": "Updated Published Article",
            "summary": "Updated summary",
            "content": "Updated content",
            "published": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify published_at was not changed (check timestamp is close, within 1 second)
    updated_news = db.session.get(News, news_id)
    # Remove timezone info for comparison if needed
    orig_time = (
        original_published_at.replace(tzinfo=None) if hasattr(original_published_at, "tzinfo") and original_published_at.tzinfo else original_published_at
    )
    updated_time = (
        updated_news.published_at.replace(tzinfo=None)
        if hasattr(updated_news.published_at, "tzinfo") and updated_news.published_at.tzinfo
        else updated_news.published_at
    )
    assert abs((orig_time - updated_time).total_seconds()) < 1


def test_edit_news_unpublish(client, admin_user, app):
    """Test unpublishing a news article"""
    from app import db
    from app.utils.datetime_utils import utc_now

    news = News(
        title="To Be Unpublished",
        content="Content here that is long enough to pass validation",
        published=True,
        published_at=utc_now(),
    )
    db.session.add(news)
    db.session.commit()
    news_id = news.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/news/{news_id}/edit",
        data={
            "title": "Unpublished Article",
            "summary": "No longer published",
            "content": "Unpublished content that is long enough to pass validation",
            # Not setting published checkbox
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify news was unpublished but published_at still exists
    updated_news = db.session.get(News, news_id)
    assert updated_news.published is False


def test_create_news_requires_admin(client, test_user):
    """Test creating news requires admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/news/create")
    assert response.status_code in [302, 403]


def test_edit_news_requires_admin(client, test_user, app):
    """Test editing news requires admin"""
    from app import db

    news = News(title="Test News", content="Test content", published=False)
    db.session.add(news)
    db.session.commit()

    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get(f"/admin/news/{news.id}/edit")
    assert response.status_code in [302, 403]
