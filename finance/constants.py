"""Centralized non-secret constants for finance domain and UX behavior."""

CURRENCY_CODES = ("GBP", "USD", "CNY", "EUR")

PROFILE_TIMEZONE_CHOICES = (
    "UTC",
    "Europe/London",
    "Asia/Shanghai",
    "America/Los_Angeles",
)

STARTER_EXPENSE_CATEGORIES = (
    "Food",
    "Transport",
    "Housing",
    "Shopping",
    "Entertainment",
)

OTP_RATE_LIMIT_SECONDS = 60
OTP_REGISTER_TTL_SECONDS = 600
OTP_ACCOUNT_ACTION_TTL_SECONDS = 300

TURNSTILE_VERIFY_TIMEOUT_SECONDS = 5
AI_CHAT_TIMEOUT_SECONDS = 20

ASSISTANT_NAME = "Nori"
ASSISTANT_NOTE_PREFIX_CHAT = "Added by Nori (chat): "
ASSISTANT_NOTE_PREFIX_AGENT = "Added by Nori (assistant): "
TRANSACTION_PAGE_SIZE = 12
