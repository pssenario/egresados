"""Application configuration for reporting."""

from django.apps import AppConfig


class AppReportesConfig(AppConfig):
    """Configure the reports application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_reportes'
    verbose_name = 'Reportes e indicadores'