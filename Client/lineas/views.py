import requests

from django.contrib import messages
from django.shortcuts import render, redirect

from core.api import fallo, get, lista, mensaje_error, objeto

API = "http://127.0.0.1:8000/api"


def _headers(request):
    return {"Authorization": f"Bearer {request.session.get('token')}"}



#  LINEAS DE ENSAMBLAJE


def lineasListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "codigo": request.POST.get("codigo"),
            "nombre": request.POST.get("nombre") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "estado": request.POST.get("estado") or None,
            "activo": request.POST.get("activo") == "on",
        }

        respuesta = requests.post(f"{API}/lineas/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Línea registrada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('lineas-lista')

    respuesta_lineas = get(f"{API}/lineas/", headers)
    respuesta_estados = get(f"{API}/lineas/estados/", headers)

    # Si la API falla se pinta la tabla vacía, pero avisando por qué: una lista
    # en blanco y sin explicación se confunde con "no hay líneas dadas de alta".
    if fallo(respuesta_lineas):
        messages.error(request, f"No se pudieron cargar las líneas. {mensaje_error(respuesta_lineas)}")

    return render(
        request,
        "lineas/lista.html",
        {
            "lineas": lista(respuesta_lineas),
            "estados": lista(respuesta_estados),
        }
    )


def lineaEditarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "nombre": request.POST.get("nombre") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "estado": request.POST.get("estado") or None,
            "activo": request.POST.get("activo") == "on",
        }

        respuesta = requests.put(f"{API}/lineas/mod/{codigo}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Línea actualizada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('lineas-lista')


def lineaBajaView(request, codigo):
    """El DELETE de la API no borra el registro: desactiva la línea (activo=False)."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/lineas/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Línea desactivada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('lineas-lista')


def lineaDetalleView(request, codigo):
    """Detalle de una línea con sus estaciones anidadas (usa LineaDetailAPIView)."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)
    respuesta = get(f"{API}/lineas/{codigo}/", headers)

    # En un detalle no hay nada que pintar si la API falla: una pantalla de
    # campos en blanco confunde más que regresar a la lista con el motivo.
    if fallo(respuesta):
        messages.error(request, f"No se pudo cargar la línea {codigo}. {mensaje_error(respuesta)}")
        return redirect('lineas-lista')

    return render(request, "lineas/linea_detalle.html", {"linea": objeto(respuesta)})



# ESTACIONES DE TRABAJO

def estacionesListView(request):

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "codigo": request.POST.get("codigo"),
            "nombre": request.POST.get("nombre") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "linea": request.POST.get("linea") or None,
            "activo": request.POST.get("activo") == "on",
        }

        respuesta = requests.post(f"{API}/lineas/estaciones/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Estación registrada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('estaciones-lista')

    respuesta_estaciones = get(f"{API}/lineas/estaciones/", headers)
    respuesta_lineas = get(f"{API}/lineas/", headers)

    if fallo(respuesta_estaciones):
        messages.error(request, f"No se pudieron cargar las estaciones. {mensaje_error(respuesta_estaciones)}")

    return render(
        request,
        "lineas/estaciones.html",
        {
            "estaciones": lista(respuesta_estaciones),
            "lineas": lista(respuesta_lineas),
        }
    )


def estacionEditarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "nombre": request.POST.get("nombre") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "linea": request.POST.get("linea") or None,
            "activo": request.POST.get("activo") == "on",
        }

        respuesta = requests.put(f"{API}/lineas/estaciones/mod/{codigo}/", json=payload, headers=headers)

        if respuesta.status_code == 200:
            messages.success(request, "Estación actualizada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('estaciones-lista')


def estacionBajaView(request, codigo):
    """El DELETE de la API no borra el registro: desactiva la estación (activo=False)."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/lineas/estaciones/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Estación desactivada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('estaciones-lista')
