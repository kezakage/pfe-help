"""
Per-scope throttle classes for the chatbot endpoints.

Rates are configured under DEFAULT_THROTTLE_RATES in settings:
  - chat_anon: anonymous public widget visitors (Explorer)
  - chat_user: authenticated users (full /app/chatbot page)
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ChatAnonRateThrottle(AnonRateThrottle):
    scope = "chat_anon"


class ChatUserRateThrottle(UserRateThrottle):
    scope = "chat_user"
