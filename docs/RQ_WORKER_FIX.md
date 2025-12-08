# RQ Worker Flask Context Fix

## Issue

RQ workers were failing with the error:
```
RuntimeError: Working outside of application context.
```

This occurred when background jobs tried to access the database or Flask-specific functions.

## Root Cause

RQ workers run in a separate process from the Flask application. When a job is executed, it doesn't automatically have access to Flask's application context, which is required for:
- Database operations (`db.session`)
- Flask utilities (`current_app`, `url_for`, `render_template`)
- Flask-Mail operations

## Solution

Wrapped each background job function with Flask's application context:

```python
def send_payment_receipt_job(user_id, payment_id):
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Job code here - now has access to Flask context
        user = db.session.get(User, user_id)
        # ... rest of job
```

## Files Updated

- **app/services/background_jobs.py** - All job functions now create app context

## How It Works

1. Each job imports `create_app` from the app factory
2. Creates a new Flask app instance
3. Uses `app.app_context()` context manager
4. All code inside the context has access to Flask features

## Testing

```python
# Queue a job
from app.services.queue import queue_job

queue_job('send_payment_receipt_job', user_id=1, payment_id=1)

# Check worker logs - should see success instead of error
```

## Alternative Approaches

### Option 1: Push App Context in Worker (Not Chosen)
Could modify `worker.py` to push app context globally, but this is less flexible and harder to test.

### Option 2: Use Flask-RQ2 (Overkill)
Flask-RQ2 automatically handles context, but adds another dependency and wraps RQ heavily.

### Option 3: Current Approach (Chosen) ✅
Each job manages its own context - explicit, testable, and no extra dependencies.

## Benefits

- ✅ Explicit and clear
- ✅ Each job is self-contained
- ✅ Easy to test individually
- ✅ No global state issues
- ✅ Works with RQ's worker architecture

## Important Notes

- Each job creates its own app instance - this is fine for background jobs
- The app instance is lightweight and created on-demand
- Database connections are managed per job (committed/rolled back properly)
- No memory leaks - context manager ensures cleanup

## Related Documentation

- [Background Jobs Guide](BACKGROUND_JOBS.md)
- [Flask Application Context](https://flask.palletsprojects.com/en/latest/appcontext/)
- [RQ Documentation](https://python-rq.org/)
