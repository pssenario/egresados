"""Named URL routes for alumni management."""

from django.urls import path

from . import views

app_name = 'app_egresados'

urlpatterns = [
    path('egresados/', views.egresados_list_view, name='egresado_list'),
    path('egresados/nuevo/', views.egresado_create_view, name='egresado_create'),
    path('egresados/<int:pk>/', views.egresado_detail_view, name='egresado_detail'),
    path(
        'egresados/<int:pk>/inactivar/',
        views.egresado_inactivate_view,
        name='egresado_inactivate',
    ),
    path(
        'egresados/<int:pk>/editar/',
        views.egresado_update_view,
        name='egresado_update',
    ),
    path(
        'egresados/<int:pk>/trayectorias/nueva/',
        views.trayectoria_create_view,
        name='trayectoria_create',
    ),
    path(
        'egresados/<int:pk>/privacidad/',
        views.privacidad_update_view,
        name='privacidad_update',
    ),
]