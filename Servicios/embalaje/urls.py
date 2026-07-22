from django.urls import path
from .views import RegistroEmbalajeAPIView, ListaRegistroEmbalajeAPIView, DetailRegistroEmbalajeAPIView, UpdateRegistroEmbalajeAPIView, DeleteRegistroEmbalajeAPIView


urlpatterns = [
    path("Embalaje/Registrar/", RegistroEmbalajeAPIView.as_view(), name="registrar_embalaje"),
    path("Embalaje/Listar/", ListaRegistroEmbalajeAPIView.as_view(), name="lista_embalajes"),
    path("Embalaje/Detalle/<int:numero>/", DetailRegistroEmbalajeAPIView.as_view(), name="detalle_embalaje"),
    path("Embalaje/Actualizar/<int:numero>/", UpdateRegistroEmbalajeAPIView.as_view(), name="actualizar_embalaje"),
    path("Embalaje/Eliminar/<int:numero>/", DeleteRegistroEmbalajeAPIView.as_view(), name="eliminar_embalaje"),

]
