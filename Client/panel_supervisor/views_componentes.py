"""Materiales, versión del panel de supervisor.

Componentes, modelos, lotes y órdenes de material. El panel de administrador
tiene su propia copia en la app `componentes/`; ésta se puede cambiar sin
afectarla.
"""

import requests

from django.contrib import messages
from django.shortcuts import render, redirect

from core.api import fallo, get, lista, mensaje_error, objeto
from core.guards import requiere_rol
from core.roles import ROL_SUPERVISOR

# URL base de la API (Servicios). Igual que en home/views.py.
API = "http://127.0.0.1:8000/api"


def _headers(request):
    return {"Authorization": f"Bearer {request.session.get('token')}"}


def _avisar_si_falla(request, respuesta, que):
    """Avisa al usuario cuando la API no entregó los datos.

    Sin esto la pantalla se ve vacía y parece que no hay registros dados de alta,
    cuando en realidad la sesión venció o la API está caída."""
    if fallo(respuesta):
        messages.error(request, f"No se pudieron cargar {que}. {mensaje_error(respuesta)}")


#COMPONENTES

@requiere_rol(ROL_SUPERVISOR)
def componentesListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "num_serie": request.POST.get("num_serie") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "linea": request.POST.get("linea") or None,
            "modelo": request.POST.get("modelo") or None,
            "lote": request.POST.get("lote") or None,
            "estado": request.POST.get("estado") or None,
            "orden_material": request.POST.get("orden_material") or None,
            "registro_ensamblaje": request.POST.get("registro_ensamblaje") or None,
        }

        respuesta = requests.post(f"{API}/componentes/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Componente registrado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('panel_supervisor:componentes-lista')

    respuesta_componentes = get(f"{API}/componentes/", headers)

    _avisar_si_falla(request, respuesta_componentes, "los componentes")

    return render(
        request,
        "panel_supervisor/componentes/lista.html",
        {
            "componentes": lista(respuesta_componentes),
            "lineas": lista(get(f"{API}/lineas/", headers)),
            "modelos": lista(get(f"{API}/componentes/modelos/", headers)),
            "lotes": lista(get(f"{API}/componentes/lotes/", headers)),
            "estados": lista(get(f"{API}/componentes/estados/", headers)),
        }
    )


@requiere_rol(ROL_SUPERVISOR)
def componenteEditarView(request, numero):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "num_serie": request.POST.get("num_serie") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "linea": request.POST.get("linea") or None,
            "modelo": request.POST.get("modelo") or None,
            "lote": request.POST.get("lote") or None,
            "estado": request.POST.get("estado") or None,
            "orden_material": request.POST.get("orden_material") or None,
            "registro_ensamblaje": request.POST.get("registro_ensamblaje") or None,
        }

        respuesta = requests.put(f"{API}/componentes/mod/{numero}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Componente actualizado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:componentes-lista')


@requiere_rol(ROL_SUPERVISOR)
def componenteBajaView(request, numero):
    """El DELETE de la API no borra el registro: lo marca como Mermado."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/mod/{numero}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Componente marcado como Mermado.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:componentes-lista')



# MODELOS DE COMPONENTE


@requiere_rol(ROL_SUPERVISOR)
def modelosListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "codigo": request.POST.get("codigo"),
            "nombre": request.POST.get("nombre") or None,
            "tipo_componente": request.POST.get("tipo_componente") or None,
            "fabricante": request.POST.get("fabricante") or None,
        }

        respuesta = requests.post(f"{API}/componentes/modelos/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Modelo de componente registrado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('panel_supervisor:modelos-lista')

    respuesta_modelos = get(f"{API}/componentes/modelos/", headers)

    _avisar_si_falla(request, respuesta_modelos, "los modelos")

    return render(
        request,
        "panel_supervisor/componentes/modelos.html",
        {
            "modelos": lista(respuesta_modelos),
            "tipos": lista(get(f"{API}/componentes/tipos/", headers)),
        }
    )


@requiere_rol(ROL_SUPERVISOR)
def modeloEditarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "nombre": request.POST.get("nombre") or None,
            "tipo_componente": request.POST.get("tipo_componente") or None,
            "fabricante": request.POST.get("fabricante") or None,
        }

        respuesta = requests.put(f"{API}/componentes/modelos/mod/{codigo}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Modelo actualizado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:modelos-lista')


@requiere_rol(ROL_SUPERVISOR)
def modeloEliminarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/modelos/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Modelo eliminado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:modelos-lista')


# LOTES DE COMPONENTE

@requiere_rol(ROL_SUPERVISOR)
def lotesListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "codigo": request.POST.get("codigo"),
            "descripcion": request.POST.get("descripcion") or None,
        }

        respuesta = requests.post(f"{API}/componentes/lotes/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Lote registrado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('panel_supervisor:lotes-lista')

    respuesta_lotes = get(f"{API}/componentes/lotes/", headers)

    _avisar_si_falla(request, respuesta_lotes, "los lotes")

    return render(request, "panel_supervisor/componentes/lotes.html", {"lotes": lista(respuesta_lotes)})


@requiere_rol(ROL_SUPERVISOR)
def loteEditarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        payload = {"descripcion": request.POST.get("descripcion") or None}

        respuesta = requests.put(f"{API}/componentes/lotes/mod/{codigo}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Lote actualizado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:lotes-lista')


@requiere_rol(ROL_SUPERVISOR)
def loteEliminarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/lotes/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Lote eliminado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:lotes-lista')


#  ORDENES DE MATERIAL

@requiere_rol(ROL_SUPERVISOR)
def ordenesListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "fecha": request.POST.get("fecha") or None,
            "hora": request.POST.get("hora") or None,
            "linea": request.POST.get("linea") or None,
        }

        respuesta = requests.post(f"{API}/componentes/ordenes/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Orden de material registrada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('panel_supervisor:ordenes-lista')

    respuesta_ordenes = get(f"{API}/componentes/ordenes/", headers)

    _avisar_si_falla(request, respuesta_ordenes, "las órdenes de material")

    return render(
        request,
        "panel_supervisor/componentes/ordenes.html",
        {
            "ordenes": lista(respuesta_ordenes),
            "lineas": lista(get(f"{API}/lineas/", headers)),
        }
    )


@requiere_rol(ROL_SUPERVISOR)
def ordenEditarView(request, numero):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "fecha": request.POST.get("fecha") or None,
            "hora": request.POST.get("hora") or None,
            "linea": request.POST.get("linea") or None,
        }

        respuesta = requests.put(f"{API}/componentes/ordenes/mod/{numero}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Orden actualizada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:ordenes-lista')


@requiere_rol(ROL_SUPERVISOR)
def ordenEliminarView(request, numero):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/ordenes/mod/{numero}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Orden eliminada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:ordenes-lista')


@requiere_rol(ROL_SUPERVISOR)
def ordenDetalleView(request, numero):
    """Renglones (detalle_material) de una orden de material."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "orden": numero,
            "modelo": request.POST.get("modelo") or None,
            "cantidad": request.POST.get("cantidad") or None,
        }

        respuesta = requests.post(f"{API}/componentes/detalles/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Renglón agregado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('panel_supervisor:orden-detalle', numero=numero)

    respuesta_orden = get(f"{API}/componentes/ordenes/{numero}/", headers)

    # En un detalle no hay nada que pintar si la API falla: se regresa a la lista
    # con el motivo en lugar de una pantalla de campos en blanco.
    if fallo(respuesta_orden):
        messages.error(request, f"No se pudo cargar la orden {numero}. {mensaje_error(respuesta_orden)}")
        return redirect('panel_supervisor:ordenes-lista')

    return render(
        request,
        "panel_supervisor/componentes/orden_detalle.html",
        {
            "orden": objeto(respuesta_orden),
            "modelos": lista(get(f"{API}/componentes/modelos/", headers)),
        }
    )


@requiere_rol(ROL_SUPERVISOR)
def renglonEliminarView(request, numero, modelo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/detalles/mod/{numero}/{modelo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Renglón eliminado correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('panel_supervisor:orden-detalle', numero=numero)



