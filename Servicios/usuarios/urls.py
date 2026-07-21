from django.urls import path
from .views import LoginAPIView, ListaEmpleadosAPIView, DetailEmpleadoAPIView, UpdateEmpleadoView, BajaEmpleadoView,RegistroEmpleadoAPIView, RegistroUsuarioAPIView
from usuarios import views #este y lo podemos borrar, no ya que lo andamos dividiendo por aplicaiones

#################################
# MARLENE MARLENE MARLENE AHORA EN POSTMAN usa "Bearer tu_token", en la parte donde tienes que poner tu token
###########################

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("Empleado/Registrar/", RegistroEmpleadoAPIView.as_view(), name="registro_empleado"),
    path("Empleado/Listar/", ListaEmpleadosAPIView.as_view(), name="lista_empleados"),
    path("Empleado/Detalle/<int:numero>/", DetailEmpleadoAPIView.as_view(), name="detalle_empleado"),
    path("Empleado/Actualizar/<int:numero>/", UpdateEmpleadoView.as_view(), name="update_empleado"),
    path("Empleado/Desactivar/<int:numero>/", BajaEmpleadoView.as_view(), name="desactivar_empleado"),
    path("Registrar/", RegistroUsuarioAPIView.as_view(), name="registro_usuario"),
]