from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Annotation, Media


@admin.register(Media)
class MediaAdmin(GISModelAdmin):
    list_display = ("id", "media_type", "project", "uploader", "size_bytes", "created_at")
    list_filter = ("media_type", "project")
    search_fields = ("caption", "license")
    readonly_fields = ("size_bytes", "mime_type", "width", "height", "duration_seconds", "created_at")


@admin.register(Annotation)
class AnnotationAdmin(GISModelAdmin):
    list_display = ("id", "media", "resource", "author", "discipline", "is_ai_generated", "is_validated", "created_at")
    list_filter = ("is_ai_generated", "is_validated", "discipline")
    search_fields = ("body_text",)
    readonly_fields = ("created_at",)
