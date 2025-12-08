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
        dob_str = form_data.get("date_of_birth")
        password = form_data.get("password")
        password_confirm = form_data.get("password_confirm")
        payment_method = form_data.get("payment_method", "online")

        if not all([name, email, dob_str, password, payment_method]):
            return None, "All required fields must be filled."

        if password != password_confirm:
            return None, "Passwords do not match."

        try:
            dob = date.fromisoformat(dob_str)
        except (ValueError, TypeError):
            return None, "Invalid date of birth."

        validated_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "dob": dob,
            "password": password,
            "payment_method": payment_method,
        }

        return validated_data, None
