from django.contrib import admin
from . import models


@admin.register(models.Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.Service._meta.fields]


@admin.register(models.Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = [f.name for f in models.Source._meta.fields]
