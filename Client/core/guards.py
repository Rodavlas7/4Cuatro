"""Guardas de rol para vistas.

El bloqueo de fondo lo hace `core.middleware.AccesoPorRolMiddleware`, que trabaja
por prefijo de URL y cubre paneles completos. Estas guardas son para el caso más
fino: una vista suelta dentro de un panel que además quieres abrir a otro rol, o
cerrar a uno.

    # Vista función
    @requiere_rol(ROL_ADMIN, ROL_SUPERVISOR)
    def miVista(request):
        ...

    # Vista de clase
    class MiVista(RolRequeridoMixin, generic.View):
        roles_permitidos = (ROL_ADMIN,)

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .roles import panel_inicio


def _respuesta_sin_permiso(request, rol):
    """A dónde mandar a alguien que sí entró pero no a este lugar.

    Se le regresa a su propio dashboard, no al login: la sesión es válida, lo
    único inválido era la URL. Sacarlo al login parecería que expiró."""
    destino = panel_inicio(rol)

    if not destino:
        # Rol desconocido: no hay panel al que devolverlo, así que fuera.
        request.session.flush()
        return redirect('login')

    messages.error(request, 'No tienes acceso a esa sección.')
    return redirect(destino)


def _verificar(request, roles_permitidos):
    """Revisa sesión y rol. Devuelve una redirección si hay que cortar, o None.

    Se pide token Y rol: una sesión creada antes de que existieran los paneles
    trae token pero no rol, y sin rol no se puede decidir nada. En ese caso se
    manda a iniciar sesión otra vez para que la sesión se rearme completa."""
    if 'token' not in request.session:
        return redirect('login')

    rol = request.session.get('rol')

    if not rol:
        request.session.flush()
        messages.info(request, 'Vuelve a iniciar sesión.')
        return redirect('login')

    if roles_permitidos and rol not in roles_permitidos:
        return _respuesta_sin_permiso(request, rol)

    return None


def requiere_rol(*roles_permitidos):
    """Decorador para vistas función: sólo deja pasar los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            corte = _verificar(request, roles_permitidos)

            if corte is not None:
                return corte

            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


class RolRequeridoMixin:
    """Mixin para vistas de clase. Se declara `roles_permitidos` en la clase.

    Va antes que la vista genérica en la lista de bases para que su dispatch
    corra primero."""

    roles_permitidos = ()

    def dispatch(self, request, *args, **kwargs):
        corte = _verificar(request, self.roles_permitidos)

        if corte is not None:
            return corte

        return super().dispatch(request, *args, **kwargs)
