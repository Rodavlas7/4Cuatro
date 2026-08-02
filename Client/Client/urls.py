"""
URL configuration for Client project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login, logout y el repartidor que manda a cada rol a su panel.
    path('', include('home.urls')),

    # Un panel por rol. Cada uno con su propio namespace, así que los tres
    # pueden nombrar sus pantallas igual sin estorbarse.
    path('panel/admin/', include('panel_admin.urls')),
    path('panel/calidad/', include('panel_calidad.urls')),
    path('panel/supervisor/', include('panel_supervisor.urls')),

    # Pantallas del panel de administrador. Se quedaron en su ruta original
    # porque son las que ya estaban hechas cuando el cliente era uno solo; el
    # middleware de core sólo deja entrar al rol ADMIN.
    path('componentes/', include('componentes.urls')),
    path('produccion/', include('produccion.urls')),
    path('lineas/', include('lineas.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('calidad/', include('calidad.urls')),
    path('embalaje/', include('embalaje.urls')),
]
