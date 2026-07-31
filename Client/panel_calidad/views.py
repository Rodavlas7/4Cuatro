"""Panel del Operador de Calidad (rol OPCALI).

Esta carpeta es del equipo que trabaja el panel de calidad. Las pantallas de
este panel viven aquí (`views_inspecciones.py`, `forms.py`) y sus plantillas en
`templates/panel_calidad/`, así que se pueden mover sin pisar los otros paneles.

El acceso lo cuida `core.middleware.AccesoPorRolMiddleware`: sólo el rol OPCALI
entra a /panel/calidad/.
"""

from django.shortcuts import render
from django.views import generic

from core.guards import RolRequeridoMixin
from core.roles import ROL_CALIDAD


class Dashboard(RolRequeridoMixin, generic.View):
    """Portada del panel de calidad."""

    roles_permitidos = (ROL_CALIDAD,)
    template_name = 'panel_calidad/dashboard.html'

    def get(self, request):
        return render(request, self.template_name)
