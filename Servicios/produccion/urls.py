from django.urls import path
from .views import (
    EdoProduccionListAPIView,
    ModeloLaptopListAPIView,
    OrdenProduccionListAPIView,
    OrdenProduccionDetailAPIView,
    OrdenProduccionModifyAPIView,
    ParoListCreateAPIView,
    ParoDetailAPIView,
    ParoModifyAPIView,
)

urlpatterns = [
    path("", OrdenProduccionListAPIView.as_view(), name="orden-list-create"),
    path("estados/", EdoProduccionListAPIView.as_view(), name="edo-produccion-list"),
    path("modelos/", ModeloLaptopListAPIView.as_view(), name="modelo-laptop-list"),
    path("paros/", ParoListCreateAPIView.as_view(), name="paro-list-create"),
    path("paros/mod/<int:numero>/", ParoModifyAPIView.as_view(), name="paro-modify"),
    path("paros/<int:numero>/", ParoDetailAPIView.as_view(), name="paro-detail"),
    path("mod/<int:folio>/", OrdenProduccionModifyAPIView.as_view(), name="orden-modify"),
    path("<int:folio>/", OrdenProduccionDetailAPIView.as_view(), name="orden-detail"),
]
