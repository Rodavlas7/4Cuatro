import requests

from django.contrib import messages
from django.shortcuts import render, redirect
# Create your views here.

# URL base de la API (Servicios). Igual que en home/views.py.
API = "http://127.0.0.1:8000/api"


def _headers(request):
    return {"Authorization": f"Bearer {request.session.get('token')}"}


def _mensaje_api(response):
    """Intenta sacar el mensaje de error que manda la API; si no puede, uno genérico."""
    try:
        datos = response.json()
    except ValueError:
        return "No se pudo comunicar con la API."
    if isinstance(datos, dict):
        if "mensaje" in datos:
            return datos["mensaje"]
        # errores de validación de DRF: {"campo": ["mensaje", ...]}
        return " | ".join(f"{campo}: {', '.join(errores)}" for campo, errores in datos.items())
    return "Ocurrió un error al procesar la solicitud."


#COMPONENTES

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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('componentes-lista')

    componentes = requests.get(f"{API}/componentes/", headers=headers).json()
    lineas = requests.get(f"{API}/lineas/", headers=headers).json()
    modelos = requests.get(f"{API}/componentes/modelos/", headers=headers).json()
    lotes = requests.get(f"{API}/componentes/lotes/", headers=headers).json()
    estados = requests.get(f"{API}/componentes/estados/", headers=headers).json()

    return render(
        request,
        "componentes/lista.html",
        {
            "componentes": componentes,
            "lineas": lineas,
            "modelos": modelos,
            "lotes": lotes,
            "estados": estados,
        }
    )


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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('componentes-lista')


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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('componentes-lista')



# MODELOS DE COMPONENTE


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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('modelos-lista')

    modelos = requests.get(f"{API}/componentes/modelos/", headers=headers).json()
    tipos = requests.get(f"{API}/componentes/tipos/", headers=headers).json()

    return render(
        request,
        "componentes/modelos.html",
        {
            "modelos": modelos,
            "tipos": tipos,
        }
    )


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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('modelos-lista')


def modeloEliminarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/modelos/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Modelo eliminado correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('modelos-lista')


# LOTES DE COMPONENTE

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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('lotes-lista')

    lotes = requests.get(f"{API}/componentes/lotes/", headers=headers).json()

    return render(request, "componentes/lotes.html", {"lotes": lotes})


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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('lotes-lista')


def loteEliminarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/lotes/mod/{codigo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Lote eliminado correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('lotes-lista')


#  ORDENES DE MATERIAL

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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('ordenes-lista')

    ordenes = requests.get(f"{API}/componentes/ordenes/", headers=headers).json()
    lineas = requests.get(f"{API}/lineas/", headers=headers).json()

    return render(
        request,
        "componentes/ordenes.html",
        {
            "ordenes": ordenes,
            "lineas": lineas,
        }
    )


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
            messages.error(request, _mensaje_api(respuesta))

    return redirect('ordenes-lista')


def ordenEliminarView(request, numero):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/ordenes/mod/{numero}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Orden eliminada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('ordenes-lista')


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
            messages.error(request, _mensaje_api(respuesta))

        return redirect('orden-detalle', numero=numero)

    orden = requests.get(f"{API}/componentes/ordenes/{numero}/", headers=headers).json()
    modelos = requests.get(f"{API}/componentes/modelos/", headers=headers).json()

    return render(
        request,
        "componentes/orden_detalle.html",
        {
            "orden": orden,
            "modelos": modelos,
        }
    )


def renglonEliminarView(request, numero, modelo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/componentes/detalles/mod/{numero}/{modelo}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Renglón eliminado correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('orden-detalle', numero=numero)



