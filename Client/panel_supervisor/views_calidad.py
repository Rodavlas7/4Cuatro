"""Inspecciones de calidad, versión del panel de supervisor.
 
El supervisor consulta y registra inspecciones de sus líneas. El panel de
calidad tiene su propia copia en `panel_calidad/views_inspecciones.py` y el de
administrador la suya en la app `calidad/`.
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
from core.roles import ROL_SUPERVISOR
 
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
 
 
class ListaInspecciones(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)
 
    template_name = "panel_supervisor/calidad/inspecciones.html"
 
    def get(self, request):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}
 
        buscar = request.GET.get("buscar", "").strip()
        fecha_inicio = request.GET.get("fecha_inicio", "")
        fecha_fin = request.GET.get("fecha_fin", "")
        page = request.GET.get("page", "1")
 
        params = {"page": page}
 
        if buscar:
            params["buscar"] = buscar
 
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
 
        if fecha_fin:
            params["fecha_fin"] = fecha_fin
 
        response = api_get(
            API_INSPECCION + "Buscar/",
            headers,
            params=params,
        )
 
        # La respuesta ahora viene paginada: {count, next, previous, results}
        data = response.json() if hasattr(response, "json") else response
 
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
            "laptops": get_choices_laptops(token),
            "lineas": get_choices_lineas_produccion(token),
            "resultados": RESULTADO_CHOICES,
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
    roles_permitidos = (ROL_SUPERVISOR,)
 
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
 
        return redirect("panel_supervisor:inspecciones")
 
 
class EditarInspeccion(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)
 
    def post(self, request, numero):
        token = request.session.get("token")
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
 
        return redirect("panel_supervisor:inspecciones")
 
 
class EliminarInspeccion(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)
 
    def post(self, request, numero):
        token = request.session.get("token")
 
        response = requests.delete(
            API_INSPECCION + f"Eliminar/{numero}/",
            headers={"Authorization": f"Bearer {token}"}
        )
 
        if response.status_code == 200:
            messages.success(request, "Inspección eliminada correctamente.")
        else:
            error_data = response.json()
            messages.error(request, error_data.get("mensaje", "No se pudo eliminar la inspección."))
 
        return redirect("panel_supervisor:inspecciones")
 
 
API_EMPLEADOS_CALIDAD = "http://127.0.0.1:8000/api/usuarios/empleados-calidad-por-linea/"
 
 
class EmpleadosCalidadPorLinea(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)
 
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
 