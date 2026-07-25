from django.urls import path
from . import views

urlpatterns = [
    # Ordenes de produccion
    path('ordenes/', views.ordenesProduccionListView, name='ordenes-produccion-lista'),
    path('ordenes/editar/<int:folio>/', views.ordenProduccionEditarView, name='orden-produccion-editar'),
    path('ordenes/cancelar/<int:folio>/', views.ordenProduccionCancelarView, name='orden-produccion-cancelar'),
    path('ordenes/<int:folio>/', views.ordenProduccionDetalleView, name='orden-produccion-detalle'),

    # Ensamblaje
    path('ensamblaje/registrar/', views.ensamblajeRegistrarView, name='ensamblaje-registrar'),
]
