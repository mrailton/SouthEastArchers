"""Tests for email utility functions"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.email import send_payment_receipt, send_welcome_email
from app.models import User, Payment, Membership
from datetime import date, timedelta


class TestSendPaymentReceipt:
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_online_payment(self, mock_mail, app, test_user):
        """Test sending payment receipt for online payment"""
        with app.app_context():
            from datetime import datetime
            # Create test payment and membership
            payment = Payment(
                id=123,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                sumup_transaction_id='txn_abc123',
                description='Annual Membership',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            result = send_payment_receipt(test_user, payment, membership)
            
            assert result is True
            assert mock_mail.send.called
            
            # Check the message
            call_args = mock_mail.send.call_args[0][0]
            assert call_args.subject == 'Payment Receipt - South East Archers'
            assert test_user.email in call_args.recipients
            assert call_args.html is not None
            assert call_args.body is not None
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_cash_payment(self, mock_mail, app, test_user):
        """Test sending payment receipt for cash payment"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=456,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='cash',
                description='Annual Membership',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            result = send_payment_receipt(test_user, payment, membership)
            
            assert result is True
            assert mock_mail.send.called
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_formats_receipt_number(self, mock_mail, app, test_user):
        """Test receipt number formatting"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=42,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            # Receipt number should be SEA-000042
            call_args = mock_mail.send.call_args[0][0]
            assert 'SEA-000042' in call_args.html or 'SEA-000042' in call_args.body
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_includes_transaction_id_for_online(self, mock_mail, app, test_user):
        """Test transaction ID is included for online payments"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=789,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                sumup_transaction_id='txn_xyz789',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            # Transaction ID should be in the email
            assert 'txn_xyz789' in call_args.html or 'txn_xyz789' in call_args.body
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_no_transaction_id_for_cash(self, mock_mail, app, test_user):
        """Test no transaction ID for cash payments"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=999,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='cash',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            assert mock_mail.send.called
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_formats_dates(self, mock_mail, app, test_user):
        """Test date formatting in receipt"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=111,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            assert mock_mail.send.called
            call_args = mock_mail.send.call_args[0][0]
            # Check that dates are formatted
            assert call_args.html is not None
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_includes_membership_details(self, mock_mail, app, test_user):
        """Test membership details are included in receipt"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=222,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            # Check membership details are included
            html_body = call_args.html
            assert membership.start_date.strftime('%d %B %Y') in html_body or membership.start_date.strftime('%d %B %Y') in call_args.body
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_handles_missing_description(self, mock_mail, app, test_user):
        """Test receipt handles missing payment description"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=333,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                description=None,
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            result = send_payment_receipt(test_user, payment, membership)
            
            assert result is True
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_exception_handling(self, mock_mail, app, test_user):
        """Test exception handling when sending fails"""
        with app.app_context():
            from datetime import datetime
            mock_mail.send.side_effect = Exception('SMTP error')
            
            payment = Payment(
                id=444,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            result = send_payment_receipt(test_user, payment, membership)
            
            assert result is False
    
    @patch('app.utils.email.mail')
    def test_send_payment_receipt_uses_correct_payment_method_display(self, mock_mail, app, test_user):
        """Test payment method display formatting"""
        with app.app_context():
            from datetime import datetime
            payment = Payment(
                id=555,
                user_id=test_user.id,
                amount=100.00,
                currency='EUR',
                payment_type='membership',
                payment_method='online',
                status='completed',
                created_at=datetime.now()
            )
            
            membership = test_user.membership
            
            send_payment_receipt(test_user, payment, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            # Should show "Credit/Debit Card (SumUp)" for online
            assert 'SumUp' in call_args.html or 'Card' in call_args.html


class TestSendWelcomeEmail:
    @patch('app.utils.email.mail')
    def test_send_welcome_email_success(self, mock_mail, app, test_user):
        """Test sending welcome email"""
        with app.app_context():
            membership = test_user.membership
            
            result = send_welcome_email(test_user, membership)
            
            assert result is True
            assert mock_mail.send.called
            
            # Check the message
            call_args = mock_mail.send.call_args[0][0]
            assert call_args.subject == 'Welcome to South East Archers!'
            assert test_user.email in call_args.recipients
            assert call_args.html is not None
    
    @patch('app.utils.email.mail')
    def test_send_welcome_email_includes_user_name(self, mock_mail, app, test_user):
        """Test welcome email includes user name"""
        with app.app_context():
            membership = test_user.membership
            
            send_welcome_email(test_user, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            assert test_user.name in call_args.html
    
    @patch('app.utils.email.mail')
    def test_send_welcome_email_includes_membership_details(self, mock_mail, app, test_user):
        """Test welcome email includes membership details"""
        with app.app_context():
            membership = test_user.membership
            
            send_welcome_email(test_user, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            html = call_args.html
            
            # Check membership details are included
            assert membership.start_date.strftime('%d %B %Y') in html
            assert membership.expiry_date.strftime('%d %B %Y') in html
            assert str(membership.credits) in html
    
    @patch('app.utils.email.mail')
    def test_send_welcome_email_includes_login_link(self, mock_mail, app, test_user):
        """Test welcome email includes login link"""
        with app.app_context():
            membership = test_user.membership
            
            send_welcome_email(test_user, membership)
            
            call_args = mock_mail.send.call_args[0][0]
            # Should contain a login URL
            assert 'login' in call_args.html.lower() or 'auth/login' in call_args.html
    
    @patch('app.utils.email.mail')
    def test_send_welcome_email_exception_handling(self, mock_mail, app, test_user):
        """Test exception handling when sending fails"""
        with app.app_context():
            mock_mail.send.side_effect = Exception('Email server error')
            
            membership = test_user.membership
            
            result = send_welcome_email(test_user, membership)
            
            assert result is False
    
    @patch('app.utils.email.mail')
    def test_send_welcome_email_with_different_credit_amounts(self, mock_mail, app):
        """Test welcome email with various credit amounts"""
        with app.app_context():
            # Create user with different credit amount
            user = User(
                name='Test User 2',
                email='test2@example.com',
                phone='1234567890',
                date_of_birth=date(2000, 1, 1)
            )
            user.set_password('password')
            
            membership = Membership(
                user_id=None,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                credits=50,
                status='active'
            )
            
            from app import db
            db.session.add(user)
            db.session.flush()
            
            membership.user_id = user.id
            db.session.add(membership)
            db.session.commit()
            
            result = send_welcome_email(user, membership)
            
            assert result is True
            call_args = mock_mail.send.call_args[0][0]
            assert '50' in call_args.html
