"""Append-only audit records for system actions."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Bitacora(models.Model):
    """Store an append-only audit record for user actions."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='eventos_bitacora',
    )
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=80)
    entidad_id = models.PositiveBigIntegerField(null=True, blank=True)
    valores_anteriores = models.JSONField(default=dict, blank=True)
    valores_nuevos = models.JSONField(default=dict, blank=True)
    creado_en = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Keep the existing audit table and newest-first ordering."""

        db_table = 'app_egresados_bitacora'
        ordering = ['-creado_en']
        verbose_name = 'registro de bitácora'
        verbose_name_plural = 'bitácora'

    def __str__(self):
        """Describe the audited action and its entity."""
        return f'{self.accion}: {self.entidad} #{self.entidad_id or "-"}'