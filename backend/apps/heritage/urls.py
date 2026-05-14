from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HeritageResourceViewSet, ProjectViewSet

router = DefaultRouter()
router.register("resources", HeritageResourceViewSet, basename="resource")
router.register("projects", ProjectViewSet, basename="project")

urlpatterns = [path("", include(router.urls))]
