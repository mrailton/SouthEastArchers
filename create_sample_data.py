#!/usr/bin/env python3
"""Create sample data for testing the application"""

from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Membership, News, Event

def create_sample_data():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@southeastarchers.ie').first()
        
        if not admin:
            # Create admin user
            admin = User(
                email='admin@southeastarchers.ie',
                first_name='Admin',
                last_name='User',
                phone='0871234567',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create admin membership
            admin_membership = Membership(
                user=admin,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365),
                credits_remaining=20,
                amount_paid=100.0
            )
            db.session.add(admin_membership)
            print("✓ Admin user created: admin@southeastarchers.ie / admin123")
        else:
            print("✓ Admin user already exists")
        
        # Create sample regular user
        member = User.query.filter_by(email='member@example.com').first()
        if not member:
            member = User(
                email='member@example.com',
                first_name='John',
                last_name='Doe',
                phone='0879876543',
                is_admin=False
            )
            member.set_password('member123')
            db.session.add(member)
            
            # Create member membership
            member_membership = Membership(
                user=member,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365),
                credits_remaining=15,
                amount_paid=100.0
            )
            db.session.add(member_membership)
            print("✓ Sample member created: member@example.com / member123")
        else:
            print("✓ Sample member already exists")
        
        # Create sample news articles
        if News.query.count() == 0:
            news1 = News(
                title='Welcome to South East Archers!',
                content='We are excited to announce the launch of our new website! Members can now register online, purchase credits, and stay up to date with all club news and events.',
                author_id=admin.id if admin else 1,
                published=True
            )
            
            news2 = News(
                title='New Training Program Starting',
                content='We are pleased to announce a new beginner training program starting next month. This 6-week course will cover all the basics of archery and is perfect for newcomers to the sport. Contact us for more information.',
                author_id=admin.id if admin else 1,
                published=True
            )
            
            news3 = News(
                title='Club Championship Results',
                content='Congratulations to all participants in last weekend\'s club championship! The competition was fierce and we saw some excellent shooting. Full results will be posted on the notice board.',
                author_id=admin.id if admin else 1,
                published=True
            )
            
            db.session.add_all([news1, news2, news3])
            print("✓ Sample news articles created")
        else:
            print("✓ News articles already exist")
        
        # Create sample events
        if Event.query.count() == 0:
            event1 = Event(
                title='Beginner\'s Night',
                description='New to archery? Join us for a beginner-friendly evening where we\'ll introduce you to the basics of the sport. Equipment provided.',
                event_date=datetime.utcnow() + timedelta(days=7),
                location='Main Range',
                published=True,
                created_by=admin.id if admin else 1
            )
            
            event2 = Event(
                title='Monthly Club Shoot',
                description='Our regular monthly competition. All members welcome! Various categories for different skill levels.',
                event_date=datetime.utcnow() + timedelta(days=14),
                location='Main Range',
                published=True,
                created_by=admin.id if admin else 1
            )
            
            event3 = Event(
                title='Equipment Maintenance Workshop',
                description='Learn how to properly maintain your archery equipment. Bring your bow and we\'ll show you how to keep it in top condition.',
                event_date=datetime.utcnow() + timedelta(days=21),
                location='Clubhouse',
                published=True,
                created_by=admin.id if admin else 1
            )
            
            db.session.add_all([event1, event2, event3])
            print("✓ Sample events created")
        else:
            print("✓ Events already exist")
        
        db.session.commit()
        print("\n✅ Sample data created successfully!")
        print("\nYou can now log in with:")
        print("  Admin: admin@southeastarchers.ie / admin123")
        print("  Member: member@example.com / member123")

if __name__ == '__main__':
    create_sample_data()
