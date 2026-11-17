"""Validated forms for institutional and self-managed follow-ups."""

from django import forms

from .models import Seguimiento


class SeguimientoForm(forms.ModelForm):
    """Validate the required content for an institutional follow-up."""

    class Meta:
        """Configure mandatory follow-up fields and date input."""

        model = Seguimiento
        fields = [
            'fecha_contacto', 'medio', 'estado_ocupacional', 'relacion_empleo',
            'empresa', 'sector_economico', 'observaciones',
        ]
        widgets = {
            'fecha_contacto': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }


class AutogestionForm(forms.ModelForm):
    """Collect an alumni-submitted status update for staff validation."""

    class Meta:
        """Configure the fields available to a graduate in their portal."""

        model = Seguimiento
        fields = [
            'fecha_contacto', 'estado_ocupacional', 'relacion_empleo',
            'empresa', 'sector_economico', 'observaciones',
        ]
        widgets = {
            'fecha_contacto': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }