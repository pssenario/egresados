"""Training program catalog models."""

from django.conf import settings
from django.db import models


class Programa(models.Model):
    """Represent a SENA training program and its assigned staff."""

    nombre = models.CharField(max_length=180, unique=True)
    codigo = models.CharField(max_length=30, blank=True)
    area = models.CharField(max_length=120, blank=True)
    funcionarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='programas_asignados',
        db_table='app_egresados_programa_funcionarios',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        """Preserve the existing database table during app ownership transfer."""

        db_table = 'app_egresados_programa'
        ordering = ['nombre']
        verbose_name = 'programa'
        verbose_name_plural = 'programas'

    def __str__(self):
        """Return the program name for Django forms and administration."""
        return self.nombre