from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnnotationViewSet, MediaViewSet

router = DefaultRouter()
router.register("annotations", AnnotationViewSet, basename="annotation")
router.register("", MediaViewSet, basename="media")

urlpatterns = [path("", include(router.urls))]
