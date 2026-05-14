from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

api_v1 = [
    path("auth/", include("apps.accounts.urls")),
    path("heritage/", include("apps.heritage.urls")),
    path("pages/", include("apps.pages.urls")),
    path("media/", include("apps.media.urls")),
    path("discussions/", include("apps.discussions.urls")),
    path("exports/", include("apps.exports.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("chat/", include("apps.chatbot.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Prometheus metrics — scraped by the prometheus container on the docker network.
    # Exposed publicly because the dev cluster is firewalled; in production this
    # should be limited via reverse-proxy ACL or moved to a separate port.
    path("", include("django_prometheus.urls")),
]

if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
