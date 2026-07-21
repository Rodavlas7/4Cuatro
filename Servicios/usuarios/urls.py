from django.urls import path
from .views import LoginAPIView
from usuarios import views

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("Empleado/Registrar/", views.RegistroEmpleadoAPIView.as_view(), name="registro_empleado")
]
