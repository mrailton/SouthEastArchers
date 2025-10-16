# Testing Documentation

## Overview

This project includes a comprehensive test suite built with PyTest, achieving **75.43% code coverage** across all application modules.

## Quick Start

### Run All Tests
```bash
./run_tests.sh
```

### Run Tests with Coverage
```bash
./run_tests.sh coverage
```

### Run Specific Tests
```bash
./run_tests.sh specific admin
```

## Test Suite Statistics

- **Total Tests**: 22
- **Test Files**: 3 (conftest.py, test_app.py, test_main.py)
- **Code Coverage**: 75.43%
- **Test Execution Time**: ~2.2 seconds

## Coverage by Module

| Module | Statements | Missing | Coverage |
|--------|-----------|---------|----------|
| app/__init__.py | 25 | 1 | 96.00% |
| app/forms.py | 38 | 0 | 100.00% |
| app/models.py | 93 | 6 | 93.55% |
| app/routes/admin.py | 203 | 98 | 51.72% |
| app/routes/auth.py | 40 | 6 | 85.00% |
| app/routes/main.py | 28 | 0 | 100.00% |
| app/routes/member.py | 33 | 2 | 93.94% |

## Test Categories

### 1. Model Tests (TestModels)
- ✅ User creation and password hashing
- ✅ Membership and credit management
- ✅ Shooting night attendance tracking
- ✅ Relationships between models

### 2. Authentication Tests (TestAuthentication)
- ✅ Login page rendering
- ✅ Successful user login
- ✅ User registration with membership creation
- ✅ Password validation

### 3. Admin Route Tests (TestAdminRoutes)
- ✅ Admin access control
- ✅ Dashboard accessibility
- ✅ Shooting night creation with credit deduction
- ✅ Member detail viewing
- ✅ Admin-only route protection

### 4. Member Route Tests (TestMemberRoutes)
- ✅ Member dashboard access
- ✅ Credit purchase functionality
- ✅ Member authentication requirements

### 5. Form Validation Tests (TestForms)
- ✅ Login form validation
- ✅ Registration form with duplicate email detection
- ✅ Shooting night form validation
- ✅ Form field requirements

### 6. Public Page Tests (TestPublicPages)
- ✅ Home page rendering
- ✅ About page
- ✅ News list and detail pages
- ✅ Events list and detail pages
- ✅ 404 error handling

## Test Fixtures

### Database Fixtures
- **app** - Test application with in-memory SQLite database
- **client** - HTTP test client
- **runner** - CLI test runner

### User Fixtures
- **admin_user** - Admin with 20 credits
- **regular_user** - Member with 15 credits
- **multiple_users** - 3 test users

### Content Fixtures
- **sample_news** - 3 news articles
- **sample_event** - Test event
- **sample_shooting_night** - Shooting night with attendance

## Test Utilities

Helper functions available in all tests:
- `login(client, email, password)` - Authenticate a user
- `logout(client)` - Log out current user

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_app.py

# Run specific test class
pytest tests/test_app.py::TestModels

# Run specific test
pytest tests/test_app.py::TestModels::test_user_creation

# Run tests matching keyword
pytest tests/ -k "admin"
```

### Coverage Commands

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Generate XML coverage for CI/CD
pytest tests/ --cov=app --cov-report=xml
```

### Using Test Runner Script

```bash
# Standard run
./run_tests.sh

# With coverage
./run_tests.sh coverage

# Fast mode (quiet)
./run_tests.sh fast

# Verbose mode
./run_tests.sh verbose

# Specific test
./run_tests.sh specific test_admin

# Help
./run_tests.sh help
```

## Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short --disable-warnings
```

### .coveragerc
```ini
[run]
source = app
omit = */venv/*, */tests/*, */migrations/*

[report]
precision = 2
show_missing = True
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test Template
```python
def test_feature_name(app, fixture):
    """Test description following AAA pattern."""
    # Arrange - Set up test data
    user = User(email='test@test.com', name='Test')
    
    # Act - Perform action
    db.session.add(user)
    db.session.commit()
    
    # Assert - Verify results
    assert user.id is not None
```

### Best Practices
1. ✅ One test per behavior
2. ✅ Use descriptive test names
3. ✅ Follow AAA pattern (Arrange, Act, Assert)
4. ✅ Keep tests isolated and independent
5. ✅ Use fixtures for common setup
6. ✅ Test edge cases and error conditions
7. ✅ Include docstrings
8. ✅ Avoid testing implementation details

## Continuous Improvement

### Coverage Goals
- Overall: 85%+ (current: 75.43%)
- Models: 95%+ (current: 93.55%)
- Routes: 80%+ (varies by module)
- Forms: 100% (achieved ✅)

### Areas for Improvement
1. Admin route coverage (currently 51.72%)
   - Add tests for edit/delete operations
   - Test error handling
   - Test pagination

2. Edge case testing
   - Invalid input handling
   - Permission edge cases
   - Database constraint violations

3. Integration tests
   - Multi-step workflows
   - Cross-module interactions

## Debugging Tests

### Common Issues

**DetachedInstanceError**
```python
# Solution: Refresh object
db.session.refresh(user)
```

**Test Isolation**
```python
# Ensure each test is independent
# Use fixtures for setup, don't rely on test order
```

**CSRF Errors**
```python
# CSRF is disabled in tests via TestConfig
# WTF_CSRF_ENABLED = False
```

## Dependencies

```txt
pytest==8.3.3           # Testing framework
pytest-cov==6.0.0       # Coverage plugin
pytest-flask==1.3.0     # Flask-specific utilities
```

## Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Test README](tests/README.md) - Detailed test documentation

## Test Maintenance

### Adding New Features
1. Write tests first (TDD)
2. Ensure tests fail initially
3. Implement feature
4. Verify tests pass
5. Check coverage doesn't decrease

### Updating Tests
- Update tests when routes change
- Add tests for new edge cases
- Refactor tests alongside code
- Keep fixtures up to date

### Review Checklist
- ✅ All tests pass
- ✅ Coverage >= 75%
- ✅ No skipped tests without reason
- ✅ Test names are descriptive
- ✅ Docstrings present
- ✅ No hardcoded values
- ✅ Fixtures used appropriately
