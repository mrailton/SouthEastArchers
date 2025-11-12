"""
Tests for the core app.
"""
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from news.models import News
from events.models import Event

User = get_user_model()


# ============================================================================
# VIEW TESTS - PUBLIC PAGES
# ============================================================================

@pytest.mark.views
@pytest.mark.django_db
class TestIndexView:
    """Test the homepage view."""

    def test_index_page_loads(self, client):
        """Test homepage loads successfully."""
        response = client.get(reverse('core:index'))
        assert response.status_code == 200

    def test_index_shows_latest_news(self, client, user):
        """Test homepage displays latest 3 news articles."""
        # Create 5 news articles
        for i in range(5):
            News.objects.create(
                title=f'News {i}',
                content=f'Content {i}',
                author=user,
                published=True
            )

        response = client.get(reverse('core:index'))
        news_list = response.context['news']

        # Should only show 3 latest
        assert len(news_list) == 3

    def test_index_shows_only_published_news(self, client, user):
        """Test homepage only shows published news articles."""
        # Create published news
        published = News.objects.create(
            title='Published News',
            content='Published content',
            author=user,
            published=True
        )

        # Create unpublished news
        News.objects.create(
            title='Draft News',
            content='Draft content',
            author=user,
            published=False
        )

        response = client.get(reverse('core:index'))
        news_list = response.context['news']

        assert len(news_list) == 1
        assert news_list[0] == published

    def test_index_shows_upcoming_events(self, client, user):
        """Test homepage displays upcoming 3 events."""
        # Create 5 future events
        for i in range(5):
            Event.objects.create(
                title=f'Event {i}',
                description=f'Description {i}',
                event_date=timezone.now() + timedelta(days=i+1),
                location='Location',
                published=True,
                created_by=user
            )

        response = client.get(reverse('core:index'))
        events_list = response.context['events']

        # Should only show 3 upcoming
        assert len(events_list) == 3

    def test_index_shows_only_published_events(self, client, user):
        """Test homepage only shows published events."""
        # Create published event
        published = Event.objects.create(
            title='Published Event',
            description='Published description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=True,
            created_by=user
        )

        # Create unpublished event
        Event.objects.create(
            title='Draft Event',
            description='Draft description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=False,
            created_by=user
        )

        response = client.get(reverse('core:index'))
        events_list = response.context['events']

        assert len(events_list) == 1
        assert events_list[0] == published

    def test_index_no_news_or_events(self, client):
        """Test homepage loads even with no news or events."""
        response = client.get(reverse('core:index'))
        assert response.status_code == 200
        assert len(response.context['news']) == 0
        assert len(response.context['events']) == 0


@pytest.mark.views
@pytest.mark.django_db
class TestAboutView:
    """Test the about page view."""

    def test_about_page_loads(self, client):
        """Test about page loads successfully."""
        response = client.get(reverse('core:about'))
        assert response.status_code == 200

    def test_about_page_accessible_to_anonymous(self, client):
        """Test about page accessible without login."""
        response = client.get(reverse('core:about'))
        assert response.status_code == 200


@pytest.mark.views
@pytest.mark.django_db
class TestNewsListView:
    """Test the news list view."""

    def test_news_list_loads(self, client):
        """Test news list page loads successfully."""
        response = client.get(reverse('core:news_list'))
        assert response.status_code == 200

    def test_news_list_shows_all_published(self, client, user):
        """Test news list shows all published articles."""
        # Create published news articles
        for i in range(10):
            News.objects.create(
                title=f'News {i}',
                content=f'Content {i}',
                author=user,
                published=True
            )

        # Create unpublished
        News.objects.create(
            title='Unpublished',
            content='Content',
            author=user,
            published=False
        )

        response = client.get(reverse('core:news_list'))
        news_list = response.context['news']

        assert len(news_list) == 10  # Only published

    def test_news_list_ordering(self, client, user):
        """Test news list is ordered by date descending."""
        old = News.objects.create(
            title='Old News',
            content='Old content',
            author=user,
            published=True
        )
        old.created_at = timezone.now() - timedelta(days=10)
        old.save()

        new = News.objects.create(
            title='New News',
            content='New content',
            author=user,
            published=True
        )

        response = client.get(reverse('core:news_list'))
        news_list = response.context['news']

        assert news_list[0] == new
        assert news_list[1] == old


@pytest.mark.views
@pytest.mark.django_db
class TestNewsDetailView:
    """Test the news detail view."""

    def test_news_detail_loads(self, client, news_article):
        """Test news detail page loads for published article."""
        response = client.get(reverse('core:news_detail', args=[news_article.pk]))
        assert response.status_code == 200
        assert response.context['news'] == news_article

    def test_news_detail_shows_content(self, client, news_article):
        """Test news detail page displays article content."""
        response = client.get(reverse('core:news_detail', args=[news_article.pk]))
        content = response.content.decode()
        assert news_article.title in content
        assert news_article.content in content

    def test_unpublished_news_returns_404(self, client, unpublished_news):
        """Test unpublished news article returns 404."""
        response = client.get(reverse('core:news_detail', args=[unpublished_news.pk]))
        assert response.status_code == 404

    def test_nonexistent_news_returns_404(self, client):
        """Test nonexistent news article returns 404."""
        response = client.get(reverse('core:news_detail', args=[99999]))
        assert response.status_code == 404


