from django.apps import AppConfig


class MediaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media"
    label = "media_app"  # avoid collision with django.conf.settings.MEDIA*
    verbose_name = "Media & annotations"
