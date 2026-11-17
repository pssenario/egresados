"""Application configuration for audit records."""

from django.apps import AppConfig


class AppAuditoriaConfig(AppConfig):
    """Configure the audit application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_auditoria'
    verbose_name = 'Auditoría del sistema'