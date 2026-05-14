from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PageVersionViewSet, PageViewSet

router = DefaultRouter()
router.register("versions", PageVersionViewSet, basename="page-version")
router.register("", PageViewSet, basename="page")

urlpatterns = [path("", include(router.urls))]
