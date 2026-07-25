from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from .models import Sesion


class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")

        if auth_header:
            # Cliente de API (Postman, curl, front): token por header Bearer.
            if not auth_header.startswith("Bearer "):
                raise AuthenticationFailed("Formato de token inválido")
            token = auth_header.split(" ")[1]
        else:
            # Permite navegar la API sin pegar el Bearer a mano.
            token = getattr(request, "session", {}).get("token")

        # Sin token en ningún lado -> no autenticar (las vistas AllowAny siguen ok).
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