"""Application configuration for alumni management."""

from django.apps import AppConfig


class AppEgresadosConfig(AppConfig):
    """Configure the alumni management application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_egresados'
    verbose_name = 'Gestión de egresados'