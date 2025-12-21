from datetime import date
from typing import Any, Dict, Optional, Tuple


class SignupValidation:

    @staticmethod
    def validate_and_extract(
        form_data: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        name = form_data.get("name")
        email = form_data.get("email")
        phone = form_data.get("phone")
        password = form_data.get("password")
        password_confirm = form_data.get("password_confirm")
        qualification = form_data.get("qualification", "None")

        if not all([name, email, password, qualification]):
            return None, "All required fields must be filled."

        if password != password_confirm:
            return None, "Passwords do not match."

        validated_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "qualification": qualification,
        }

        return validated_data, None
