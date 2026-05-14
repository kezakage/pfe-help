from django.contrib import admin

from .models import Page, PageVersion


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "position", "updated_at")
    list_filter = ("project",)
    search_fields = ("title",)


@admin.register(PageVersion)
class PageVersionAdmin(admin.ModelAdmin):
    list_display = ("page", "version_number", "author", "discipline", "status", "created_at")
    list_filter = ("status", "discipline")
    search_fields = ("page__title", "change_summary")
    readonly_fields = ("created_at",)
