from datetime import date

from flask import current_app
from flask_sqlalchemy.pagination import Pagination

from app.models import Membership, User
from app.repositories import MembershipRepository, RBACRepository, UserRepository
from app.services.result import ServiceResult
from app.services.settings_service import SettingsService


class UserService:
    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        """Get a user by ID."""
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def get_all_users_paginated(page: int = 1, per_page: int = 20, search: str = "", membership_filter: str = "all") -> Pagination:
        """Get all users ordered by name with pagination, search, and membership filter."""
        return UserRepository.get_all_paginated(page=page, per_page=per_page, search=search, membership_filter=membership_filter)

    @staticmethod
    def update_profile(user: User, name: str = None, phone: str = None) -> ServiceResult[None]:
        """Update user profile information."""
        if name:
            user.name = name
        if phone is not None:
            user.phone = phone

        try:
            UserRepository.save()
            return ServiceResult.ok(message="Profile updated successfully!")
        except Exception as e:
            current_app.logger.error(f"Error updating profile: {str(e)}")
            return ServiceResult.fail("An error occurred while updating profile.")

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> ServiceResult[None]:
        """Change user password after verifying current password."""
        if not user.check_password(current_password):
            return ServiceResult.fail("Current password is incorrect.")

        if len(new_password) < 8:
            return ServiceResult.fail("New password must be at least 8 characters long.")

        user.set_password(new_password)
        try:
            UserRepository.save()
            return ServiceResult.ok(message="Password changed successfully!")
        except Exception as e:
            current_app.logger.error(f"Error changing password: {str(e)}")
            return ServiceResult.fail("An error occurred while changing password.")

    @staticmethod
    def create_member(
        name: str,
        email: str,
        phone: str = None,
        password: str = "changeme123",
        role_ids: list[int] | None = None,
        create_membership: bool = False,
        qualification: str = "none",
    ) -> ServiceResult[User]:
        """Create a new member (admin function)."""
        if UserRepository.get_by_email(email):
            return ServiceResult.fail("Email already registered.")

        user = User(
            name=name,
            email=email,
            phone=phone,
            qualification=qualification,
            is_active=False,
        )
        user.set_password(password)

        try:
            UserRepository.add(user)
            UserRepository.flush()

            if role_ids:
                roles = RBACRepository.get_roles_by_ids(role_ids)
                user.roles = roles  # type: ignore[assignment]

            if create_membership:
                start_date = date.today()
                membership = Membership(
                    user_id=user.id,
                    start_date=start_date,
                    expiry_date=SettingsService.calculate_membership_expiry(start_date).date(),
                    initial_credits=20,
                    purchased_credits=0,
                    status="active",
                )
                MembershipRepository.add(membership)

            UserRepository.save()
            return ServiceResult.ok(data=user)
        except Exception as e:
            current_app.logger.error(f"Error creating member: {str(e)}")
            return ServiceResult.fail("An error occurred while creating member.")

    @staticmethod
    def update_member(
        user: User,
        name: str,
        email: str,
        phone: str = None,
        qualification: str = None,
        qualification_detail: str = None,
        role_ids: list[int] | None = None,
        is_active: bool = True,
        password: str = None,
        membership_start_date: date = None,
        membership_expiry_date: date = None,
        membership_initial_credits: int = None,
        membership_purchased_credits: int = None,
    ) -> ServiceResult[None]:
        """Update an existing member (admin function)."""
        user.name = name
        user.email = email
        user.phone = phone
        if qualification:
            user.qualification = qualification
        user.qualification_detail = None if qualification == "none" else (qualification_detail or None)
        if role_ids is not None:
            roles = RBACRepository.get_roles_by_ids(role_ids)
            user.roles = roles  # type: ignore[assignment]
        user.is_active = is_active

        if password:
            user.set_password(password)

        if user.membership:
            if membership_start_date:
                user.membership.start_date = membership_start_date  # type: ignore[attr-defined]
            if membership_expiry_date:
                user.membership.expiry_date = membership_expiry_date  # type: ignore[attr-defined]
            if membership_initial_credits is not None:
                user.membership.initial_credits = membership_initial_credits  # type: ignore[attr-defined]
            if membership_purchased_credits is not None:
                user.membership.purchased_credits = membership_purchased_credits  # type: ignore[attr-defined]

        try:
            UserRepository.save()
            return ServiceResult.ok(message=f"Member {user.name} updated successfully!")
        except Exception as e:
            current_app.logger.error(f"Error updating member: {str(e)}")
            return ServiceResult.fail("An error occurred while updating member.")

    @staticmethod
    def create_user(
        name: str,
        email: str,
        password: str,
        phone: str = None,
        qualification: str = "None",
        qualification_detail: str = None,
    ) -> ServiceResult[User]:
        if UserRepository.get_by_email(email):
            return ServiceResult.fail("Email already registered.")

        user = User(
            name=name,
            email=email,
            phone=phone,
            qualification=qualification,
            qualification_detail=None if qualification in (None, "none", "None") else (qualification_detail or None),
            is_active=False,
        )
        user.set_password(password)

        try:
            UserRepository.add(user)
            UserRepository.save()
            return ServiceResult.ok(data=user)
        except Exception as e:
            current_app.logger.error(f"Error creating user: {str(e)}")
            return ServiceResult.fail("An error occurred during registration.")

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        user = UserRepository.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def create_password_reset_token(user: User) -> str:
        return user.generate_reset_token()  # type: ignore[no-any-return]

    @staticmethod
    def reset_password(token: str, new_password: str) -> ServiceResult[None]:
        user = User.verify_reset_token(token, max_age=86400)

        if not user:
            return ServiceResult.fail("Invalid or expired reset link.")

        user.set_password(new_password)
        UserRepository.save()

        return ServiceResult.ok(message="Password reset successfully.")
