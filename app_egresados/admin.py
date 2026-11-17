"""Django administration registrations for alumni domain records."""

from django.contrib import admin

from .models import Egresado, TrayectoriaAcademica


class TrayectoriaInline(admin.TabularInline):
    """Display each independent academic program association."""

    model = TrayectoriaAcademica
    extra = 0


@admin.register(Egresado)
class EgresadoAdmin(admin.ModelAdmin):
    """Expose alumni records for privileged operational administration."""

    list_display = (
        'numero_documento', 'nombre_completo', 'estado_ocupacional',
        'activo', 'origen', 'creado_en',
    )
    list_filter = ('activo', 'estado_ocupacional', 'autorizacion_datos', 'origen')
    search_fields = ('numero_documento', 'nombres', 'apellidos', 'correo')
    inlines = [TrayectoriaInline]
    readonly_fields = ('origen', 'creado_por', 'creado_en', 'actualizado_en')

    def has_delete_permission(self, request, obj=None):
        """Prevent physical deletion of graduate records."""
        return False


