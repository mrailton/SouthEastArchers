# Test Suite Documentation

This directory contains the comprehensive test suite for the South East Archers application using PyTest.

## Test Coverage

Current test coverage: **75.43%**

## Test Structure

### Test Files

- **`conftest.py`** - PyTest configuration and fixtures
- **`test_app.py`** - Main application tests covering models, authentication, admin, member routes, and forms
- **`test_main.py`** - Public page tests (home, news, events, about)

### Test Classes

1. **TestModels** - Tests for database models
   - User creation and password hashing
   - Membership and credits functionality
   - Shooting night attendance tracking

2. **TestAuthentication** - Tests for auth routes
   - Login page rendering
   - Successful login
   - User registration

3. **TestAdminRoutes** - Tests for admin functionality
   - Admin access control
   - Dashboard access
   - Shooting night creation
   - Member management

4. **TestMemberRoutes** - Tests for member functionality
   - Member dashboard access
   - Credit purchase

5. **TestForms** - Tests for form validation
   - Login form validation
   - Registration form validation
   - Shooting night form validation

6. **TestPublicPages** - Tests for public pages
   - Home, about, news, events pages
   - 404 error handling

## Fixtures

### App Fixtures
- **`app`** - Test application instance with in-memory SQLite database
- **`client`** - Test client for making HTTP requests
- **`runner`** - Test CLI runner

### User Fixtures
- **`admin_user`** - Admin user with 20 credits
- **`regular_user`** - Regular member with 15 credits
- **`multiple_users`** - Three test users for bulk operations

### Data Fixtures
- **`sample_news`** - Three sample news articles
- **`sample_event`** - Sample event
- **`sample_shooting_night`** - Shooting night with attendance

### Helper Functions
- **`login(client, email, password)`** - Helper to log in a user
- **`logout(client)`** - Helper to log out a user

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_app.py
```

### Run specific test class
```bash
pytest tests/test_app.py::TestModels
```

### Run specific test
```bash
pytest tests/test_app.py::TestModels::test_user_creation
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Generate HTML coverage report
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Run tests matching pattern
```bash
pytest tests/ -k "admin"  # Run all tests with 'admin' in name
```

### Show test collection without running
```bash
pytest tests/ --collect-only
```

## Test Configuration

### pytest.ini
- Configured test paths, naming conventions
- Warning suppression
- Short traceback format
- Markers for slow/integration tests

### .coveragerc
- Coverage source configuration
- File omissions (venv, migrations, tests)
- Report formatting

## Writing New Tests

### Basic Test Structure
```python
def test_feature_name(app, fixture):
    """Test description."""
    # Arrange
    user = User(email='test@test.com', name='Test')
    
    # Act
    db.session.add(user)
    db.session.commit()
    
    # Assert
    assert user.id is not None
```

### Testing Routes
```python
def test_route(client, regular_user):
    """Test route access."""
    login(client, 'user@test.com', 'user123')
    response = client.get('/member/dashboard')
    assert response.status_code == 200
    assert b'Expected Content' in response.data
```

### Testing Forms
```python
def test_form(app):
    """Test form validation."""
    form = MyForm(data={'field': 'value'})
    assert form.validate()
    assert form.field.data == 'value'
```

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test
- Automatically cleaned up after each test
- Isolated from production data
- Fast and reliable

## Coverage Goals

Target coverage by module:
- Models: 95%+
- Routes: 80%+
- Forms: 95%+
- Overall: 85%+

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pytest tests/ --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Database Session Issues
If you see "DetachedInstanceError", ensure objects are refreshed:
```python
db.session.refresh(user)
```

### Fixture Scope
- Use `scope='function'` for most fixtures (default)
- Use `scope='session'` only for read-only setup

### CSRF Protection
CSRF is disabled in tests via `WTF_CSRF_ENABLED = False` in TestConfig

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Descriptive Names** - Use clear test and class names
3. **One Assert Per Test** - Focus on single behavior
4. **Use Fixtures** - Reuse setup code via fixtures
5. **Test Edge Cases** - Include boundary conditions
6. **Keep Tests Fast** - Use in-memory database
7. **Document Tests** - Include docstrings
8. **Follow AAA** - Arrange, Act, Assert pattern

## Dependencies

```
pytest==8.3.3
pytest-cov==6.0.0
pytest-flask==1.3.0
```

## Additional Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
