"""SumUp payment service using official SumUp Python SDK"""

from flask import current_app
from sumup import Sumup, APIError
from sumup.checkouts import CreateCheckoutBody
import uuid


class SumUpService:
    """SumUp payment API service using official SDK"""

    def __init__(self, api_key=None):
        """Initialize SumUp client with API key"""
        self.api_key = api_key or current_app.config.get("SUMUP_API_KEY")
        self.client = Sumup(api_key=self.api_key)

    def create_checkout(
        self,
        amount,
        currency="EUR",
        description="",
        checkout_reference="",
        merchant_code=None,
    ):
        """
        Create a checkout session using SumUp SDK

        Args:
            amount: Amount in decimal (e.g., 100.00 for €100)
            currency: Currency code (default: EUR)
            description: Payment description
            checkout_reference: Unique reference for this checkout (auto-generated if not provided)
            merchant_code: SumUp merchant code (optional, from config if not provided)

        Returns:
            dict: Checkout response with checkout_id or None on error
        """
        try:
            # Get merchant code from config if not provided
            if not merchant_code:
                merchant_code = current_app.config.get("SUMUP_MERCHANT_CODE")

            # Merchant code is required by SumUp SDK
            if not merchant_code:
                current_app.logger.error("SUMUP_MERCHANT_CODE not configured")
                raise ValueError(
                    "SUMUP_MERCHANT_CODE must be set in environment variables"
                )

            # Generate checkout reference if not provided
            if not checkout_reference:
                checkout_reference = str(uuid.uuid4())

            # Create checkout body
            checkout_body = CreateCheckoutBody(
                amount=float(amount),
                currency=currency,
                checkout_reference=checkout_reference,
                merchant_code=merchant_code,
                description=description,
            )

            # Create checkout using SDK
            response = self.client.checkouts.create(body=checkout_body)

            # Log the response for debugging
            current_app.logger.info(
                f'SumUp checkout created with ID: {response.id if hasattr(response, "id") else "no id"}'
            )

            # The SDK returns a Checkout object
            if response and hasattr(response, "id"):
                checkout_id = response.id

                return {
                    "id": checkout_id,
                    "checkout_reference": (
                        response.checkout_reference
                        if hasattr(response, "checkout_reference")
                        else checkout_reference
                    ),
                    "status": (
                        response.status if hasattr(response, "status") else "PENDING"
                    ),
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

    def get_checkout(self, checkout_id):
        """
        Get checkout details by ID

        Args:
            checkout_id: The checkout ID

        Returns:
            Checkout object or None
        """
        try:
            checkout = self.client.checkouts.get(checkout_id=checkout_id)
            return checkout
        except APIError as e:
            current_app.logger.error(f"SumUp API error getting checkout: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting SumUp checkout: {str(e)}")
            return None

    def verify_payment(self, checkout_id):
        """
        Verify if payment was successful

        Args:
            checkout_id: The checkout ID to verify

        Returns:
            bool: True if payment successful, False otherwise
        """
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

    def process_checkout_payment(
        self,
        checkout_id,
        card_number,
        card_name,
        expiry_month,
        expiry_year,
        cvv,
        payment_type="card",
    ):
        """
        Process a checkout payment with card details

        Args:
            checkout_id: The checkout ID to process
            card_number: Full card number
            card_name: Cardholder name
            expiry_month: Expiry month (01-12)
            expiry_year: Expiry year (YYYY or YY)
            cvv: Card CVV/CVC
            payment_type: Payment type (default: 'card')

        Returns:
            dict: Payment result or None on error
        """
        try:
            from sumup.checkouts import ProcessCheckoutBody
            from sumup.checkouts.types import Card

            # Ensure expiry_year is 4 digits
            if len(expiry_year) == 2:
                expiry_year = "20" + expiry_year

            # Ensure expiry_month is 2 digits with leading zero
            if len(expiry_month) == 1:
                expiry_month = "0" + expiry_month

            # Get last 4 digits
            last_4 = card_number[-4:]

            # Create card object
            card = Card(
                number=card_number,
                name=card_name,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                cvv=cvv,
                last_4_digits=last_4,
                type="UNKNOWN",  # SumUp will detect card type
            )

            # Create process body
            process_body = ProcessCheckoutBody(payment_type=payment_type, card=card)

            # Process the checkout
            response = self.client.checkouts.process(id=checkout_id, body=process_body)

            current_app.logger.info(
                f"SumUp payment processed for checkout: {checkout_id}"
            )

            # Check the response status
            status = getattr(response, "status", None)

            # Return processed result with actual status
            return {
                "success": status == "PAID",
                "status": status,
                "checkout_id": checkout_id,
                "transaction_id": getattr(response, "transaction_id", None),
                "response": response,
            }

        except APIError as e:
            current_app.logger.error(f"SumUp API error processing payment: {str(e)}")
            # Extract more detailed error info if available
            error_message = str(e)
            if hasattr(e, "body"):
                error_message = str(e.body)
            return {"success": False, "status": "FAILED", "error": error_message}
        except Exception as e:
            current_app.logger.error(f"Error processing SumUp payment: {str(e)}")
            return {"success": False, "status": "FAILED", "error": str(e)}
