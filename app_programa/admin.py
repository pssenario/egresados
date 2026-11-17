"""Django administration for training programs."""

from django.contrib import admin

from .models import Programa


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    """Provide searchable program and staff-scope administration."""

    list_display = ('nombre', 'codigo', 'area', 'activo')
    list_filter = ('activo', 'area')
    search_fields = ('nombre', 'codigo', 'area')
    filter_horizontal = ('funcionarios',)