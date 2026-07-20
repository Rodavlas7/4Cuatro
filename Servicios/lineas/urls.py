from django.urls import path
from .views import *

urlpatterns = [
    path("", LineaListAPIView.as_view(), name="linea-list-create"),
    path("estados/", EdoLineaListAPIView.as_view(), name="edo-linea-list"),
    path("estaciones/", EstacionListCreateAPIView.as_view(), name="estacion-list-create"),
    path("estaciones/<str:codigo>/", EstacionDetailAPIView.as_view(), name="estacion-detail"),
    path("mod/<str:codigo>/", LineaModifyAPIView.as_view(), name="linea-modify"),
    path("<str:codigo>/", LineaDetailAPIView.as_view(), name="linea-detail"),
]
