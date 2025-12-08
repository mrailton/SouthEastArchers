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

Created a smart context manager that:
1. Checks if already running in an app context (e.g., during tests)
2. If yes, uses existing context
3. If no, creates new context for the worker

```python
def _get_app_context():
    """Get or create app context for background jobs"""
    if has_app_context():
        # Already in app context (e.g., during tests)
        return None
    else:
        # Create new app context for worker
        from app import create_app
        app = create_app()
        return app.app_context()

def send_payment_receipt_job(user_id, payment_id):
    ctx = _get_app_context()
    try:
        if ctx:
            ctx.push()
        
        # Job code here - has access to Flask context
        user = db.session.get(User, user_id)
        # ... rest of job
    finally:
        if ctx:
            ctx.pop()
```

## Files Updated

- **app/services/background_jobs.py** - All job functions now use smart context

## How It Works

### In Production (RQ Worker)
1. `has_app_context()` returns `False`
2. Creates new Flask app instance
3. Pushes app context
4. Executes job
5. Pops context in finally block

### In Tests
1. Test fixture already provides app context
2. `has_app_context()` returns `True`
3. Returns `None` (no new context needed)
4. Job uses existing test context
5. Test can mock/verify normally

## Benefits

- ✅ Works in production workers
- ✅ Works in test environment
- ✅ No duplicate contexts
- ✅ Proper cleanup with try/finally
- ✅ Each job is self-contained
- ✅ Easy to test individually

## Testing

```python
# In tests - job uses test app context
def test_send_payment_receipt_job(app, test_user_with_payment):
    user = test_user_with_payment["user"]
    payment = test_user_with_payment["payment"]
    
    # Already in app.app_context(), job will detect and use it
    send_payment_receipt_job(user.id, payment.id)
    # Works!

# In production - job creates its own context
# Queue a job
queue_job('send_payment_receipt_job', user_id=1, payment_id=1)
# Worker creates context automatically
```

## Why This Approach?

### Alternative 1: Always Create Context (Previous)
❌ Creates unnecessary nested contexts in tests
❌ Can cause database session issues
❌ Tests try to connect to production database

### Alternative 2: Push Context in Worker
❌ Less flexible
❌ Harder to test
❌ Global state issues

### Alternative 3: Smart Context Detection (Current) ✅
✅ Works everywhere
✅ Efficient
✅ Test-friendly
✅ Production-ready

## Important Notes

- Uses `has_app_context()` to detect existing context
- Uses `try/finally` to ensure cleanup
- Context only created when needed
- No memory leaks or connection issues
- Works with Flask's request-local state

## Related Documentation

- [Background Jobs Guide](BACKGROUND_JOBS.md)
- [Flask Application Context](https://flask.palletsprojects.com/en/latest/appcontext/)
- [RQ Documentation](https://python-rq.org/)

