"""Control de acceso a los paneles por prefijo de URL.

Se hace en middleware y no vista por vista a propósito: un panel son decenas de
vistas, y si el candado se pone en cada una, basta que alguien olvide un
decorador para abrir la puerta. Aquí el bloqueo es por prefijo, así que una
pantalla nueva dentro de un panel ya nace protegida.

Ojo: esto NO reemplaza los permisos de la API. La API valida por su cuenta
(Servicios/usuarios/permissions.py). Esto es para que nadie navegue a pantallas
que no le tocan y para que el error salga aquí, bonito, en lugar de un 403 de la
API a media pantalla.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles. Para agregar una
sección nueva a un panel, agrega su prefijo en RUTAS_POR_ROL.
"""

from django.contrib import messages
from django.shortcuts import redirect

from .roles import ROL_ADMIN, ROL_CALIDAD, ROL_SUPERVISOR, panel_inicio


# Rutas que no piden sesión, comparadas completas. El '/' entra aquí porque
# `indexView` ya se encarga de mandar al login o al panel según corresponda.
RUTAS_LIBRES = (
    '/',
    '/login/',
    '/logout/',
)

# Igual que RUTAS_LIBRES pero comparadas por prefijo, para lo que trae cola:
# archivos estáticos y el admin de Django (que tiene su propio login).
PREFIJOS_LIBRES = (
    '/static/',
    '/admin/',
)

# Prefijo de URL -> roles que pueden entrar. Se evalúa en orden y gana el primer
# prefijo que coincida, así que los más específicos van arriba.
RUTAS_POR_ROL = (
    ('/panel/admin/', (ROL_ADMIN,)),
    ('/panel/calidad/', (ROL_CALIDAD,)),
    ('/panel/supervisor/', (ROL_SUPERVISOR,)),

    # Pantallas del panel de administrador. Viven en las apps originales
    # (produccion/, calidad/, ...) porque son las que ya estaban construidas
    # cuando el cliente era uno solo; son del admin y de nadie más.
    ('/produccion/', (ROL_ADMIN,)),
    ('/calidad/', (ROL_ADMIN,)),
    ('/componentes/', (ROL_ADMIN,)),
    ('/lineas/', (ROL_ADMIN,)),
    ('/usuarios/', (ROL_ADMIN,)),
)


class AccesoPorRolMiddleware:
    """Corta la petición si el rol de la sesión no puede ver esa ruta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        corte = self._revisar(request)

        if corte is not None:
            return corte

        return self.get_response(request)

    def _revisar(self, request):
        ruta = request.path

        if ruta in RUTAS_LIBRES or ruta.startswith(PREFIJOS_LIBRES):
            return None

        if 'token' not in request.session:
            return redirect('login')

        rol = request.session.get('rol')

        if not rol:
            # Sesión vieja, de antes de que el cliente se dividiera en paneles:
            # tiene token pero no rol. Sin rol no hay panel, así que se rearma.
            request.session.flush()
            messages.info(request, 'Vuelve a iniciar sesión.')
            return redirect('login')

        for prefijo, roles in RUTAS_POR_ROL:

            if not ruta.startswith(prefijo):
                continue

            if rol in roles:
                return None

            return self._sin_permiso(request, rol)

        # Ruta sin regla: pedimos sesión (ya se validó arriba) pero no rol.
        return None

    def _sin_permiso(self, request, rol):
        """Regresa al usuario a su propio dashboard, no al login: su sesión es
        válida, lo único que no le corresponde era la URL."""
        destino = panel_inicio(rol)

        if not destino:
            request.session.flush()
            return redirect('login')

        messages.error(request, 'No tienes acceso a esa sección.')
        return redirect(destino)
