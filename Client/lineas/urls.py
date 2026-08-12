from django.urls import path
from . import views

urlpatterns = [
    # Estaciones de trabajo (deben ir ANTES del catch-all <str:codigo>/ de abajo,
    # si no Django interpreta "estaciones/" como si fuera el código de una línea)
    path('estaciones/', views.estacionesListView, name='estaciones-lista'),
    path('estaciones/editar/<str:codigo>/', views.estacionEditarView, name='estacion-editar'),
    path('estaciones/baja/<str:codigo>/', views.estacionBajaView, name='estacion-baja'),

    # Lineas de ensamblaje
    path('', views.lineasListView, name='lineas-lista'),
    path('editar/<str:codigo>/', views.lineaEditarView, name='linea-editar'),
    path('baja/<str:codigo>/', views.lineaBajaView, name='linea-baja'),

    # Supervisores de la línea (también antes del catch-all de abajo)
    path('<str:codigo>/supervisores/asignar/', views.lineaSupervisorAsignarView, name='linea-supervisor-asignar'),
    path('<str:codigo>/supervisores/quitar/<int:numero>/', views.lineaSupervisorQuitarView, name='linea-supervisor-quitar'),

    path('<str:codigo>/', views.lineaDetalleView, name='linea-detalle'),
]
