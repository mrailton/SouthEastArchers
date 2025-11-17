"""Tests for admin CRUD operations"""
import pytest
from datetime import date, timedelta
from app.models import User, News, Event, Shoot, ShootLocation, Membership


class TestAdminMemberCRUD:
    def test_create_member_page(self, client, admin_user):
        """Test accessing create member page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/members/create')
        assert response.status_code == 200
        assert b'Create Member' in response.data

    def test_create_member_success(self, client, admin_user, app):
        """Test creating a new member"""
        from app import db
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post('/admin/members/create', data={
            'name': 'New Member',
            'email': 'newmember@example.com',
            'phone': '1234567890',
            'date_of_birth': '2000-01-01',
            'password': 'testpass123',
            'create_membership': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify member was created
        new_user = User.query.filter_by(email='newmember@example.com').first()
        assert new_user is not None
        assert new_user.name == 'New Member'
        assert new_user.membership is not None
        assert new_user.membership.credits == 20

    def test_create_member_duplicate_email(self, client, admin_user, test_user):
        """Test creating member with duplicate email"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post('/admin/members/create', data={
            'name': 'Duplicate',
            'email': test_user.email,
            'date_of_birth': '2000-01-01',
            'password': 'testpass'
        })
        
        assert response.status_code == 200
        assert b'already registered' in response.data

    def test_edit_member_page(self, client, admin_user, test_user):
        """Test accessing edit member page"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/members/{test_user.id}/edit')
        assert response.status_code == 200
        assert b'Edit Member' in response.data
        assert test_user.name.encode() in response.data

    def test_edit_member_success(self, client, admin_user, test_user):
        """Test updating member details"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/members/{test_user.id}/edit', data={
            'name': 'Updated Name',
            'email': test_user.email,
            'phone': '9876543210',
            'date_of_birth': test_user.date_of_birth.isoformat(),
            'is_admin': '',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes
        from app import db
        db.session.refresh(test_user)
        assert test_user.name == 'Updated Name'
        assert test_user.phone == '9876543210'

    def test_edit_member_change_password(self, client, admin_user, test_user):
        """Test changing member password"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/members/{test_user.id}/edit', data={
            'name': test_user.name,
            'email': test_user.email,
            'date_of_birth': test_user.date_of_birth.isoformat(),
            'password': 'newpassword123',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify password was changed
        from app import db
        db.session.refresh(test_user)
        assert test_user.check_password('newpassword123')


class TestAdminNewsCRUD:
    def test_edit_news_page(self, client, admin_user, app):
        """Test accessing edit news page"""
        from app import db
        
        news = News(
            title='Test News',
            content='Test content here',
            published=False
        )
        db.session.add(news)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/news/{news.id}/edit')
        assert response.status_code == 200
        assert b'Edit News' in response.data
        assert b'Test News' in response.data

    def test_edit_news_success(self, client, admin_user, app):
        """Test updating news article"""
        from app import db
        
        news = News(
            title='Original Title',
            content='Original content',
            published=False
        )
        db.session.add(news)
        db.session.commit()
        news_id = news.id
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/news/{news_id}/edit', data={
            'title': 'Updated Title',
            'summary': 'Updated summary',
            'content': 'Updated content here with more text',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes
        updated_news = db.session.get(News, news_id)
        assert updated_news.title == 'Updated Title'
        assert updated_news.published is True
        assert updated_news.published_at is not None

    def test_edit_news_not_found(self, client, admin_user):
        """Test editing non-existent news"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/news/99999/edit')
        assert response.status_code == 404


