from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DiscussionViewSet, MessageViewSet

router = DefaultRouter()
router.register("messages", MessageViewSet, basename="message")
router.register("", DiscussionViewSet, basename="discussion")

urlpatterns = [path("", include(router.urls))]
