"""URLs del panel de calidad. Van montadas en /panel/calidad/.

El `app_name` mete todos estos nombres bajo el namespace `panel_calidad`, así
que desde las plantillas se usan como {% url 'panel_calidad:inspecciones' %}.
Gracias a eso este panel puede nombrar sus pantallas como quiera sin chocar con
los otros dos.
"""

from django.urls import path

from . import views, views_flujo, views_inspecciones

app_name = 'panel_calidad'

urlpatterns = [
    path('', views.Dashboard.as_view(), name='dashboard'),

    # Flujo guiado: laptop -> ensamblaje -> inspección. La línea no se elige,
    # sale del empleado que inició sesión.
    path(
        'flujo/',
        views_flujo.SeleccionarLaptop.as_view(),
        name='flujo-laptops',
    ),
    path(
        'flujo/<int:laptop>/ensamblaje/',
        views_flujo.RegistrarEnsamblaje.as_view(),
        name='flujo-ensamblaje',
    ),
    path(
        'flujo/<int:laptop>/inspeccion/',
        views_flujo.Inspeccionar.as_view(),
        name='flujo-inspeccion',
    ),

    # Inspecciones de calidad
    path(
        'inspecciones/',
        views_inspecciones.ListaInspecciones.as_view(),
        name='inspecciones',
    ),
    path(
        'inspecciones/crear/',
        views_inspecciones.CrearInspeccion.as_view(),
        name='inspeccion-crear',
    ),
    path(
        'inspecciones/editar/<int:numero>/',
        views_inspecciones.EditarInspeccion.as_view(),
        name='inspeccion-editar',
    ),
    path(
        'inspecciones/eliminar/<int:numero>/',
        views_inspecciones.EliminarInspeccion.as_view(),
        name='inspeccion-eliminar',
    ),

    # Consulta que usa el formulario para llenar el select de empleados
    path(
        'empleados-calidad-por-linea/<str:linea_id>/',
        views_inspecciones.EmpleadosCalidadPorLinea.as_view(),
        name='empleados-calidad-por-linea',
    ),
]
