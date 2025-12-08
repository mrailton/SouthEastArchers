# URL Generation in Background Jobs Fix

## Issue

Background jobs (RQ workers) were failing with:
```
RuntimeError: Unable to build URLs outside an active request without 'SERVER_NAME' configured.
Also configure 'APPLICATION_ROOT' and 'PREFERRED_URL_SCHEME' as needed.
```

This occurred when emails tried to generate URLs using `url_for(..., _external=True)`.

## Root Cause

Flask's `url_for(..., _external=True)` requires certain configuration values to generate absolute URLs outside of a request context:
- `SERVER_NAME` - The domain name of your application
- `PREFERRED_URL_SCHEME` - `http` or `https`
- `APPLICATION_ROOT` - The base path (usually `/`)

Background jobs run without a request context, so these must be configured.

## Solution

### 1. Added Configuration

**config/config.py:**
```python
class Config:
    SERVER_NAME = os.environ.get("SERVER_NAME")
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT", "/")

class DevelopmentConfig(Config):
    SERVER_NAME = os.environ.get("SERVER_NAME", "localhost:5000")
    PREFERRED_URL_SCHEME = "http"

class TestingConfig(Config):
    SERVER_NAME = "localhost.localdomain"
    PREFERRED_URL_SCHEME = "http"
```

### 2. Added URL Generation Fallback

**app/utils/email.py:**
```python
# Generate login URL safely
try:
    login_url = url_for("auth.login", _external=True)
except RuntimeError:
    # Fallback if SERVER_NAME not configured
    login_url = current_app.config.get("SITE_URL", "https://southeastarchers.ie") + "/login"
```

This provides a fallback mechanism if `SERVER_NAME` is not configured.

### 3. Updated Environment Variables

**.env.example:**
```bash
SERVER_NAME=localhost:5000
PREFERRED_URL_SCHEME=http
SITE_URL=http://localhost:5000
```

**docker/.env.production.example:**
```bash
SERVER_NAME=southeastarchers.ie
PREFERRED_URL_SCHEME=https
SITE_URL=https://southeastarchers.ie
```

### 4. Updated Docker Compose

**docker/docker-compose.yml:**
```yaml
web:
  environment:
    SERVER_NAME: ${SERVER_NAME}
    PREFERRED_URL_SCHEME: ${PREFERRED_URL_SCHEME:-https}
    SITE_URL: ${SITE_URL}

worker:
  environment:
    SERVER_NAME: ${SERVER_NAME}
    PREFERRED_URL_SCHEME: ${PREFERRED_URL_SCHEME:-https}
    SITE_URL: ${SITE_URL}
```

## Files Modified

- ✅ `config/config.py` - Added SERVER_NAME configuration
- ✅ `app/utils/email.py` - Added fallback URL generation
- ✅ `.env.example` - Added SERVER_NAME variables
- ✅ `docker/.env.production.example` - Added production config
- ✅ `docker/docker-compose.yml` - Added environment variables
- ✅ `tests/utils/test_email.py` - Added comprehensive tests

## Environment Variables

### Required for Production

```bash
# Your domain name (without protocol)
SERVER_NAME=southeastarchers.ie

# Protocol to use
PREFERRED_URL_SCHEME=https

# Full site URL (fallback)
SITE_URL=https://southeastarchers.ie
```

### For Development

```bash
SERVER_NAME=localhost:5000
PREFERRED_URL_SCHEME=http
SITE_URL=http://localhost:5000
```

### For Dokploy

Add these to your Dokploy environment variables:
```
SERVER_NAME=your-domain.com
PREFERRED_URL_SCHEME=https
SITE_URL=https://your-domain.com
```

## How It Works

### With SERVER_NAME Configured (Normal Case)

1. Background job runs in app context
2. Flask uses `SERVER_NAME` to generate URLs
3. `url_for("auth.login", _external=True)` works
4. Email contains: `https://southeastarchers.ie/login`

### Without SERVER_NAME (Fallback)

1. Background job runs in app context
2. `url_for(..., _external=True)` raises `RuntimeError`
3. Code catches exception
4. Uses `SITE_URL + "/login"` as fallback
5. Email still contains correct URL

## Testing

### Manual Testing

```bash
# Set environment variables
export SERVER_NAME=localhost:5000
export PREFERRED_URL_SCHEME=http

# Run worker
python worker.py

# Queue a job (from Flask shell or app)
from app.services.background_jobs import send_payment_receipt_job
send_payment_receipt_job(user_id=1, payment_id=1)

# Check worker logs - should see success
```

### Automated Testing

```bash
# Run email tests
pytest tests/utils/test_email.py -v

# Specifically test URL generation
pytest tests/utils/test_email.py::TestEmailURLGeneration -v
```

## Tests Added

1. **test_email_with_server_name_configured**
   - Verifies emails work with SERVER_NAME set

2. **test_email_without_server_name_uses_fallback**
   - Tests fallback mechanism when SERVER_NAME missing

3. **test_welcome_email_with_url_generation**
   - Ensures welcome emails generate URLs correctly

4. **test_welcome_email_without_server_name**
   - Tests welcome email fallback

5. **test_config_has_server_name_in_testing**
   - Ensures test config has SERVER_NAME

6. **test_config_has_site_url_fallback**
   - Verifies SITE_URL fallback availability

## Common Issues

### Issue: Still getting URL generation error

**Check:**
1. Is `SERVER_NAME` set in environment?
2. Is worker using correct environment?
3. Did you restart worker after setting variables?

**Debug:**
```bash
# In worker or Flask shell
from flask import current_app
print(current_app.config.get("SERVER_NAME"))
print(current_app.config.get("PREFERRED_URL_SCHEME"))
```

### Issue: URLs have wrong domain

**Check:**
- `SERVER_NAME` should NOT include protocol (`https://`)
- `SERVER_NAME` should match your actual domain
- For localhost development, include port: `localhost:5000`

**Correct:**
- ✅ `SERVER_NAME=southeastarchers.ie`
- ✅ `SERVER_NAME=localhost:5000`

**Incorrect:**
- ❌ `SERVER_NAME=https://southeastarchers.ie`
- ❌ `SERVER_NAME=http://localhost:5000`

### Issue: Tests failing with URL generation error

**Fix:**
Ensure TestingConfig has SERVER_NAME:
```python
class TestingConfig(Config):
    SERVER_NAME = "localhost.localdomain"
    PREFERRED_URL_SCHEME = "http"
```

## Best Practices

1. **Always set SERVER_NAME in production**
   - Required for email URLs
   - Required for background jobs
   - Required for URL generation

2. **Use SITE_URL as fallback**
   - Provides backup if SERVER_NAME not set
   - Useful for local development
   - Safety net for configuration issues

3. **Test both scenarios**
   - Test with SERVER_NAME configured
   - Test without (fallback)
   - Ensures robustness

4. **Use environment variables**
   - Don't hardcode domain names
   - Different for dev/staging/prod
   - Easy to change without code updates

## Related Documentation

- [Flask URL Building](https://flask.palletsprojects.com/en/latest/api/#url-building)
- [Flask Configuration](https://flask.palletsprojects.com/en/latest/config/)
- [RQ Worker Fix](RQ_WORKER_FIX.md)
- [Background Jobs Guide](BACKGROUND_JOBS.md)

## Summary

✅ **Fixed:** URL generation in background jobs
✅ **Added:** SERVER_NAME configuration
✅ **Added:** Fallback URL generation
✅ **Added:** Comprehensive tests
✅ **Updated:** All environment examples
✅ **Updated:** Docker Compose files

Background jobs can now generate URLs correctly in all environments!
