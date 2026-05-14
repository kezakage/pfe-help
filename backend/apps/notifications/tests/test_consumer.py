"""
Tests for the WebSocket NotificationsConsumer.

Uses an in-memory channel layer override so the tests don't depend on Redis,
and the JWTAuthMiddleware in production code path so we exercise the full
URL → middleware → consumer chain just like a real browser.
"""
import pytest
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.middleware import JWTAuthMiddlewareStack
from apps.notifications.routing import websocket_urlpatterns
from apps.notifications.utils import push

# Use the in-memory layer for tests — independent of Redis.
TEST_CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


def _build_application():
    """Same wrapping as patrimoinehub.asgi for the WS protocol."""
    return JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))


def _jwt_for(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_ws_connect_with_valid_token_accepted(expert_user):
    token = await _async_token(expert_user)
    comm = WebsocketCommunicator(_build_application(), f"/ws/notifications/?token={token}")
    connected, _ = await comm.connect()
    assert connected is True
    # Consumer greets the client with a "ready" frame on accept.
    hello = await comm.receive_json_from()
    assert hello == {"type": "ready"}
    await comm.disconnect()


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_ws_connect_without_token_rejected():
    comm = WebsocketCommunicator(_build_application(), "/ws/notifications/")
    connected, code = await comm.connect()
    assert connected is False
    # 4401 = our custom "not authenticated" close code in NotificationsConsumer.
    assert code == 4401


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_ws_connect_with_garbage_token_rejected():
    comm = WebsocketCommunicator(
        _build_application(), "/ws/notifications/?token=not-a-real-jwt",
    )
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4401


@override_settings(CHANNEL_LAYERS=TEST_CHANNEL_LAYERS)
async def test_ws_receives_pushed_notification(expert_user):
    """push() → group_send → consumer.notify() → client receives JSON frame."""
    token = await _async_token(expert_user)
    comm = WebsocketCommunicator(_build_application(), f"/ws/notifications/?token={token}")
    connected, _ = await comm.connect()
    assert connected is True
    await comm.receive_json_from()  # drain the "ready" hello

    # Push from "the server side" — must reach this user's group.
    await _async_push(expert_user)

    frame = await comm.receive_json_from(timeout=2)
    assert frame["type"] == "notification"
    assert frame["data"]["title"] == "Hello"
    assert frame["data"]["type"] == "system"

    await comm.disconnect()


# ---------------------------------------------------------------------------
# Sync→async helpers so we don't hit the SynchronousOnlyOperation guard
# ---------------------------------------------------------------------------
from channels.db import database_sync_to_async  # noqa: E402


@database_sync_to_async
def _async_token(user) -> str:
    return _jwt_for(user)


@database_sync_to_async
def _async_push(user):
    from apps.notifications.models import Notification
    push(
        user,
        type=Notification.Type.SYSTEM,
        title="Hello",
        body="from the server",
    )
