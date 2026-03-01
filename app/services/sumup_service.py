import uuid
from typing import Any

from flask import current_app
from sumup import APIError, Sumup
from sumup.checkouts import CreateCheckoutBody


class SumUpService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or current_app.config.get("SUMUP_API_KEY")
        self.client = Sumup(api_key=self.api_key)

    def create_checkout(
        self,
        amount: int,
        currency: str = "EUR",
        description: str = "",
        checkout_reference: str = "",
        merchant_code: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            # Get merchant code from config if not provided
            if not merchant_code:
                merchant_code = current_app.config.get("SUMUP_MERCHANT_CODE")

            # Merchant code is required by SumUp SDK
            if not merchant_code:
                current_app.logger.error("SUMUP_MERCHANT_CODE not configured")
                raise ValueError("SUMUP_MERCHANT_CODE must be set in environment variables")

            # Generate checkout reference if not provided
            if not checkout_reference:
                checkout_reference = str(uuid.uuid4())

            # Convert cents to euros for SumUp API
            amount_euros = amount / 100.0

            # Create checkout body
            checkout_body = CreateCheckoutBody(
                amount=float(amount_euros),
                currency=currency,
                checkout_reference=checkout_reference,
                merchant_code=merchant_code,
                description=description,
            )

            # Create checkout using SDK
            response = self.client.checkouts.create(body=checkout_body)

            # Log the response for debugging
            current_app.logger.info(f"SumUp checkout created with ID: {response.id if hasattr(response, 'id') else 'no id'}")

            # The SDK returns a Checkout object
            if response and hasattr(response, "id"):
                checkout_id = response.id

                return {
                    "id": checkout_id,
                    "checkout_reference": (response.checkout_reference if hasattr(response, "checkout_reference") else checkout_reference),
                    "status": (response.status if hasattr(response, "status") else "PENDING"),
                }

            current_app.logger.error("SumUp checkout response missing id")
            return None

        except APIError as e:
            current_app.logger.error(f"SumUp API error creating checkout: {str(e)}")
            return None
        except ValueError as e:
            current_app.logger.error(f"Configuration error: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error creating SumUp checkout: {str(e)}")
            return None

    def get_checkout(self, checkout_id: str) -> Any | None:
        try:
            checkout = self.client.checkouts.get(checkout_id=checkout_id)
            return checkout
        except APIError as e:
            current_app.logger.error(f"SumUp API error getting checkout: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting SumUp checkout: {str(e)}")
            return None

    def verify_payment(self, checkout_id: str) -> bool:
        try:
            checkout = self.get_checkout(checkout_id)

            if not checkout:
                return False

            # Check if checkout status is PAID
            status = checkout.status if hasattr(checkout, "status") else None
            return status == "PAID"

        except Exception as e:
            current_app.logger.error(f"Error verifying SumUp payment: {str(e)}")
            return False
