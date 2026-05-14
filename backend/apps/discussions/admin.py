from django.contrib import admin

from .models import ConflictVote, Discussion, Message


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "type", "status", "opened_by", "updated_at")
    list_filter = ("type", "status")
    search_fields = ("title",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "discussion", "author", "is_proposal", "created_at")
    list_filter = ("is_proposal",)
    search_fields = ("body",)


@admin.register(ConflictVote)
class ConflictVoteAdmin(admin.ModelAdmin):
    list_display = ("discussion", "voter", "choice", "created_at")
    list_filter = ("choice",)
