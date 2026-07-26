from django.urls import path
from .views import ListaInspecciones, CrearInspeccion, EditarInspeccion, EliminarInspeccion, EmpleadosCalidadPorLinea


urlpatterns = [
    path('inspecciones/', ListaInspecciones.as_view(), name='lista_inspeccion_calidad'),
    path('inspecciones/crear/', CrearInspeccion.as_view(), name='inspeccion-crear'),
    path('inspecciones/editar/<int:numero>/', EditarInspeccion.as_view(), name='inspeccion-editar'),
    path('inspecciones/eliminar/<int:numero>/', EliminarInspeccion.as_view(), name='inspeccion-eliminar'),
    path('empleados-calidad-por-linea/<str:linea_id>/', EmpleadosCalidadPorLinea.as_view(), name='empleados-calidad-por-linea'),
]