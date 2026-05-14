from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AskView, ChatSessionViewSet

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = [
    path("ask/", AskView.as_view(), name="chat-ask"),
    path("", include(router.urls)),
]
