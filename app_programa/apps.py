"""Application configuration for the training program catalog."""

from django.apps import AppConfig


class AppProgramaConfig(AppConfig):
    """Configure the program catalog application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_programa'
    verbose_name = 'Programas de formación'