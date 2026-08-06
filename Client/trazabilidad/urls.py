from django.urls import path

from . import views

app_name = 'trazabilidad'

urlpatterns = [
    # Buscador Inteligente Unificado
    path('', views.trazabilidadView, name='trazabilidad'),
    
    # RF44 - Trazabilidad consolidada por Orden de Producción
    path('orden/<int:folio>/', views.TrazabilidadOrden.as_view(), name='trazabilidad_x_orden'),
    
    # RF43 a RF50 - Trazabilidad específica por Laptop
    path('laptop/<str:num_serie>/', views.trazabilidadLaptopView, name='trazabilidad_x_laptop'), 
]