class TestAdminEventCRUD:
    def test_edit_event_page(self, client, admin_user, app):
        """Test accessing edit event page"""
        from app import db
        from datetime import datetime
        
        event = Event(
            title='Test Event',
            description='Test description',
            start_date=datetime.now(),
            published=False
        )
        db.session.add(event)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get(f'/admin/events/{event.id}/edit')
        assert response.status_code == 200
        assert b'Edit Event' in response.data
        assert b'Test Event' in response.data

    def test_edit_event_success(self, client, admin_user, app):
        """Test updating event"""
        from app import db
        from datetime import datetime
        
        event = Event(
            title='Original Event',
            description='Original description',
            start_date=datetime.now(),
            published=False
        )
        db.session.add(event)
        db.session.commit()
        event_id = event.id
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        new_date = datetime.now().strftime('%Y-%m-%dT%H:%M')
        response = client.post(f'/admin/events/{event_id}/edit', data={
            'title': 'Updated Event',
            'description': 'Updated description',
            'start_date': new_date,
            'location': 'New Location',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes
        updated_event = db.session.get(Event, event_id)
        assert updated_event.title == 'Updated Event'
        assert updated_event.location == 'New Location'
        assert updated_event.published is True

    def test_edit_event_not_found(self, client, admin_user):
        """Test editing non-existent event"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.get('/admin/events/99999/edit')
        assert response.status_code == 404


class TestAdminPermissions:
    def test_create_member_requires_admin(self, client, test_user):
        """Test that create member requires admin"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get('/admin/members/create')
        assert response.status_code in [302, 403]

    def test_edit_member_requires_admin(self, client, test_user):
        """Test that edit member requires admin"""
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get(f'/admin/members/{test_user.id}/edit')
        assert response.status_code in [302, 403]

    def test_edit_news_requires_admin(self, client, test_user, app):
        """Test that edit news requires admin"""
        from app import db
        
        news = News(title='Test', content='Test content')
        db.session.add(news)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get(f'/admin/news/{news.id}/edit')
        assert response.status_code in [302, 403]

    def test_edit_event_requires_admin(self, client, test_user, app):
        """Test that edit event requires admin"""
        from app import db
        from datetime import datetime
        
        event = Event(
            title='Test',
            description='Test',
            start_date=datetime.now()
        )
        db.session.add(event)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        response = client.get(f'/admin/events/{event.id}/edit')
        assert response.status_code in [302, 403]


class TestAdminMembershipEdit:
    def test_edit_member_membership_dates(self, client, admin_user, test_user):
        """Test updating membership dates"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        from datetime import date, timedelta
        new_start = date.today() - timedelta(days=10)
        new_expiry = date.today() + timedelta(days=355)
        
        response = client.post(f'/admin/members/{test_user.id}/edit', data={
            'name': test_user.name,
            'email': test_user.email,
            'date_of_birth': test_user.date_of_birth.isoformat(),
            'is_active': 'on',
            'membership_start_date': new_start.isoformat(),
            'membership_expiry_date': new_expiry.isoformat(),
            'membership_credits': str(test_user.membership.credits)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify membership dates were updated
        from app import db
        db.session.refresh(test_user)
        assert test_user.membership.start_date == new_start
        assert test_user.membership.expiry_date == new_expiry

    def test_edit_member_credits(self, client, admin_user, test_user):
        """Test updating member credits"""
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/members/{test_user.id}/edit', data={
            'name': test_user.name,
            'email': test_user.email,
            'date_of_birth': test_user.date_of_birth.isoformat(),
            'is_active': 'on',
            'membership_start_date': test_user.membership.start_date.isoformat(),
            'membership_expiry_date': test_user.membership.expiry_date.isoformat(),
            'membership_credits': '50'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify credits were updated
        from app import db
        db.session.refresh(test_user)
        assert test_user.membership.credits == 50

    def test_edit_member_without_membership(self, client, admin_user, app):
        """Test editing member without membership"""
        from app import db
        
        user = User(
            name='No Membership User',
            email='nomembership@example.com',
            date_of_birth=date(2000, 1, 1)
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpass'
        })
        
        response = client.post(f'/admin/members/{user.id}/edit', data={
            'name': 'Updated Name',
            'email': user.email,
            'date_of_birth': user.date_of_birth.isoformat(),
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify name was updated even without membership
        db.session.refresh(user)
        assert user.name == 'Updated Name'
