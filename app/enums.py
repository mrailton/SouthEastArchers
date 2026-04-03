from enum import StrEnum


class PaymentType(StrEnum):
    MEMBERSHIP = "membership"
    CREDITS = "credits"


class PaymentMethod(StrEnum):
    CASH = "cash"
    ONLINE = "online"
