from django.urls import path
from .views import LoginAPIView, ListaEmpleadosAPIView, DetailEmpleadoAPIView, UpdateEmpleadoAPIView, BajaEmpleadoView,RegistroEmpleadoAPIView, RegistroUsuarioAPIView, UpdateUsuarioAPIView, BajaUsuarioAPIView, ListaUsuariosAPIView, DetailUsuarioAPIView,ReactivarUsuarioAPIView
from usuarios import views #este y lo podemos borrar, ya que lo andamos dividiendo por aplicaiones

#################################
# MARLENE MARLENE MARLENE AHORA EN POSTMAN usa "Bearer tu_token", en la parte donde tienes que poner tu token
###########################


urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("Empleado/Registrar/", RegistroEmpleadoAPIView.as_view(), name="registro_empleado"),
    path("Empleado/Listar/", ListaEmpleadosAPIView.as_view(), name="lista_empleados"),
    path("Empleado/Detalle/<int:numero>/", DetailEmpleadoAPIView.as_view(), name="detalle_empleado"),
    path("Empleado/Actualizar/<int:numero>/", UpdateEmpleadoAPIView.as_view(), name="update_empleado"),
    path("Empleado/Desactivar/<int:numero>/", BajaEmpleadoView.as_view(), name="desactivar_empleado"),
    path("Usuario/Registrar/", RegistroUsuarioAPIView.as_view(), name="registro_usuario"),
    path("Usuario/Listar/", ListaUsuariosAPIView.as_view(), name="lista_usuarios"),
    path("Usuario/Detalle/<int:numero>/", DetailUsuarioAPIView.as_view(), name="detalle_empleado"),
    path("Usuario/Actualizar/<int:numero>/", UpdateUsuarioAPIView.as_view(), name="actualizar_usuario"),
    path("Usuario/Desactivar/<int:numero>/", BajaUsuarioAPIView.as_view(), name="desactivar_usuario"),
    path("Usuario/Reactivar/<int:numero>/", views.ReactivarUsuarioAPIView.as_view(), name="reactivar_usuario"),
    path("Empleado/Buscar/", views.BuscarUsuarioView.as_view(), name="buscar_empleado"),
    path("Usuario/Buscar/", views.BuscarUsuarioView.as_view(), name="buscar_usuario"),
    path("Empleado/Linea/Buscar/", views.BuscarEmpleadoLineaView.as_view(), name="buscar_empleado-linea"),
    path("Empleado/Estacion/Buscar/", views.BuscarEmpleadoEstacionView.as_view(), name="buscar_empleado-estacion")
]