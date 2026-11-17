"""Named URL routes for the program catalog."""

from django.urls import path

from . import views

app_name = 'app_programa'

urlpatterns = [
    path('programas/', views.programas_list_view, name='programa_list'),
    path('programas/nuevo/', views.programa_create_view, name='programa_create'),
    path(
        'programas/<int:pk>/editar/',
        views.programa_update_view,
        name='programa_update',
    ),
]