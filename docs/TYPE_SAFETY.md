# Type Safety Guide

This project uses **Pydantic** for runtime validation and **mypy** for static type checking.

## Quick Start

### Run Type Checking
```bash
make typecheck
```

### Validate Requests
```python
from app.schemas import LoginSchema
from app.utils.pydantic_helpers import validate_request

validated, errors = validate_request(LoginSchema, request)
if errors:
    # Handle errors
    pass
```

## Features

✅ Runtime validation with Pydantic  
✅ Static type checking with mypy  
✅ Type-safe schemas for all forms  
✅ Generic service responses  
✅ Full IDE autocomplete support  

## Available Schemas

- **Auth**: LoginSchema, SignupSchema, ResetPasswordSchema
- **Member**: ProfileSchema, ChangePasswordSchema  
- **Admin**: ShootSchema, NewsSchema, EventSchema

See `app/schemas/` for complete list.
