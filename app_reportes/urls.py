"""Named URL routes for dashboards and exports."""

from django.urls import path

from . import views

app_name = 'app_reportes'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('egresados/exportar/', views.egresados_export_view, name='egresado_export'),
]