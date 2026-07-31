"""Panel del Supervisor (rol SUPER).

Esta carpeta es del equipo que trabaja el panel de supervisor. Las pantallas de
este panel viven aquí (`views_produccion.py`, `views_componentes.py`,
`views_calidad.py`, `forms.py`) y sus plantillas en
`templates/panel_supervisor/`, así que se pueden mover sin pisar los otros
paneles.

El acceso lo cuida `core.middleware.AccesoPorRolMiddleware`: sólo el rol SUPER
entra a /panel/supervisor/.
"""

from django.shortcuts import render
from django.views import generic

from core.guards import RolRequeridoMixin
from core.roles import ROL_SUPERVISOR


class Dashboard(RolRequeridoMixin, generic.View):
    """Portada del panel de supervisor."""

    roles_permitidos = (ROL_SUPERVISOR,)
    template_name = 'panel_supervisor/dashboard.html'

    def get(self, request):
        return render(request, self.template_name)
