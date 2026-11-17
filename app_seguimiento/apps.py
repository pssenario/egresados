"""Application configuration for graduate follow-up workflows."""

from django.apps import AppConfig


class AppSeguimientoConfig(AppConfig):
    """Configure the follow-up application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_seguimiento'
    verbose_name = 'Seguimiento a egresados'