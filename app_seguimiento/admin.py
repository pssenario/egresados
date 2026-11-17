"""Django administration for follow-up history."""

from django.contrib import admin

from .models import Seguimiento


@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    """Allow administrators to inspect follow-up history."""

    list_display = ('egresado', 'fecha_contacto', 'medio', 'validacion', 'responsable')
    list_filter = ('medio', 'validacion', 'fecha_contacto')
    search_fields = ('egresado__nombres', 'egresado__apellidos', 'egresado__numero_documento')

    def has_delete_permission(self, request, obj=None):
        """Preserve follow-up history from physical deletion."""
        return False