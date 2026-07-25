from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import Sesion


# Cookie de host compartida entre el cliente (:8001) y la API (:8000).
# Las cookies no distinguen puerto, así que el token que guarda el cliente al
# iniciar sesión llega también hasta aquí y no hace falta loguearse dos veces.
TOKEN_COOKIE = "token_4cuatro"


class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")

        if auth_header:
            # Cliente de API (Postman, curl, front): token por header Bearer.
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Formato de token inválido")
            token = auth_header.split(" ")[1]
        else:
            # Navegador: token en la cookie que comparten cliente y API
            token = request.COOKIES.get(TOKEN_COOKIE)

        # Sin token en ningún lado
        if not token:
            return None

        try:
            sesion = Sesion.objects.get(token=token)

        except Sesion.DoesNotExist:
            raise AuthenticationFailed("Token inválido")

        if sesion.fecha_expiracion < timezone.now():
            sesion.delete()
            raise AuthenticationFailed("La sesión ha expirado")

        return (sesion.usuario, token)