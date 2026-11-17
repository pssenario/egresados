"""Domain models for graduates, their education, and follow-up history."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from app_programa.models import Programa


class Egresado(models.Model):
    """Store one person and their current contact and privacy preferences."""

    class MotivoInactivacion(models.TextChoices):
        """Configurable reasons for administrative inactivation."""

        RETIRO = 'retiro', 'Retiro del registro'
        FALLECIMIENTO = 'fallecimiento', 'Fallecimiento'
        DUPLICADO = 'duplicado', 'Registro duplicado'
        OTRO = 'otro', 'Otro motivo'

    class TipoDocumento(models.TextChoices):
        """Available Colombian identity document types."""

        CC = 'CC', 'Cédula de ciudadanía'
        CE = 'CE', 'Cédula de extranjería'
        TI = 'TI', 'Tarjeta de identidad'
        PPT = 'PPT', 'Permiso por protección temporal'
        PAS = 'PAS', 'Pasaporte'

    class EstadoOcupacional(models.TextChoices):
        """Current employment and education situations."""

        SIN_DATO = 'sin_dato', 'Sin información'
        EMPLEADO = 'empleado', 'Empleado'
        EMPRENDIMIENTO = 'emprendimiento', 'Emprendimiento'
        DESEMPLEADO = 'desempleado', 'Desempleado'
        ESTUDIANDO = 'estudiando', 'Estudiando'
        BUSCANDO = 'buscando', 'En búsqueda de empleo'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registro_egresado',
    )
    tipo_documento = models.CharField(max_length=3, choices=TipoDocumento.choices)
    numero_documento = models.CharField(max_length=30)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    correo = models.EmailField(blank=True)
    correo_verificado = models.BooleanField(default=False)
    telefono = models.CharField(max_length=30, blank=True)
    telefono_verificado = models.BooleanField(default=False)
    direccion = models.CharField(max_length=220, blank=True)
    estado_ocupacional = models.CharField(
        max_length=20,
        choices=EstadoOcupacional.choices,
        default=EstadoOcupacional.SIN_DATO,
    )
    preferencias_contacto = models.CharField(max_length=120, blank=True)
    autorizacion_datos = models.BooleanField(default=False)
    fecha_autorizacion = models.DateTimeField(null=True, blank=True)
    no_contacto = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    motivo_inactivacion = models.CharField(
        max_length=20,
        choices=MotivoInactivacion.choices,
        blank=True,
    )
    fusionado_en = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='registros_fusionados',
    )
    origen = models.CharField(max_length=20, default='manual')
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='egresados_creados',
    )
    creado_en = models.DateTimeField(default=timezone.now, editable=False)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['apellidos', 'nombres']
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_documento', 'numero_documento'],
                name='egresado_documento_unico',
            ),
        ]
        permissions = [
            ('ambito_global_egresados', 'Puede consultar todos los programas'),
            ('ver_contacto_completo', 'Puede consultar datos de contacto completos'),
        ]
        verbose_name = 'egresado'
        verbose_name_plural = 'egresados'

    def __str__(self):
        """Return the graduate's full name and document number."""
        return f'{self.nombres} {self.apellidos} ({self.numero_documento})'

    @property
    def nombre_completo(self):
        """Return the graduate's display name."""
        return f'{self.nombres} {self.apellidos}'

    @property
    def ultima_fecha_seguimiento(self):
        """Return the latest follow-up date, if any."""
        return self.seguimientos.order_by('-fecha_contacto').values_list(
            'fecha_contacto', flat=True
        ).first()


class TrayectoriaAcademica(models.Model):
    """Link a graduate to one distinct titled training program."""

    egresado = models.ForeignKey(
        Egresado, on_delete=models.CASCADE, related_name='trayectorias'
    )
    programa = models.ForeignKey(
        Programa, on_delete=models.PROTECT, related_name='trayectorias'
    )
    ficha = models.CharField(max_length=30, blank=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_titulacion = models.DateField()

    class Meta:
        ordering = ['-fecha_titulacion']
        constraints = [
            models.UniqueConstraint(
                fields=['egresado', 'programa'],
                name='trayectoria_programa_unico_por_egresado',
            ),
        ]
        verbose_name = 'trayectoria académica'
        verbose_name_plural = 'trayectorias académicas'

    def clean(self):
        """Reject dates that violate academic chronology."""
        errors = {}
        if self.fecha_titulacion and self.fecha_titulacion > timezone.localdate():
            errors['fecha_titulacion'] = 'La fecha de titulación no puede ser futura.'
        if (
            self.fecha_inicio
            and self.fecha_titulacion
            and self.fecha_titulacion < self.fecha_inicio
        ):
            errors['fecha_titulacion'] = (
                'La fecha de titulación no puede ser anterior al inicio del programa.'
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Validate the academic dates before persisting the association."""
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        """Return the program and graduate associated with this record."""
        return f'{self.egresado.nombre_completo} - {self.programa.nombre}'


