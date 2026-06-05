import logging
import uuid
from typing import Any

from sumup import APIError, Sumup
from sumup.checkouts import CreateCheckoutBody

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SumUpService:
    def __init__(self, api_key: str | None = None, merchant_code: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.sumup_api_key
        self.merchant_code = merchant_code or settings.sumup_merchant_code
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
            merchant_code = merchant_code or self.merchant_code
            if not merchant_code:
                logger.error("SUMUP_MERCHANT_CODE not configured")
                raise ValueError("SUMUP_MERCHANT_CODE must be set in environment variables")

            if not checkout_reference:
                checkout_reference = str(uuid.uuid4())

            checkout_body = CreateCheckoutBody(
                amount=float(amount / 100.0),
                currency=currency,
                checkout_reference=checkout_reference,
                merchant_code=merchant_code,
                description=description,
            )
            response = self.client.checkouts.create(body=checkout_body)
            if response and hasattr(response, "id"):
                return {
                    "id": response.id,
                    "checkout_reference": getattr(response, "checkout_reference", checkout_reference),
                    "status": getattr(response, "status", "PENDING"),
                }
            logger.error("SumUp checkout response missing id")
            return None
        except APIError as exc:
            logger.error("SumUp API error creating checkout: %s", exc)
            return None
        except ValueError as exc:
            logger.error("Configuration error: %s", exc)
            return None
        except Exception as exc:
            logger.error("Error creating SumUp checkout: %s", exc)
            return None

    def get_checkout(self, checkout_id: str) -> Any | None:
        try:
            return self.client.checkouts.get(id=checkout_id)
        except APIError as exc:
            logger.error("SumUp API error getting checkout: %s", exc)
            return None
        except Exception as exc:
            logger.error("Error getting SumUp checkout: %s", exc)
            return None

    def verify_payment(self, checkout_id: str) -> bool:
        try:
            checkout = self.get_checkout(checkout_id)
            if not checkout:
                return False
            status = checkout.status if hasattr(checkout, "status") else None
            return status == "PAID"
        except Exception as exc:
            logger.error("Error verifying SumUp payment: %s", exc)
            return False
