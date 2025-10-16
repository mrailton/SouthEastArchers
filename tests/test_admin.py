from datetime import datetime, timedelta

from app import db
from app.models import News, Event, ShootingNight, User
from tests.conftest import login


class TestAdmin:
    def test_admin_dashboard_requires_admin(self, client, regular_user):
        """Test non-admin cannot access admin dashboard."""
        login(client, 'user@test.com', 'user123')
        response = client.get('/admin/dashboard', follow_redirects=True)
        # Should redirect or show error
        assert response.status_code in [200, 302]

    def test_admin_can_access_dashboard(self, client, admin_user):
        """Test admin can access dashboard."""
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/dashboard')
        assert response.status_code == 200

class TestAdminNews:
    def test_news_list(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/news')
        assert response.status_code == 200
    
    def test_news_create_get(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/news/create')
        assert response.status_code == 200
    
    def test_news_create_post(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.post('/admin/news/create', data={
            'title': 'Test News',
            'content': 'This is test news content.',
            'published': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        news = News.query.filter_by(title='Test News').first()
        assert news is not None
        assert news.content == 'This is test news content.'
        assert news.published is True
    
    def test_news_edit_get(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create news first
        news = News(
            title='Original Title',
            content='Original content',
            author_id=admin_user.id,
            published=True
        )
        db.session.add(news)
        db.session.commit()
        
        response = client.get(f'/admin/news/{news.id}/edit')
        assert response.status_code == 200
    
    def test_news_edit_post(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create news first
        news = News(
            title='Original Title',
            content='Original content',
            author_id=admin_user.id,
            published=False
        )
        db.session.add(news)
        db.session.commit()
        news_id = news.id
        
        response = client.post(f'/admin/news/{news_id}/edit', data={
            'title': 'Updated Title',
            'content': 'Updated content',
            'published': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated_news = db.session.get(News, news_id)
        assert updated_news.title == 'Updated Title'
        assert updated_news.content == 'Updated content'
        assert updated_news.published is True
    
    def test_news_delete(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create news first
        news = News(
            title='To Delete',
            content='This will be deleted',
            author_id=admin_user.id,
            published=True
        )
        db.session.add(news)
        db.session.commit()
        news_id = news.id
        
        response = client.post(f'/admin/news/{news_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        deleted_news = db.session.get(News, news_id)
        assert deleted_news is None


class TestAdminEvents:
    def test_event_list(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/events')
        assert response.status_code == 200
    
    def test_event_create_get(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/events/create')
        assert response.status_code == 200
    
    def test_event_create_post(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        event_date = datetime.utcnow() + timedelta(days=30)
        
        response = client.post('/admin/events/create', data={
            'title': 'Test Event',
            'description': 'This is a test event.',
            'event_date': event_date.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Test Location',
            'published': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        event = Event.query.filter_by(title='Test Event').first()
        assert event is not None
        assert event.description == 'This is a test event.'
        assert event.location == 'Test Location'
    
    def test_event_edit_get(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create event first
        event = Event(
            title='Original Event',
            description='Original description',
            event_date=datetime.utcnow() + timedelta(days=7),
            created_by=admin_user.id,
            published=True
        )
        db.session.add(event)
        db.session.commit()
        
        response = client.get(f'/admin/events/{event.id}/edit')
        assert response.status_code == 200
    
    def test_event_edit_post(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create event first
        event = Event(
            title='Original Event',
            description='Original description',
            event_date=datetime.utcnow() + timedelta(days=7),
            created_by=admin_user.id,
            published=False
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id
        
        new_date = datetime.utcnow() + timedelta(days=14)
        response = client.post(f'/admin/events/{event_id}/edit', data={
            'title': 'Updated Event',
            'description': 'Updated description',
            'event_date': new_date.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Updated Location',
            'published': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated_event = db.session.get(Event, event_id)
        assert updated_event.title == 'Updated Event'
        assert updated_event.description == 'Updated description'
        assert updated_event.published is True
    
    def test_event_delete(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create event first
        event = Event(
            title='To Delete',
            description='This will be deleted',
            event_date=datetime.utcnow() + timedelta(days=7),
            created_by=admin_user.id,
            published=True
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id
        
        response = client.post(f'/admin/events/{event_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        deleted_event = db.session.get(Event, event_id)
        assert deleted_event is None


class TestAdminMembers:
    def test_member_list(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/members')
        assert response.status_code == 200
    
    def test_member_detail(self, client, admin_user, regular_user):
        """Test admin can view member details."""
        login(client, 'admin@test.com', 'admin123')
        response = client.get(f'/admin/members/{regular_user.id}')
        assert response.status_code == 200
        assert b'Regular User' in response.data


class TestAdminShootingNights:
    def test_shooting_night_list(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')
        response = client.get('/admin/shooting-nights')
        assert response.status_code == 200
    
    def test_shooting_night_create_get(self, client, admin_user):
        login(client, 'admin@test.com', 'admin123')


    def test_create_shooting_night(self, client, admin_user, regular_user):
        login(client, 'admin@test.com', 'admin123')

        response = client.get('/admin/shooting-nights/create')
        assert response.status_code == 200

        user = db.session.get(User, regular_user.id)
        initial_credits = user.current_membership.credits_remaining

        response = client.post('/admin/shooting-nights/create', data={
            'date': datetime.utcnow().date().isoformat(),
            'location': 'Hall',
            'attendees': [regular_user.id],
            'notes': 'Test'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify credit was deducted
        user = db.session.get(User, regular_user.id)
        assert user.current_membership.credits_remaining == initial_credits - 1
    
    def test_shooting_night_detail(self, client, admin_user, regular_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create shooting night first
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            created_by=admin_user.id
        )
        db.session.add(night)
        db.session.commit()
        
        response = client.get(f'/admin/shooting-nights/{night.id}')
        assert response.status_code == 200
    
    def test_shooting_night_edit_get(self, client, admin_user, regular_user):
        login(client, 'admin@test.com', 'admin123')
        
        # Create shooting night first
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            created_by=admin_user.id
        )
        db.session.add(night)
        db.session.flush()
        night.attendees.append(regular_user)
        db.session.commit()
        
        response = client.get(f'/admin/shooting-nights/{night.id}/edit')
        assert response.status_code == 200
    
    def test_shooting_night_edit_post(self, client, admin_user, regular_user):
        """Test editing a shooting night."""
        login(client, 'admin@test.com', 'admin123')
        
        # Create shooting night first
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            notes='Original notes',
            created_by=admin_user.id
        )
        db.session.add(night)
        db.session.flush()
        night.attendees.append(regular_user)
        db.session.commit()
        night_id = night.id
        
        # Get initial credits
        initial_credits = regular_user.current_membership.credits_remaining
        
        new_date = datetime.utcnow().date() + timedelta(days=1)
        response = client.post(f'/admin/shooting-nights/{night_id}/edit', data={
            'date': new_date.isoformat(),
            'location': 'Meadow',
            'notes': 'Updated notes',
            'attendees': [regular_user.id]
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated_night = db.session.get(ShootingNight, night_id)
        assert updated_night.location == 'Meadow'
        assert updated_night.notes == 'Updated notes'
    
    def test_shooting_night_edit_remove_attendee(self, client, admin_user, regular_user):
        """Test removing attendee from shooting night restores credits."""
        login(client, 'admin@test.com', 'admin123')
        
        # Create shooting night with attendee
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            created_by=admin_user.id
        )
        db.session.add(night)
        db.session.flush()
        night.attendees.append(regular_user)
        db.session.commit()
        night_id = night.id
        
        # Get initial credits
        db.session.refresh(regular_user)
        initial_credits = regular_user.current_membership.credits_remaining
        
        # Edit to remove attendee
        response = client.post(f'/admin/shooting-nights/{night_id}/edit', data={
            'date': night.date.isoformat(),
            'location': 'Hall',
            'attendees': []  # No attendees
        }, follow_redirects=True)
        
        assert response.status_code == 200
        db.session.refresh(regular_user)
        # Credits should be restored
        assert regular_user.current_membership.credits_remaining == initial_credits + 1
    
    def test_shooting_night_delete(self, client, admin_user, regular_user):
        """Test deleting a shooting night restores credits."""
        login(client, 'admin@test.com', 'admin123')
        
        # Create shooting night with attendee
        night = ShootingNight(
            date=datetime.utcnow().date(),
            location='Hall',
            created_by=admin_user.id
        )
        db.session.add(night)
        db.session.flush()
        night.attendees.append(regular_user)
        db.session.commit()
        night_id = night.id
        
        # Get initial credits
        db.session.refresh(regular_user)
        initial_credits = regular_user.current_membership.credits_remaining
        
        response = client.post(f'/admin/shooting-nights/{night_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        deleted_night = db.session.get(ShootingNight, night_id)
        assert deleted_night is None
        
        # Credits should be restored
        db.session.refresh(regular_user)
        assert regular_user.current_membership.credits_remaining == initial_credits + 1
