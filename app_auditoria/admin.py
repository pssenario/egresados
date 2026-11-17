"""Read-only Django administration for audit records."""

from django.contrib import admin

from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    """Expose audit events as read-only administration records."""

    list_display = ('creado_en', 'usuario', 'accion', 'entidad', 'entidad_id')
    list_filter = ('accion', 'entidad', 'creado_en')
    search_fields = ('usuario__username', 'entidad', 'accion')
    readonly_fields = (
        'usuario', 'accion', 'entidad', 'entidad_id',
        'valores_anteriores', 'valores_nuevos', 'creado_en',
    )

    def has_add_permission(self, request):
        """Disallow manual creation of audit events in the admin site."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disallow changes to audit events in the admin site."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disallow deletion of audit events in the admin site."""
        return False