from django.urls import path
from . import views


urlpatterns = [
    path("Inspeccion/Registrar/", views.RegistroInspeccionCalidadAPIView.as_view(), name="registrar_inspeccion_calidad"),
    path("Inspeccion/Listar/", views.ListaInspeccionCalidadAPIView.as_view(), name="listar_inspecciones_calidad"),
    path("Inspeccion/Detalle/<int:numero>/", views.DetailInspeccionCalidadAPIView.as_view(), name="detalle_inspeccion_calidad"),
    path("Inspeccion/Actualizar/<int:numero>/",views.UpdateInspeccionCalidadAPIView.as_view(), name="actualizar_inspeccion_calidad"),
    path("Inspeccion/Eliminar/<int:numero>/", views.DeleteInspeccionCalidadAPIView.as_view(),name="eliminar_inspeccion_calidad"),
    path("Inspeccion/Buscar/", views.BuscarInspeccionCalidadView.as_view(), name="buscar_inspeccion_calidad"),

    # Piezas que reprobaron una inspección
    path("Inspeccion/Detalle/Registrar/", views.RegistroDetalleInspeccionAPIView.as_view(), name="registrar_detalle_inspeccion"),
    path("Inspeccion/Detalle/Piezas/<int:inspeccion>/", views.ListaDetalleInspeccionAPIView.as_view(), name="listar_detalle_inspeccion"),
]