"""
URL configuration for egresados project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""Project URL routing."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='app_egresados/app_egresados_login.html'
        ),
        name='login',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('app_reportes.urls')),
    path('', include('app_egresados.urls')),
    path('', include('app_programa.urls')),
    path('', include('app_seguimiento.urls')),
    path('', include('app_auditoria.urls')),
]
