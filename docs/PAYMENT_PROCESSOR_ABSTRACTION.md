# Payment Processor Abstraction Layer

## Overview

The application now uses a flexible payment processor abstraction layer that makes it easy to switch between or add multiple payment processors (like SumUp, Stripe, PayPal, etc.).

## Architecture

### Core Components

1. **PaymentProcessor (Base Class)** - `/app/services/payment_processors/base.py`
   - Abstract base class defining the interface all payment processors must implement
   - Provides `PaymentResult` class for standardized payment responses
   
2. **SumUpProcessor** - `/app/services/payment_processors/sumup.py`
   - Implementation of the PaymentProcessor interface for SumUp
   - Wraps the SumUp SDK with our standardized interface

3. **PaymentGateway** - `/app/services/payment_gateway.py`
   - Main service that manages payment processors
   - Provides a unified interface for creating and processing payments
   - Automatically selects the configured processor

4. **Payment Model** - `/app/models/payment.py`
   - Stores payment processor name in `payment_processor` field
   - Stores external transaction ID in `external_transaction_id` field
   - Amounts stored in cents (integers) to avoid floating-point issues

## Usage

### Configuration

Set the payment processor in your environment or config:

```python
PAYMENT_PROCESSOR=sumup  # or 'stripe', 'paypal', etc.
```

### In Routes

```python
from app.services import PaymentGateway

# Create a checkout
gateway = PaymentGateway()
checkout = gateway.create_checkout(
    amount_cents=10000,  # €100.00 in cents
    currency="EUR",
    description="Annual Membership",
    reference="membership_123_456"
)

# Process a payment
result = gateway.process_checkout(
    checkout_id=checkout['id'],
    card_number="...",
    card_name="...",
    expiry_month="12",
    expiry_year="2025",
    cvv="123"
)

if result.success:
    # Payment successful
    transaction_id = result.transaction_id
    transaction_code = result.transaction_code
    processor_name = gateway.name  # 'sumup'
```

### Payment Result Object

```python
class PaymentResult:
    success: bool              # True if payment succeeded
    checkout_id: str          # The checkout ID
    transaction_id: str       # External transaction ID
    transaction_code: str     # Searchable transaction code
    status: str               # PAID, FAILED, PENDING, etc.
    error: str | None         # Error message if failed
```

## Adding a New Payment Processor

To add support for Stripe, PayPal, or another processor:

1. **Create the processor class**

```python
# app/services/payment_processors/stripe.py

from .base import PaymentProcessor, PaymentResult

class StripeProcessor(PaymentProcessor):
    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get("STRIPE_API_KEY")
        import stripe
        stripe.api_key = self.api_key
    
    @property
    def name(self) -> str:
        return "stripe"
    
    def create_checkout(self, amount_cents, currency, description, reference, **kwargs):
        # Implement Stripe checkout creation
        pass
    
    def get_checkout_status(self, checkout_id):
        # Implement Stripe status check
        pass
    
    def process_checkout(self, checkout_id, **kwargs):
        # Implement Stripe payment processing
        pass
```

2. **Register the processor**

```python
# app/services/payment_processors/__init__.py

from .base import PaymentProcessor
from .sumup import SumUpProcessor
from .stripe import StripeProcessor

__all__ = ["PaymentProcessor", "SumUpProcessor", "StripeProcessor"]
```

3. **Add to gateway**

```python
# app/services/payment_gateway.py

class PaymentGateway:
    PROCESSORS = {
        "sumup": SumUpProcessor,
        "stripe": StripeProcessor,
    }
```

4. **Update configuration**

```python
# config/config.py

PAYMENT_PROCESSOR = os.environ.get("PAYMENT_PROCESSOR", "sumup")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
```

That's it! The rest of the application will automatically use the new processor.

## Legacy Code

The old `SumUpService` class in `/app/services/sumup_service.py` is deprecated but kept for backwards compatibility. It will show deprecation warnings when used.

New code should use `PaymentGateway` instead.

## Benefits

1. **Easy to switch processors** - Change one config value
2. **Support multiple processors** - Can use different processors for different use cases
3. **Testable** - Easy to mock the gateway for testing
4. **Consistent interface** - All processors work the same way
5. **Type safety** - PaymentResult provides consistent structure
6. **Future-proof** - Add new processors without changing existing code

## Testing

When writing tests, mock the `PaymentGateway` class:

```python
from unittest.mock import Mock, patch

def test_payment():
    with patch("app.routes.payment.PaymentGateway") as mock_gateway_class:
        mock_gateway = Mock()
        mock_gateway.name = "sumup"
        mock_gateway.process_checkout.return_value = PaymentResult(
            success=True,
            checkout_id="123",
            transaction_id="txn_456",
            transaction_code="CODE123",
            status="PAID"
        )
        mock_gateway_class.return_value = mock_gateway
        
        # Run your test
```

## Migration Notes

### Amount Storage

All payment amounts are now stored in cents (integers) to avoid floating-point precision issues:

- €100.00 is stored as 10000
- €4.50 is stored as 450

The Payment model has helper properties to convert between euros and cents:

```python
payment.amount_cents = 10000
print(payment.amount)  # 100.0

payment.amount = 50.0
print(payment.amount_cents)  # 5000
```

### Database Fields

- `payment_processor` - Stores processor name ("sumup", "stripe", etc.)
- `external_transaction_id` - Stores the transaction ID from the processor
- `amount_cents` - Stores amount in cents (integer)
