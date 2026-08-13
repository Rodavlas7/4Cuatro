
"""Inspecciones de calidad, versión del panel de calidad.
 
Estas pantallas son de este panel. El panel de administrador tiene su propia
copia en la app `calidad/`, y el de supervisor la suya; se pueden cambiar por
separado porque el operador de calidad y el admin no necesitan ver lo mismo.
"""
 
import requests
from datetime import datetime
from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
from django.http import JsonResponse
 
from core.guards import RolRequeridoMixin
 
# Se importa con alias porque las vistas de este módulo tienen su propio
# método get(); un `get` a secas adentro se leería como si fuera el método.
from core.api import get as api_get, lista, objeto
from core.lineas import de_la_sesion
from core.roles import ROL_CALIDAD
 
from .forms import get_choices_laptops, get_choices_lineas_produccion
 
API_INSPECCION = "http://127.0.0.1:8000/api/calidad/Inspeccion/"
 
RESULTADO_CHOICES = [
    ("1", "Aprobada"),
    ("0", "Rechazada"),
    ("2", "Continuar ensamblaje"),
]
 
 
def normalizar_listar(item):
    return {
        "numero": item.get("numero"),
        "resultado": item.get("resultado_nombre"),
        "fecha": item.get("fecha"),
        "hora": item.get("hora"),
        "laptop": item.get("laptop_numero"),
        "num_serie": item.get("laptop_num_serie"),
        "empleado": item.get("empleado_nombre"),
        "linea": item.get("linea_nombre"),
    }


SIN_LINEA = (
    "Tu usuario no tiene una línea asignada, así que no se puede saber qué "
    "inspecciones te tocan. Pídele a un administrador que te asigne a una línea."
)

AJENA = "Esa inspección es de otra línea, no la puedes modificar."


def es_de_mi_linea(request, numero, headers):
    """True si esa inspección es de la línea del operador.

    Editar y borrar van por número y el número viaja en el formulario, así que
    sin esta comprobación bastaría con cambiarlo a mano para tocar una
    inspección de otra línea: justo la que la lista no le deja ver."""
    linea = de_la_sesion(request)

    if not linea:
        return False

    detalle = objeto(api_get(API_INSPECCION + f"Detalle/{numero}/", headers))

    return detalle.get("linea_codigo") == linea["codigo"]


