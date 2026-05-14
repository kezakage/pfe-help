"""
Django settings for PatrimoineHub.
"""
from datetime import timedelta
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: list[str] | None = None) -> list[str]:
    val = os.environ.get(key)
    if not val:
        return default or []
    return [x.strip() for x in val.split(",") if x.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["*"])

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",

    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "channels",
    "drf_spectacular",
    "guardian",
    "storages",
    "django_elasticsearch_dsl",
    "django_prometheus",

    # Social auth (OAuth2 / SSO)
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "dj_rest_auth",
    "dj_rest_auth.registration",

    # Local
    "apps.accounts",
    "apps.heritage",
    "apps.pages",
    "apps.media",
    "apps.discussions",
    "apps.exports",
    "apps.notifications",
    "apps.chatbot",
]

MIDDLEWARE = [
    # django-prometheus must wrap all other middleware to time the full request
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must come right after SecurityMiddleware so it can serve
    # /static/ files in production without an extra nginx in front of Daphne.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware must come AFTER SessionMiddleware (it can read the
    # session-stored language) and BEFORE CommonMiddleware (which uses the
    # active language to format URLs and error responses).
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Required by django-allauth >= 0.56 — manages the per-request auth state.
    "allauth.account.middleware.AccountMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "patrimoinehub.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "patrimoinehub.wsgi.application"
ASGI_APPLICATION = "patrimoinehub.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL + PostGIS
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        # django-prometheus wraps the PostGIS backend to expose query/connection metrics
        "ENGINE": "django_prometheus.db.backends.postgis",
        "NAME": env("POSTGRES_DB", "patrimoinehub"),
        "USER": env("POSTGRES_USER", "patrimoine"),
        "PASSWORD": env("POSTGRES_PASSWORD", "patrimoine"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
    # Required for django-allauth's social-account flow.
    "allauth.account.auth_backends.AuthenticationBackend",
)

# ---------------------------------------------------------------------------
# Social auth (OAuth2 / SSO) — django-allauth + dj-rest-auth
# ---------------------------------------------------------------------------
SITE_ID = 1

# Allauth — keep things minimal: no signup forms (we use REST), email-based,
# trust the provider's verified email so we skip our own confirmation flow.
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
# Our custom User model has no `username` field — tell allauth/dj-rest-auth
# to use email as the identifier and skip username-related serializer fields.
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_ADAPTER = "apps.accounts.allauth_adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "apps.accounts.allauth_adapters.SocialAccountAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "github": {
        "APP": {
            "client_id": env("GITHUB_OAUTH_CLIENT_ID", ""),
            "secret": env("GITHUB_OAUTH_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["read:user", "user:email"],
    },
}

# Where the provider sends the browser back after consent. The frontend
# handles that route, extracts ?code=, and POSTs it to the matching social
# login endpoint (which mints our SimpleJWT pair).
SOCIAL_REDIRECT_FRONTEND = env("SOCIAL_REDIRECT_FRONTEND", "http://localhost:5173")

# dj-rest-auth — return SimpleJWT tokens (not Django sessions) on social login.
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_HTTPONLY": False,
    "JWT_AUTH_RETURN_EXPIRATION": True,
    "TOKEN_MODEL": None,  # we don't use DRF's auth-token, only JWT
    "SESSION_LOGIN": False,
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/hour",
        "user": "1200/hour",
        "chat_anon": "10/hour",
        "chat_user": "60/hour",
    },
}

# ---------------------------------------------------------------------------
# Elasticsearch
# ---------------------------------------------------------------------------
ELASTICSEARCH_URL = env("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ELASTICSEARCH_DSL = {
    "default": {"hosts": ELASTICSEARCH_URL, "timeout": 20},
}
# Index real-time on save/delete signals (django-elasticsearch-dsl)
ELASTICSEARCH_DSL_AUTOSYNC = env_bool("ELASTICSEARCH_DSL_AUTOSYNC", True)
ELASTICSEARCH_DSL_AUTO_REFRESH = env_bool("ELASTICSEARCH_DSL_AUTO_REFRESH", True)

