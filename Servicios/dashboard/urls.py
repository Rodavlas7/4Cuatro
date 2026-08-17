"""Rutas del dashboard de administrador. Cuelgan de /api/dashboard/.

    /api/dashboard/resumen/                    foto de la planta ahora
    /api/dashboard/resumen-rango/?desde=&hasta= totales del periodo (sp_Dashboard_Resumen)
    /api/dashboard/produccion/?desde=&hasta=   laptops producidas por día
    /api/dashboard/calidad/?desde=&hasta=      inspecciones por día
    /api/dashboard/paros/?desde=&hasta=        paros por día
    /api/dashboard/tiempos/?desde=&hasta=      tiempo en línea por día (bruto y de turno)
    /api/dashboard/tiempos/laptop/<numero>/    lo que lleva una laptop, pasada por pasada
    /api/dashboard/stock/?umbral=10            inventario / material bajo
    /api/dashboard/actividad/?limite=15        últimos movimientos
    /api/dashboard/paros-abiertos/             paros sin cerrar
    /api/dashboard/rechazos/?desde=&hasta=     inspecciones rechazadas
    /api/dashboard/trazabilidad/               órdenes para el buscador
    /api/dashboard/trazabilidad/<folio>/       todo lo de una orden

Todas son GET y todas piden token de un usuario ADMIN.
"""

from django.urls import path

from .views import *

urlpatterns = [
    path("resumen/", ResumenPlantaAPIView.as_view(), name="dash-resumen"),
    path("resumen-rango/", ResumenRangoAPIView.as_view(), name="dash-resumen-rango"),
    path("produccion/", ProduccionDiariaAPIView.as_view(), name="dash-produccion"),
    path("calidad/", CalidadDiariaAPIView.as_view(), name="dash-calidad"),
    path("paros/", ParosDiariaAPIView.as_view(), name="dash-paros"),
    path("tiempos/", TiempoLineaDiariaAPIView.as_view(), name="dash-tiempos"),
    path("tiempos/laptop/<int:numero>/", TiempoLaptopAPIView.as_view(), name="dash-tiempo-laptop"),
    path("stock/", StockComponentesAPIView.as_view(), name="dash-stock"),
    path("actividad/", ActividadAPIView.as_view(), name="dash-actividad"),
    path("paros-abiertos/", ParosAbiertosAPIView.as_view(), name="dash-paros-abiertos"),
    path("rechazos/", RechazosAPIView.as_view(), name="dash-rechazos"),

    # La lista va antes que el detalle para que /trazabilidad/ no se lo coma
    # el patrón del folio.
    path("trazabilidad/", TrazabilidadOrdenesAPIView.as_view(), name="dash-traza-lista"),
    path("trazabilidad/<int:folio>/", TrazabilidadOrdenAPIView.as_view(), name="dash-traza-orden"),
]
