from django.urls import path
from .views import *
 
urlpatterns = [
    # Componentes
    path("", ComponenteListAPIView.as_view(), name="componente-list-create"),
    path("mod/<int:numero>/", ComponenteModifyAPIView.as_view(), name="componente-modify"),
    path("<int:numero>/", ComponenteDetailAPIView.as_view(), name="componente-detail"),
    path("tipos/", TipoCompListAPIView.as_view(), name="tipo-comp-list"),
    path("estados/", EdoComponenteListAPIView.as_view(), name="edo-componente-list"),
 
    # Lotes de componentes
    path("lotes/", LoteCompListCreateAPIView.as_view(), name="lote-comp-list-create"),
    path("lotes/mod/<str:codigo>/", LoteCompModifyAPIView.as_view(), name="lote-comp-modify"),
    path("lotes/<str:codigo>/", LoteCompDetailAPIView.as_view(), name="lote-comp-detail"),
 
    # Modelos de componente
    path("modelos/", ModeloComponenteListCreateAPIView.as_view(), name="modelo-componente-list-create"),
    path("modelos/mod/<str:codigo>/", ModeloComponenteModifyAPIView.as_view(), name="modelo-componente-modify"),
    path("modelos/<str:codigo>/", ModeloComponenteDetailAPIView.as_view(), name="modelo-componente-detail"),
 
    # Ordenes de material
    path("ordenes/", OrdenMaterialListCreateAPIView.as_view(), name="orden-material-list-create"),
    path("ordenes/mod/<int:numero>/", OrdenMaterialModifyAPIView.as_view(), name="orden-material-modify"),
    path("ordenes/<int:numero>/", OrdenMaterialDetailAPIView.as_view(), name="orden-material-detail"),
 
    # Detalle de material (renglones de una orden)
    path("detalles/", DetalleMaterialListCreateAPIView.as_view(), name="detalle-material-list-create"),
    path("detalles/mod/<int:orden>/<str:modelo>/", DetalleMaterialModifyAPIView.as_view(), name="detalle-material-modify"),
]