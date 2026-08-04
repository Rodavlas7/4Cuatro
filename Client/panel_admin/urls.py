"""URLs del panel de administrador. Van montadas en /panel/admin/.

El `app_name` hace que los nombres queden bajo el namespace `panel_admin`, así
que desde las plantillas se usan como {% url 'panel_admin:dashboard' %}. Gracias
a eso este panel puede nombrar sus pantallas como quiera sin chocar con los otros
dos.
"""

from django.urls import path

from . import views_dashboard, views_trazabilidad

app_name = 'panel_admin'

urlpatterns = [
    path('', views_dashboard.Dashboard.as_view(), name='dashboard'),

    # La trazabilidad acepta el folio en la URL o por el buscador (?folio=N),
    # por eso son dos rutas al mismo lugar.
    path('trazabilidad/', views_trazabilidad.TrazabilidadOrden.as_view(),
         name='trazabilidad'),
    path('trazabilidad/<int:folio>/', views_trazabilidad.TrazabilidadOrden.as_view(),
         name='trazabilidad-orden'),
]
