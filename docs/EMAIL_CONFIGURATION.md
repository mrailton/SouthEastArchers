# Email Configuration Guide

## Issue

SMTP authentication failing with error:
```
538 Error: Must issue a STARTTLS command first
```

This occurs when the SMTP server requires STARTTLS encryption before authentication, but Flask-Mail isn't configured to use it.

## Solution

Ensure `MAIL_USE_TLS` is set to `True` and `MAIL_USE_SSL` is set to `False` for STARTTLS on port 587.

## Configuration

### Environment Variables

```bash
# SMTP Server Configuration
MAIL_SERVER=smtp.mailersend.net       # Your SMTP server
MAIL_PORT=587                         # Port 587 for STARTTLS
MAIL_USE_TLS=True                     # Enable STARTTLS (required!)
MAIL_USE_SSL=False                    # Disable SSL (use TLS instead)
MAIL_USERNAME=your-username           # SMTP username
MAIL_PASSWORD=your-password           # SMTP password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

### Port Selection

| Port | Protocol | Use Case | Configuration |
|------|----------|----------|---------------|
| 587  | STARTTLS | **Recommended** | `MAIL_USE_TLS=True` `MAIL_USE_SSL=False` |
| 465  | SSL/TLS  | Legacy | `MAIL_USE_TLS=False` `MAIL_USE_SSL=True` |
| 25   | Plain    | Internal only | Not recommended |

## Common SMTP Providers

### MailerSend

```bash
MAIL_SERVER=smtp.mailersend.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=MS_xxxxxx@yourdomain.com
MAIL_PASSWORD=your-api-token
```

### Gmail

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use App Password, not regular password
```

### SendGrid

```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

### Mailgun

```bash
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=postmaster@yourdomain.mailgun.org
MAIL_PASSWORD=your-mailgun-password
```

### AWS SES

```bash
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-ses-smtp-username
MAIL_PASSWORD=your-ses-smtp-password
```

## Dokploy Configuration

Add these environment variables in Dokploy:

1. Go to your application in Dokploy
2. Navigate to **Environment Variables**
3. Add each variable:

```
MAIL_SERVER = smtp.mailersend.net
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = MS_xxxxxx@yourdomain.com
MAIL_PASSWORD = your-password
MAIL_DEFAULT_SENDER = noreply@yourdomain.com
```

4. **Redeploy** the application

## Troubleshooting

### Error: Must issue a STARTTLS command first

**Problem:** Server requires STARTTLS but it's not being used

**Solution:**
```bash
MAIL_USE_TLS=True  # ✅ Must be True
MAIL_USE_SSL=False # ✅ Must be False
MAIL_PORT=587      # ✅ Use port 587
```

### Error: Connection refused

**Problem:** Wrong port or server

**Solution:**
- Check `MAIL_SERVER` is correct
- Verify `MAIL_PORT` (usually 587)
- Test connection: `telnet smtp.server.com 587`

### Error: Authentication failed

**Problem:** Invalid credentials

**Solution:**
- Verify `MAIL_USERNAME` is correct
- Check `MAIL_PASSWORD` (some providers use API keys)
- For Gmail: Use App Password, not regular password
- Check if account is enabled for SMTP

### Error: SSL/TLS negotiation failed

**Problem:** Wrong SSL/TLS settings

**Solution:**
- For port 587: `MAIL_USE_TLS=True`, `MAIL_USE_SSL=False`
- For port 465: `MAIL_USE_TLS=False`, `MAIL_USE_SSL=True`
- Never set both to True

### Test Email Configuration

Create a test script:

```python
# test_email.py
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.mailersend.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your-username'
app.config['MAIL_PASSWORD'] = 'your-password'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@yourdomain.com'

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject='Test Email',
        recipients=['test@example.com'],
        body='This is a test email'
    )
    try:
        mail.send(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
```

Run: `python test_email.py`

## Configuration in Code

The configuration is set in `config/config.py`:

```python
class Config:
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in (
        "true", "1", "yes", "on"
    )
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False").lower() in (
        "true", "1", "yes", "on"
    )
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@southeastarchers.ie"
    )
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all sensitive data
3. **Use App Passwords** for Gmail (not your regular password)
4. **Rotate passwords** regularly
5. **Use STARTTLS** (port 587) over SSL/TLS (port 465)
6. **Monitor email logs** for suspicious activity
7. **Set up SPF/DKIM/DMARC** records for your domain

## Verification

After configuration, verify emails are working:

1. **Trigger a test email** (e.g., password reset, payment receipt)
2. **Check worker logs** for success/errors
3. **Check recipient inbox** (including spam folder)
4. **Monitor SMTP provider dashboard** for delivery status

## Related Documentation

- [Flask-Mail Documentation](https://flask-mail.readthedocs.io/)
- [Background Jobs Guide](BACKGROUND_JOBS.md)
- [RQ Worker Fix](RQ_WORKER_FIX.md)
- [Dokploy Deployment](DOKPLOY_DEPLOYMENT.md)

---

**Quick Fix:** For STARTTLS on port 587, ensure `MAIL_USE_TLS=True` and `MAIL_USE_SSL=False`
