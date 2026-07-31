from django.urls import path
from . import views

urlpatterns = [
    # Ordenes de produccion
    path('ordenes/', views.ordenesProduccionListView, name='ordenes-produccion-lista'),
    path('ordenes/editar/<int:folio>/', views.ordenProduccionEditarView, name='orden-produccion-editar'),
    path('ordenes/cancelar/<int:folio>/', views.ordenProduccionCancelarView, name='orden-produccion-cancelar'),
    path('ordenes/<int:folio>/', views.ordenProduccionDetalleView, name='orden-produccion-detalle'),

    # Laptops
    path('laptops/', views.laptopsListView, name='laptops-lista'),
    path('laptops/editar/<int:numero>/', views.laptopEditarView, name='laptop-editar'),
    path('laptops/rechazar/<int:numero>/', views.laptopRechazarView, name='laptop-rechazar'),
    path('laptops/<int:numero>/', views.laptopDetalleView, name='laptop-detalle'),
    path('laptops/<int:numero>/liberar/<int:componente>/', views.laptopComponenteLiberarView, name='laptop-componente-liberar'),

    # Ensamblaje
    path('ensamblaje/', views.ensamblajeSeguimientoView, name='ensamblaje-seguimiento'),
    path('ensamblaje/registrar/', views.ensamblajeRegistrarView, name='ensamblaje-registrar'),
    
    #Paros
    path('paros/', views.ListaParos.as_view(), name='lista_paros'),
    path('paros/crear/', views.CrearParo.as_view(), name='paro-crear'),
    path('paros/editar/<int:numero>/', views.EditarParo.as_view(), name='paro-editar'),
    path('paros/cerrar/<int:numero>/', views.CerrarParo.as_view(), name='paro-cerrar'),
]
