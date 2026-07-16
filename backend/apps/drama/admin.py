# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from apps.drama.models import (
    DramaArtifactVersion,
    DramaAuditEvent,
    DramaCommand,
    DramaConfigRevision,
    DramaGenerationJob,
    DramaLlmProvider,
    DramaProject,
    DramaWorkflowState,
)

admin.site.unregister(User)
admin.site.register(User, BaseUserAdmin)


@admin.register(DramaProject)
class DramaProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "settings_revision", "updated_at")
    search_fields = ("title",)


admin.site.register(DramaWorkflowState)
admin.site.register(DramaArtifactVersion)
admin.site.register(DramaCommand)
admin.site.register(DramaGenerationJob)
admin.site.register(DramaConfigRevision)
admin.site.register(DramaAuditEvent)
admin.site.register(DramaLlmProvider)
