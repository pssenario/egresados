"""Named URL routes for graduate follow-up workflows."""

from django.urls import path

from . import views

app_name = 'app_seguimiento'

urlpatterns = [
    path(
        'egresados/<int:pk>/seguimientos/nuevo/',
        views.seguimiento_create_view,
        name='seguimiento_create',
    ),
    path(
        'mi-portal/actualizar-situacion/',
        views.autogestion_create_view,
        name='autogestion_create',
    ),
    path(
        'seguimientos/pendientes/',
        views.seguimientos_pendientes_view,
        name='seguimientos_pendientes',
    ),
]