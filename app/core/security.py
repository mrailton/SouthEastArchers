import os
from typing import cast

from passlib.context import CryptContext

# Low bcrypt cost in tests — full rounds add ~400ms per hash and dominate suite runtime.
if os.environ.get("APP_ENV") == "testing":
    pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4, deprecated="auto")
else:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    return cast(bool, pwd_context.verify(plain, hashed))
