import requests

from django.contrib import messages
from django.shortcuts import render, redirect

API = "http://127.0.0.1:8000/api"


def _headers(request):
    return {"Authorization": f"Bearer {request.session.get('token')}"}


def _mensaje_api(response):
    try:
        datos = response.json()
    except ValueError:
        return "No se pudo comunicar con la API."
    if isinstance(datos, dict):
        if "mensaje" in datos:
            return datos["mensaje"]
        return " | ".join(f"{campo}: {', '.join(errores)}" for campo, errores in datos.items())
    return "Ocurrió un error al procesar la solicitud."



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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('lineas-lista')

    lineas = requests.get(f"{API}/lineas/", headers=headers).json()
    estados = requests.get(f"{API}/lineas/estados/", headers=headers).json()

    return render(
        request,
        "lineas/lista.html",
        {
            "lineas": lineas,
            "estados": estados,
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
            messages.error(request, _mensaje_api(respuesta))

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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('lineas-lista')


def lineaDetalleView(request, codigo):
    """Detalle de una línea con sus estaciones anidadas (usa LineaDetailAPIView)."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)
    linea = requests.get(f"{API}/lineas/{codigo}/", headers=headers).json()

    return render(request, "lineas/linea_detalle.html", {"linea": linea})



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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('estaciones-lista')

    estaciones = requests.get(f"{API}/lineas/estaciones/", headers=headers).json()
    lineas = requests.get(f"{API}/lineas/", headers=headers).json()

    return render(
        request,
        "lineas/estaciones.html",
        {
            "estaciones": estaciones,
            "lineas": lineas,
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
            messages.error(request, _mensaje_api(respuesta))

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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('estaciones-lista')
