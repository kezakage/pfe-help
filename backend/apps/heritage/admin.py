from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import HeritageResource, Project, ProjectMember


@admin.register(HeritageResource)
class HeritageResourceAdmin(GISModelAdmin):
    list_display = ("name_fr", "wilaya", "period", "architectural_type", "classification_level")
    list_filter = ("period", "architectural_type", "classification_level", "wilaya")
    search_fields = ("name_fr", "name_ar", "wilaya", "commune")


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "resource", "created_by", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "description")
    inlines = (ProjectMemberInline,)
