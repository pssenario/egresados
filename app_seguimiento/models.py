"""Follow-up records and validation states."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from app_egresados.models import Egresado


class Seguimiento(models.Model):
    """Record an institutional or graduate-submitted follow-up."""

    class Medio(models.TextChoices):
        """Contact channels available for follow-up."""

        TELEFONO = 'telefono', 'Llamada telefónica'
        CORREO = 'correo', 'Correo electrónico'
        PRESENCIAL = 'presencial', 'Presencial'
        MENSAJERIA = 'mensajeria', 'Mensajería'
        AUTOGESTIONADO = 'autogestionado', 'Autogestionado'

    class RelacionEmpleo(models.TextChoices):
        """Relationship between a job and the graduate's training."""

        RELACIONADO = 'relacionado', 'Relacionado'
        NO_RELACIONADO = 'no_relacionado', 'No relacionado'
        NO_APLICA = 'no_aplica', 'No aplica'

    class Validacion(models.TextChoices):
        """Validation state for self-reported follow-ups."""

        APROBADO = 'aprobado', 'Aprobado'
        PENDIENTE = 'pendiente', 'Pendiente de validación'
        RECHAZADO = 'rechazado', 'Rechazado'

    egresado = models.ForeignKey(
        Egresado, on_delete=models.PROTECT, related_name='seguimientos'
    )
    fecha_contacto = models.DateField()
    medio = models.CharField(max_length=20, choices=Medio.choices)
    estado_ocupacional = models.CharField(
        max_length=20, choices=Egresado.EstadoOcupacional.choices
    )
    relacion_empleo = models.CharField(
        max_length=20, choices=RelacionEmpleo.choices
    )
    observaciones = models.TextField()
    empresa = models.CharField(max_length=180, blank=True)
    sector_economico = models.CharField(max_length=120, blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='seguimientos_registrados',
    )
    origen = models.CharField(max_length=20, default='institucional')
    validacion = models.CharField(
        max_length=12, choices=Validacion.choices, default=Validacion.APROBADO
    )
    observacion_validacion = models.TextField(blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='seguimientos_validados',
    )
    creado_en = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        """Keep the existing follow-up table and ordering."""

        db_table = 'app_egresados_seguimiento'
        ordering = ['-fecha_contacto', '-creado_en']
        verbose_name = 'seguimiento'
        verbose_name_plural = 'seguimientos'

    def clean(self):
        """Require employment details when the reported situation needs them."""
        errors = {}
        if self.fecha_contacto and self.fecha_contacto > timezone.localdate():
            errors['fecha_contacto'] = 'La fecha de contacto no puede ser futura.'
        if self.estado_ocupacional in {
            Egresado.EstadoOcupacional.EMPLEADO,
            Egresado.EstadoOcupacional.EMPRENDIMIENTO,
        }:
            if not self.empresa:
                errors['empresa'] = 'Indica la empresa o emprendimiento.'
            if not self.sector_economico:
                errors['sector_economico'] = 'Indica el sector económico.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Validate the follow-up before persisting it."""
        self.full_clean()
        return super().save(*args, **kwargs)