from django.urls import path
from .views import RegistroEmbalajeAPIView, ListaRegistroEmbalajeAPIView, DetailRegistroEmbalajeAPIView, UpdateRegistroEmbalajeAPIView, BuscarRegistroEmbalajeView, LaptopsDisponiblesAPIView, TipoEmbalajeListAPIView


urlpatterns = [
    path("Embalaje/Registrar/", RegistroEmbalajeAPIView.as_view(), name="registrar_embalaje"),
    path("Embalaje/Listar/", ListaRegistroEmbalajeAPIView.as_view(), name="lista_embalajes"),
    path("Embalaje/Detalle/<int:numero>/", DetailRegistroEmbalajeAPIView.as_view(), name="detalle_embalaje"),
    path("Embalaje/Actualizar/<int:numero>/", UpdateRegistroEmbalajeAPIView.as_view(), name="actualizar_embalaje"),
    path("Embalaje/Buscar/", BuscarRegistroEmbalajeView.as_view(), name="buscar_embalaje"),
    path("Embalaje/Auxiliares/LaptopsDisponibles/", LaptopsDisponiblesAPIView.as_view(), name="laptops_disponibles"),
    path("Embalaje/Auxiliares/TiposEmbalaje/", TipoEmbalajeListAPIView.as_view(), name="tipos_embalaje"),

]
