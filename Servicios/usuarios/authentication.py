from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import Sesion


class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise AuthenticationFailed("Token no proporcionado")

        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Formato de token inválido")

        token = auth_header.split(" ")[1]

        try:
            sesion = Sesion.objects.get(token=token)

        except Sesion.DoesNotExist:
            raise AuthenticationFailed("Token inválido")

        if sesion.fecha_expiracion < timezone.now():
            sesion.delete()
            raise AuthenticationFailed("La sesión ha expirado")

        # DRF espera regresar (usuario, auth)
        return (sesion.usuario, token)