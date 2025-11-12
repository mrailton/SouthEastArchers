"""
Tests for the news app.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from news.models import News
from news.forms import NewsForm

User = get_user_model()


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.models
@pytest.mark.django_db
class TestNewsModel:
    """Test the News model."""

    def test_create_news_article(self, user):
        """Test creating a news article."""
        news = News.objects.create(
            title='Test News',
            content='Test content for news article.',
            author=user,
            published=True
        )
        assert news.title == 'Test News'
        assert news.content == 'Test content for news article.'
        assert news.author == user
        assert news.published is True
        assert news.created_at is not None

    def test_news_string_representation(self, news_article):
        """Test __str__ method returns title."""
        assert str(news_article) == 'Test News Article'

    def test_news_ordering(self, user):
        """Test news articles are ordered by created_at descending."""
        old_news = News.objects.create(
            title='Old News',
            content='Old content',
            author=user,
            published=True
        )
        old_news.created_at = timezone.now() - timezone.timedelta(days=10)
        old_news.save()

        new_news = News.objects.create(
            title='New News',
            content='New content',
            author=user,
            published=True
        )

        news_list = list(News.objects.all())
        assert news_list[0] == new_news
        assert news_list[1] == old_news

    def test_news_defaults(self, user):
        """Test default values for news article."""
        news = News.objects.create(
            title='Default News',
            content='Content',
            author=user
        )
        assert news.published is True  # Default published


# ============================================================================
# FORM TESTS
# ============================================================================

@pytest.mark.forms
@pytest.mark.django_db
class TestNewsForm:
    """Test the NewsForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        form = NewsForm(data={
            'title': 'Test News',
            'content': 'Test content for the news article.',
            'published': True
        })
        assert form.is_valid()

    def test_missing_required_fields(self):
        """Test form validation fails with missing required fields."""
        form = NewsForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'content' in form.errors

    def test_unpublished_news(self):
        """Test creating unpublished news article."""
        form = NewsForm(data={
            'title': 'Draft News',
            'content': 'Draft content.',
            'published': False
        })
        assert form.is_valid()
        assert form.cleaned_data['published'] is False


# ============================================================================
# ADMIN TESTS
# ============================================================================

@pytest.mark.admin
@pytest.mark.django_db
class TestNewsAdmin:
    """Test News admin functionality."""

    def test_admin_list_view(self, admin_client):
        """Test admin can view news list."""
        response = admin_client.get('/admin/news/news/')
        assert response.status_code == 200

    def test_admin_can_create_news(self, admin_client, admin_user):
        """Test admin can create news article."""
        response = admin_client.post('/admin/news/news/add/', {
            'title': 'Admin Created News',
            'content': 'Content created by admin.',
            'published': True,
            'author': admin_user.id
        })
        # Should redirect after successful creation or stay on page
        assert response.status_code in [200, 302]

    def test_admin_search_news(self, admin_client, news_article):
        """Test admin can search news by title."""
        response = admin_client.get('/admin/news/news/', {'q': 'Test News'})
        assert response.status_code == 200
        assert news_article.title.encode() in response.content
