from django.urls import path
from .views import *

urlpatterns = [
    path("", LineaListAPIView.as_view(), name="linea-list-create"),
    path("estados/", EdoLineaListAPIView.as_view(), name="edo-linea-list"),
    path("tipos/", TipoLineaListAPIView.as_view(), name="tipo-linea-list"),
    path("estaciones/", EstacionListCreateAPIView.as_view(), name="estacion-list-create"),
    path("estaciones/mod/<str:codigo>/", EstacionModifyAPIView.as_view(), name="estacion-modify"),
    path("estaciones/<str:codigo>/", EstacionDetailAPIView.as_view(), name="estacion-detail"),
    path("mod/<str:codigo>/", LineaModifyAPIView.as_view(), name="linea-modify"),
    path("<str:codigo>/supervisores/", SupervisoresLineaAPIView.as_view(), name="linea-supervisores"),
    path("<str:codigo>/supervisores/<int:numero>/", SupervisorLineaQuitarAPIView.as_view(), name="linea-supervisor-quitar"),
    path("<str:codigo>/", LineaDetailAPIView.as_view(), name="linea-detail"),
    path("lineas/estaciones/", ListaEstacionesAPIView.as_view(), name="linea-estacion"),
    path("lineas/activas/", LineasActivasAPIView.as_view(), name="lineas-activas"),
]