# ---------------------------------------------------------------------------
# Chatbot RAG
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-haiku-4-5")
EMBEDDING_MODEL_NAME = env(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
)
CHATBOT_TOP_K = int(env("CHATBOT_TOP_K", "5"))
CHATBOT_MAX_CONTEXT_CHARS = int(env("CHATBOT_MAX_CONTEXT_CHARS", "6000"))

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_LIFETIME_MIN", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_LIFETIME_DAYS", "14"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PatrimoineHub API",
    "DESCRIPTION": "Collaborative platform for Algerian architectural heritage",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    ["http://localhost:5173", "http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", "redis://localhost:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Algiers"

# ---------------------------------------------------------------------------
# Storage — MinIO / S3
# ---------------------------------------------------------------------------
USE_S3 = env_bool("USE_S3", False)

if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "patrimoinehub-media")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_ADDRESSING_STYLE = env("AWS_S3_ADDRESSING_STYLE", "path")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    # Public-facing host for generated URLs (browsers can't resolve the
    # internal Docker DNS name "minio"). When set, django-storages emits
    # plain URLs against this domain instead of presigned ones — relies on
    # the bucket being publicly readable (set via `mc anonymous`).
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_S3_URL_PROTOCOL = env("AWS_S3_URL_PROTOCOL", "https:")
    AWS_QUERYSTRING_AUTH = env_bool("AWS_QUERYSTRING_AUTH", not bool(AWS_S3_CUSTOM_DOMAIN))
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# Upload limits
MAX_IMAGE_SIZE = int(env("MAX_IMAGE_SIZE", str(50 * 1024 * 1024)))   # 50 MB
MAX_VIDEO_SIZE = int(env("MAX_VIDEO_SIZE", str(500 * 1024 * 1024)))  # 500 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_VIDEO_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_VIDEO_SIZE

# ---------------------------------------------------------------------------
# I18N / TZ
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Algiers"
USE_I18N = True
USE_TZ = True
LANGUAGES = [("fr", "Français"), ("ar", "العربية")]
# Where Django looks for compiled translations. Each app may also ship its
# own `locale/` directory; this central path covers project-wide strings.
LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: compressed + hashed static files in production. The S3 storage
# branch above only overrides "default" (media) — staticfiles stays local so
# Django and WhiteNoise can serve /static/ without round-tripping to S3.
if not DEBUG:
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Production hardening — only applied when DJANGO_DEBUG=0
# ---------------------------------------------------------------------------
# Fail loudly if someone deploys with DEBUG=0 but forgot to override the
# placeholder secret. Better to crash on boot than ship a known-public key.
if not DEBUG and SECRET_KEY == "insecure-dev-key-change-me":
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a real value when DJANGO_DEBUG=0. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(50))\""
    )

# Likewise, refuse to start in prod with the wildcard host that's convenient
# for dev but unsafe behind a reverse proxy.
if not DEBUG and (not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS):
    raise RuntimeError(
        "DJANGO_ALLOWED_HOSTS must list explicit hostnames when DJANGO_DEBUG=0 "
        "(no wildcard)."
    )

if not DEBUG:
    # Trust the X-Forwarded-Proto header set by the reverse proxy (nginx)
    # so request.is_secure() returns True for HTTPS-terminated traffic.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS — 1 year, includeSubDomains, preload-ready. Tunable via env so
    # operators can dial it back during the initial HTTPS rollout.
    SECURE_HSTS_SECONDS = int(env("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", True)

    # Force HTTPS at the Django layer too (defence in depth — the reverse
    # proxy should already redirect).
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)

    # Cookies must only travel over HTTPS in prod.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False  # JS reads the CSRF token to set the header
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

    # Misc browser hardening
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

    # CSRF: the frontend lives on a different origin behind the same proxy,
    # so allow it explicitly. Configured via env so we don't bake a hostname
    # into the codebase.
    CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])
