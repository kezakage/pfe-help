from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .social_views import GitHubLoginView, GoogleLoginView, SocialProvidersStatusView
from .views import (
    AdminStatsView,
    DisciplineViewSet,
    LoginView,
    MeViewSet,
    RefreshView,
    RegisterView,
    UserAdminViewSet,
)

router = DefaultRouter()
router.register("disciplines", DisciplineViewSet, basename="discipline")
router.register("admin/users", UserAdminViewSet, basename="admin-users")
router.register("register", RegisterView, basename="register")
router.register("me", MeViewSet, basename="me")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),

    # OAuth2 / SSO
    path("social/providers/", SocialProvidersStatusView.as_view(), name="social-providers"),
    path("social/google/", GoogleLoginView.as_view(), name="social-google"),
    path("social/github/", GitHubLoginView.as_view(), name="social-github"),

    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("", include(router.urls)),
]
