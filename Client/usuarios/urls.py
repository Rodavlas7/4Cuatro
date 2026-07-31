from django.urls import path
from .views import ListaEmpleados, CrearEmpleado, EditarEmpleado, DesactivarEmpleado, DetalleEmpleado, EstacionesPorLinea, ListaUsuarios, CrearUsuario, EditarUsuario, DesactivarUsuario, DetalleUsuario, ReactivarUsuario, ReactivarEmpleado
urlpatterns = [
    path('empleados/', ListaEmpleados.as_view(), name='lista_empleados'),
    path('empleados/crear/', CrearEmpleado.as_view(), name='empleado-crear'),
    path('empleados/detalle/<int:numero>/', DetalleEmpleado.as_view(), name='empleado-detalle'),
    path('empleados/Actualizar/<int:numero>/', EditarEmpleado.as_view(), name='empleado-editar'),
    path('empleados/desactivar/<int:numero>/', DesactivarEmpleado.as_view(), name='empleado-desactivar'),
    path('estaciones-por-linea/<str:linea_id>/', EstacionesPorLinea.as_view(), name='estaciones-por-linea'),
    path( "usuarios/", ListaUsuarios.as_view(), name="lista_usuarios"),
    path("usuarios/crear/", CrearUsuario.as_view(),name="usuario-crear"),
    path("usuarios/detalle/<int:numero>/", DetalleUsuario.as_view(),name="usuario-detalle"),
    path("usuarios/Actualizar/<int:numero>/",EditarUsuario.as_view(), name="usuario-editar"),
    path("usuarios/desactivar/<int:numero>/", DesactivarUsuario.as_view(), name="usuario-desactivar"),
    path("usuarios/reactivar/<int:numero>/", ReactivarUsuario.as_view(),name="usuario-reactivar"),
    path("empleados/reactivar/<int:numero>/", ReactivarEmpleado.as_view(), name="empleado-reactivar"),
]
