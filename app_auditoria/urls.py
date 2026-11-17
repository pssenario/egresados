"""Named URL routes for the audit log."""

from django.urls import path

from . import views

app_name = 'app_auditoria'

urlpatterns = [
    path('bitacora/', views.bitacora_list_view, name='bitacora'),
]