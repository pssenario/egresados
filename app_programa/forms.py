"""Validated forms for training program management."""

from django import forms

from .models import Programa


class ProgramaForm(forms.ModelForm):
    """Collect catalog fields without managing Django user accounts."""

    class Meta:
        """Configure the editable program catalog fields."""

        model = Programa
        fields = ['nombre', 'codigo', 'area', 'activo']