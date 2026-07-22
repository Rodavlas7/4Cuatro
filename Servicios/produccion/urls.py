from django.urls import path
from .views import *

urlpatterns = [
    path("", OrdenProduccionListAPIView.as_view(), name="orden-list-create"),
    path("estados/", EdoProduccionListAPIView.as_view(), name="edo-produccion-list"),
    path("modelos/", ModeloLaptopListAPIView.as_view(), name="modelo-laptop-list"),
    path("modelos/<str:codigo>/", ModeloLaptopDetailAPIView.as_view(), name="modelo-laptop-detail"),
    path("estados-laptop/", EdoLaptopListAPIView.as_view(), name="edo-laptop-list"),
    path("lotes/", LoteLaptopListAPIView.as_view(), name="lote-laptop-list"),
    path("lotes/<str:codigo>/", LoteLaptopDetailAPIView.as_view(), name="lote-laptop-detail"),
    path("paros/", ParoListCreateAPIView.as_view(), name="paro-list-create"),
    path("paros/mod/<int:numero>/", ParoModifyAPIView.as_view(), name="paro-modify"),
    path("paros/<int:numero>/", ParoDetailAPIView.as_view(), name="paro-detail"),
    path("laptops/", LaptopListAPIView.as_view(), name="laptop-list-create"),
    path("laptops/mod/<int:numero>/", LaptopModifyAPIView.as_view(), name="laptop-modify"),
    path("laptops/<int:numero>/", LaptopDetailAPIView.as_view(), name="laptop-detail"),
    path("registros-ensamblaje/", RegistroEnsamblajeListCreateAPIView.as_view(), name="registro-ensamblaje-list-create"),
    path("registros-ensamblaje/mod/<int:numero>/", RegistroEnsamblajeModifyAPIView.as_view(), name="registro-ensamblaje-modify"),
    path("registros-ensamblaje/<int:numero>/", RegistroEnsamblajeDetailAPIView.as_view(), name="registro-ensamblaje-detail"),
    path("mod/<int:folio>/", OrdenProduccionModifyAPIView.as_view(), name="orden-modify"),
    path("<int:folio>/", OrdenProduccionDetailAPIView.as_view(), name="orden-detail"),
]