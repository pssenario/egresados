"""Validated forms for graduate and follow-up workflows."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from app_programa.models import Programa

from .models import Egresado, TrayectoriaAcademica


class EgresadoForm(forms.ModelForm):
    """Collect required identity, contact, and initial academic information."""

    programa = forms.ModelChoiceField(queryset=Programa.objects.filter(activo=True))
    ficha = forms.CharField(max_length=30, required=False)
    fecha_inicio = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'})
    )
    fecha_titulacion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        """Configure the graduate fields displayed in the creation form."""

        model = Egresado
        fields = [
            'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'correo', 'telefono', 'programa', 'ficha', 'fecha_inicio',
            'fecha_titulacion', 'autorizacion_datos',
        ]
        widgets = {
            'autorizacion_datos': forms.CheckboxInput(),
        }

    def clean_fecha_titulacion(self):
        """Reject future graduation dates and dates before program start."""
        graduation_date = self.cleaned_data['fecha_titulacion']
        start_date = self.cleaned_data.get('fecha_inicio')
        if graduation_date > timezone.localdate():
            raise ValidationError('La fecha de titulación no puede ser futura.')
        if start_date and graduation_date < start_date:
            raise ValidationError(
                'La fecha de titulación no puede ser anterior al inicio del programa.'
            )
        return graduation_date

    def clean(self):
        """Require at least one contact channel and reject duplicate identity."""
        cleaned_data = super().clean()
        if not cleaned_data.get('correo') and not cleaned_data.get('telefono'):
            raise ValidationError('Registra al menos un correo o un teléfono.')
        document_type = cleaned_data.get('tipo_documento')
        document_number = cleaned_data.get('numero_documento')
        if document_type and document_number:
            existing = Egresado.objects.filter(
                tipo_documento=document_type,
                numero_documento=document_number,
            ).first()
            if existing:
                raise ValidationError(
                    f'Ya existe un egresado con ese documento: '
                    f'{existing.nombre_completo} (registro #{existing.pk}).'
                )
        return cleaned_data

    def save(self, commit=True):
        """Save the graduate and their first academic program association."""
        egresado = super().save(commit=commit)
        if commit:
            TrayectoriaAcademica.objects.create(
                egresado=egresado,
                programa=self.cleaned_data['programa'],
                ficha=self.cleaned_data.get('ficha', ''),
                fecha_inicio=self.cleaned_data.get('fecha_inicio'),
                fecha_titulacion=self.cleaned_data['fecha_titulacion'],
            )
        return egresado


class ContactoEgresadoForm(forms.ModelForm):
    """Allow contact and current situation edits without academic changes."""

    class Meta:
        """Configure editable contact and current-situation fields."""

        model = Egresado
        fields = [
            'correo', 'telefono', 'direccion', 'estado_ocupacional',
            'preferencias_contacto',
        ]

    def clean(self):
        """Ensure at least one contact channel remains on the record."""
        cleaned_data = super().clean()
        if not cleaned_data.get('correo') and not cleaned_data.get('telefono'):
            raise ValidationError('Debe conservar al menos un correo o teléfono.')
        return cleaned_data


class TrayectoriaForm(forms.ModelForm):
    """Collect one additional training program association."""

    def __init__(self, *args, egresado=None, **kwargs):
        """Bind the graduate whose program associations must remain unique."""
        self.egresado = egresado
        super().__init__(*args, **kwargs)

    def clean(self):
        """Reject a program already associated with this graduate."""
        cleaned_data = super().clean()
        program = cleaned_data.get('programa')
        if self.egresado and program and TrayectoriaAcademica.objects.filter(
            egresado=self.egresado,
            programa=program,
        ).exists():
            self.add_error('programa', 'Este programa ya está asociado al egresado.')
        return cleaned_data

    class Meta:
        """Configure academic fields for an additional program association."""

        model = TrayectoriaAcademica
        fields = ['programa', 'ficha', 'fecha_inicio', 'fecha_titulacion']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_titulacion': forms.DateInput(attrs={'type': 'date'}),
        }

