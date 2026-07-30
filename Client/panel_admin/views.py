"""Panel del Administrador.

Esta carpeta es del equipo que trabaja el panel de administrador. Las pantallas
del admin (producción, calidad, componentes, líneas, personal) viven todavía en
las apps originales del proyecto, porque son las que ya estaban construidas
cuando el cliente era uno solo; se llegan desde el sidebar de este panel.

El acceso lo cuida `core.middleware.AccesoPorRolMiddleware`: sólo el rol ADMIN
entra a /panel/admin/ y a las apps que le pertenecen.
"""

from django.shortcuts import render
from django.views import generic

from core.guards import RolRequeridoMixin
from core.roles import ROL_ADMIN


class Dashboard(RolRequeridoMixin, generic.View):
    """Portada del panel de administrador."""

    roles_permitidos = (ROL_ADMIN,)
    template_name = 'panel_admin/dashboard.html'

    def get(self, request):
        return render(request, self.template_name)
