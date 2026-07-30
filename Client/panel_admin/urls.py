"""URLs del panel de administrador. Van montadas en /panel/admin/.

El `app_name` hace que los nombres queden bajo el namespace `panel_admin`, así
que desde las plantillas se usan como {% url 'panel_admin:dashboard' %}. Gracias
a eso este panel puede nombrar sus pantallas como quiera sin chocar con los otros
dos.
"""

from django.urls import path

from . import views

app_name = 'panel_admin'

urlpatterns = [
    path('', views.Dashboard.as_view(), name='dashboard'),
]
