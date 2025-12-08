import uuid

from flask import current_app
from sumup import APIError, Sumup
from sumup.checkouts import CreateCheckoutBody


class SumUpService:

    def __init__(self, api_key=None):
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
            current_app.logger.info(f'SumUp checkout created with ID: {response.id if hasattr(response, "id") else "no id"}')

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

    def get_checkout(self, checkout_id):
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

            current_app.logger.info(f"SumUp payment processed for checkout: {checkout_id}")

            # Check the response status
            status = getattr(response, "status", None)

            # Get transaction details
            transaction_code = getattr(response, "transaction_code", None)
            transaction_id = getattr(response, "transaction_id", None)

            # Return processed result with actual status
            return {
                "success": status == "PAID",
                "status": status,
                "checkout_id": checkout_id,
                "transaction_id": transaction_code or transaction_id,
                "transaction_code": transaction_code,
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