class ListaInspecciones(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_CALIDAD,)
 
    template_name = "panel_calidad/inspecciones.html"
 
    def get(self, request):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}
 
        buscar = request.GET.get("buscar", "").strip()
        fecha_inicio = request.GET.get("fecha_inicio", "")
        fecha_fin = request.GET.get("fecha_fin", "")
        # OJO: "Rechazada" es el código "0". Se compara contra cadena vacía y no
        # con `if resultado:` porque más adelante, si alguien lo convierte a
        # entero, el 0 se volvería falso y el filtro se caería justo en el
        # resultado que más se consulta.
        resultado = request.GET.get("resultado", "")
        page = request.GET.get("page", "1")
 
        # El operador de calidad sólo ve las inspecciones de su línea. La línea
        # sale de empleado_linea, no de un filtro de la pantalla: no es algo que
        # él elija, así que tampoco se le ofrece para cambiarlo.
        linea = de_la_sesion(request)

        data = {}

        if not linea:
            # Sin línea no se filtra por "todas": se enseña vacío. Al revés
            # dejaría ver justo lo que esta pantalla tiene que esconder.
            messages.error(request, SIN_LINEA)
        else:
            params = {"page": page, "linea": linea["codigo"]}

            if buscar:
                params["buscar"] = buscar

            if fecha_inicio:
                params["fecha_inicio"] = fecha_inicio

            if fecha_fin:
                params["fecha_fin"] = fecha_fin

            if resultado != "":
                params["resultado"] = resultado

            # La respuesta viene paginada: {count, next, previous, results}
            data = objeto(api_get(
                API_INSPECCION + "Buscar/",
                headers,
                params=params,
            ))

        items = data.get("results", [])
        inspecciones_base = [normalizar_listar(i) for i in items]
 
        inspecciones = []
        for i in inspecciones_base:
            det_resp = api_get(API_INSPECCION + f"Detalle/{i['numero']}/", headers)
            detalle = objeto(det_resp)
            inspecciones.append({
                **i,
                "resultado_codigo": detalle.get("resultado"),
                "observaciones": detalle.get("observaciones"),
            })
 
        count = data.get("count", 0)
        page_size = 10  # debe coincidir con InspeccionPagination.page_size
        total_pages = max(1, -(-count // page_size))
 
        context = {
            "inspecciones": inspecciones,
            "linea": linea,
            "laptops": get_choices_laptops(token),
            "lineas": get_choices_lineas_produccion(token),
            "resultados": RESULTADO_CHOICES,
            "resultado": resultado,
            "buscar": buscar,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "page_actual": int(page),
            "total_pages": total_pages,
            "has_next": data.get("next") is not None,
            "has_previous": data.get("previous") is not None,
            "total_count": count,
        }
        return render(request, self.template_name, context)
 
 
class CrearInspeccion(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_CALIDAD,)
 
    def post(self, request):
        token = request.session.get("token")
        ahora = datetime.now()
 
        data = {
            "resultado": request.POST.get("resultado"),
            "observaciones": request.POST.get("observaciones"),
            "fecha": ahora.strftime("%Y-%m-%d"),
            "hora": ahora.strftime("%H:%M:%S"),
            "laptop": request.POST.get("laptop"),
            "empleado": request.POST.get("empleado"),
            "linea": request.POST.get("linea"),
        }
 
        response = requests.post(
            API_INSPECCION + "Registrar/",
            headers={"Authorization": f"Bearer {token}"},
            data=data
        )
 
        if response.status_code == 201:
            messages.success(request, "Inspección registrada correctamente.")
        else:
            error_data = response.json()
            mensaje = error_data.get("mensaje") or str(error_data)
            messages.error(request, mensaje)
 
        return redirect("panel_calidad:inspecciones")
 
 
class EditarInspeccion(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_CALIDAD,)
 
    def post(self, request, numero):
        token = request.session.get("token")

        if not es_de_mi_linea(request, numero, {"Authorization": f"Bearer {token}"}):
            messages.error(request, AJENA)
            return redirect("panel_calidad:inspecciones")

        data = {
            "resultado": request.POST.get("resultado"),
            "observaciones": request.POST.get("observaciones"),
        }

        response = requests.patch(
            API_INSPECCION + f"Actualizar/{numero}/",
            headers={"Authorization": f"Bearer {token}"},
            data=data
        )
 
        if response.status_code == 200:
            messages.success(request, "Inspección actualizada correctamente.")
        else:
            error_data = response.json()
            mensaje = error_data.get("mensaje") or str(error_data)
            messages.error(request, mensaje)
 
        return redirect("panel_calidad:inspecciones")
 
 
class EliminarInspeccion(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_CALIDAD,)
 
    def post(self, request, numero):
        token = request.session.get("token")

        if not es_de_mi_linea(request, numero, {"Authorization": f"Bearer {token}"}):
            messages.error(request, AJENA)
            return redirect("panel_calidad:inspecciones")

        response = requests.delete(
            API_INSPECCION + f"Eliminar/{numero}/",
            headers={"Authorization": f"Bearer {token}"}
        )
 
        if response.status_code == 200:
            messages.success(request, "Inspección eliminada correctamente.")
        else:
            error_data = response.json()
            messages.error(request, error_data.get("mensaje", "No se pudo eliminar la inspección."))
 
        return redirect("panel_calidad:inspecciones")
 
 
API_EMPLEADOS_CALIDAD = "http://127.0.0.1:8000/api/usuarios/empleados-calidad-por-linea/"
 
 
class EmpleadosCalidadPorLinea(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_CALIDAD,)
 
    def get(self, request, linea_id):
        token = request.session.get("token")
 
        url = f"{API_EMPLEADOS_CALIDAD}{linea_id}/"
 
        headers = {
            "Authorization": f"Bearer {token}"
        }
 
        try:
            resp = requests.get(url, headers=headers)
 
            if resp.status_code != 200:
                return JsonResponse([], safe=False)
 
            try:
                data = resp.json()
            except Exception:
                return JsonResponse([], safe=False)
 
            return JsonResponse(data, safe=False)
 
        except Exception:
            return JsonResponse([], safe=False)