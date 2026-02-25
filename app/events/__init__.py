"""Domain events for the application.

Signals are used to decouple business logic from side effects (e.g., sending
emails) so that services emit events and handlers react without direct imports.
"""

from blinker import signal

# --- User lifecycle ---
user_registered = signal("user-registered")
"""Sent when a new user signs up. kwargs: user_id (int)"""

user_activated = signal("user-activated")
"""Sent when an admin activates a user account. kwargs: user_id (int)"""

# --- Payment lifecycle ---
payment_completed = signal("payment-completed")
"""Sent when a payment is completed. kwargs: user_id, payment_id, payment_type"""

credit_purchased = signal("credit-purchased")
"""Sent when credits are purchased. kwargs: user_id, payment_id, quantity"""

cash_payment_submitted = signal("cash-payment-submitted")
"""Sent when a cash payment request is submitted. kwargs: user_id, payment_id"""

# --- Auth ---
password_reset_requested = signal("password-reset-requested")
"""Sent when a password reset is requested. kwargs: user_id, token"""

# --- Membership ---
membership_activated = signal("membership-activated")
"""Sent when a membership is activated by admin. kwargs: user_id, payment_id (optional)"""