@pytest.mark.views
@pytest.mark.django_db
class TestEventsListView:
    """Test the events list view."""

    def test_events_list_loads(self, client):
        """Test events list page loads successfully."""
        response = client.get(reverse('core:events_list'))
        assert response.status_code == 200

    def test_events_list_shows_upcoming_only(self, client, user):
        """Test events list shows only upcoming published events."""
        # Create future events
        future1 = Event.objects.create(
            title='Future Event 1',
            description='Description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=True,
            created_by=user
        )

        future2 = Event.objects.create(
            title='Future Event 2',
            description='Description',
            event_date=timezone.now() + timedelta(days=14),
            location='Location',
            published=True,
            created_by=user
        )

        # Create past event
        Event.objects.create(
            title='Past Event',
            description='Description',
            event_date=timezone.now() - timedelta(days=7),
            location='Location',
            published=True,
            created_by=user
        )

        response = client.get(reverse('core:events_list'))
        events_list = response.context['events']

        # Should only show future events
        assert len(events_list) == 2
        assert future1 in events_list
        assert future2 in events_list

    def test_events_list_hides_unpublished(self, client, user):
        """Test events list hides unpublished events."""
        # Create published event
        Event.objects.create(
            title='Published Event',
            description='Description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=True,
            created_by=user
        )

        # Create unpublished event
        Event.objects.create(
            title='Unpublished Event',
            description='Description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=False,
            created_by=user
        )

        response = client.get(reverse('core:events_list'))
        events_list = response.context['events']

        assert len(events_list) == 1


@pytest.mark.views
@pytest.mark.django_db
class TestEventDetailView:
    """Test the event detail view."""

    def test_event_detail_loads(self, client, event):
        """Test event detail page loads for published event."""
        response = client.get(reverse('core:event_detail', args=[event.pk]))
        assert response.status_code == 200
        assert response.context['event'] == event

    def test_event_detail_shows_content(self, client, event):
        """Test event detail page displays event content."""
        response = client.get(reverse('core:event_detail', args=[event.pk]))
        content = response.content.decode()
        assert event.title in content
        assert event.description in content
        assert event.location in content

    def test_unpublished_event_accessible(self, client, user):
        """Test unpublished event returns 404."""
        unpublished = Event.objects.create(
            title='Unpublished Event',
            description='Description',
            event_date=timezone.now() + timedelta(days=7),
            location='Location',
            published=False,
            created_by=user
        )
        response = client.get(reverse('core:event_detail', args=[unpublished.pk]))
        assert response.status_code == 404

    def test_nonexistent_event_returns_404(self, client):
        """Test nonexistent event returns 404."""
        response = client.get(reverse('core:event_detail', args=[99999]))
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.django_db
class TestPublicSiteIntegration:
    """Integration tests for public site navigation."""

    def test_complete_public_site_navigation(self, client, user):
        """Test navigating through public pages."""
        # Visit homepage
        response = client.get(reverse('core:index'))
        assert response.status_code == 200

        # Create news and event
        news = News.objects.create(
            title='Test News',
            content='Test content',
            author=user,
            published=True
        )

        event = Event.objects.create(
            title='Test Event',
            description='Test description',
            event_date=timezone.now() + timedelta(days=7),
            location='Test Location',
            published=True,
            created_by=user
        )

        # Visit news list
        response = client.get(reverse('core:news_list'))
        assert response.status_code == 200

        # Visit news detail
        response = client.get(reverse('core:news_detail', args=[news.pk]))
        assert response.status_code == 200

        # Visit events list
        response = client.get(reverse('core:events_list'))
        assert response.status_code == 200

        # Visit event detail
        response = client.get(reverse('core:event_detail', args=[event.pk]))
        assert response.status_code == 200

        # Visit about
        response = client.get(reverse('core:about'))
        assert response.status_code == 200

    def test_login_to_dashboard_flow(self, client, user, user_data, membership):
        """Test complete flow from login to dashboard."""
        # Try to access dashboard (should redirect)
        response = client.get(reverse('memberships:dashboard'))
        assert response.status_code == 302

        # Login
        response = client.post(reverse('accounts:login'), {
            'email': user_data['email'],
            'password': user_data['password']
        })
        assert response.status_code == 302

        # Access dashboard (should work now)
        response = client.get(reverse('memberships:dashboard'))
        assert response.status_code == 200
        assert response.context['membership'] == membership
