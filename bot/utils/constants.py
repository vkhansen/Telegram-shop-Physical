"""
Application-wide constants to replace magic strings.
"""

# Payment methods
PAYMENT_BITCOIN = "bitcoin"
PAYMENT_CASH = "cash"
PAYMENT_PROMPTPAY = "promptpay"

# Delivery types (Card 3)
DELIVERY_DOOR = "door"
DELIVERY_DEAD_DROP = "dead_drop"
DELIVERY_PICKUP = "pickup"

# Order status → emoji mapping (shared across admin & user views)
STATUS_EMOJI = {
    "pending": "\u23f3",
    "reserved": "\U0001f512",
    "confirmed": "\u2705",
    "preparing": "\U0001f373",
    "ready": "\U0001f4e6",
    "out_for_delivery": "\U0001f697",
    "delivered": "\u2705",
    "cancelled": "\u274c",
    "canceled": "\u274c",
    "expired": "\u23f0",
}
