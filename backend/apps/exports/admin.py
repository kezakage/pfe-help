from django.contrib import admin

from .models import ExportJob


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ("id", "format", "status", "requested_by", "project", "created_at", "finished_at")
    list_filter = ("format", "status")
    readonly_fields = ("started_at", "finished_at", "created_at", "error_message")
