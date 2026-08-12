"""Panel del Supervisor (rol SUPER).

Esta carpeta es del equipo que trabaja el panel de supervisor. Las pantallas de
este panel viven aquí (`views_produccion.py`, `views_componentes.py`,
`views_calidad.py`, `forms.py`) y sus plantillas en
`templates/panel_supervisor/`, así que se pueden mover sin pisar los otros
paneles.

El acceso lo cuida `core.middleware.AccesoPorRolMiddleware`: sólo el rol SUPER
entra a /panel/supervisor/.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import generic

from core import lineas as lineas_del_empleado
from core.guards import RolRequeridoMixin, requiere_rol
from core.roles import ROL_SUPERVISOR


class Dashboard(RolRequeridoMixin, generic.View):
    """Portada del panel de supervisor."""

    roles_permitidos = (ROL_SUPERVISOR,)
    template_name = 'panel_supervisor/dashboard.html'

    def get(self, request):
        return render(request, self.template_name)


@requiere_rol(ROL_SUPERVISOR)
def cambiarLineaView(request):
    """Cambia con qué línea está trabajando el supervisor.

    Un supervisor puede tener varias líneas a su cargo (empleado_linea es M a M),
    pero las pantallas muestran una a la vez. El selector del menú manda aquí el
    código de la que quiere ver; core.lineas comprueba que sea suya antes de
    guardarla en la sesión.

    Al terminar se regresa a la pantalla de donde vino, para que cambiar de línea
    no sea también perder el lugar donde estaba."""

    destino = request.POST.get('siguiente')

    if request.method == 'POST':

        codigo = request.POST.get('linea')

        if lineas_del_empleado.elegir(request, codigo):
            messages.success(request, "Ahora estás viendo la línea seleccionada.")
        else:
            messages.error(request, "Esa línea no está a tu cargo.")

    # El destino lo manda el formulario, o sea el navegador. Sólo se acepta si es
    # una ruta de este sitio: si no, con una URL completa ('//otro-sitio.com')
    # esto sería un brinco a donde quiera quien arme la petición.
    if destino and destino.startswith('/') and not destino.startswith('//'):
        return redirect(destino)

    return redirect('panel_supervisor:dashboard')
