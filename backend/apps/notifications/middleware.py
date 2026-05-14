"""
Channels middleware that authenticates WebSocket connections using a JWT
passed as `?token=...` query string parameter.

Browsers cannot set custom headers on WebSocket handshakes, so we rely on the
URL query string to carry the access token. The token is validated using the
same simplejwt configuration as the REST API.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user(validated_token):
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

    User = get_user_model()
    try:
        user_id = validated_token.get("user_id")
        if not user_id:
            return AnonymousUser()
        return User.objects.get(pk=user_id)
    except (User.DoesNotExist, InvalidToken, TokenError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError

        query = parse_qs((scope.get("query_string") or b"").decode())
        token = (query.get("token") or [None])[0]

        if token:
            try:
                validated = AccessToken(token)
                scope["user"] = await _get_user(validated)
            except (TokenError, Exception):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
