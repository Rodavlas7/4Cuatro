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
            "tipo": request.POST.get("tipo") or None,
            "estado": request.POST.get("estado") or None,
            "activo": request.POST.get("activo") == "on",
        }

        respuesta = requests.post(f"{API}/lineas/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            datos = respuesta.json()
            codigo = datos.get("codigo") or datos.get("id")
            if codigo:
                messages.success(request, f"Línea registrada correctamente. Código: {codigo}")
            else:
                messages.success(request, "Línea registrada correctamente.")
        else:
            messages.error(request, mensaje_error(respuesta))

        return redirect('lineas-lista')

    respuesta_lineas = get(f"{API}/lineas/", headers)
    respuesta_estados = get(f"{API}/lineas/estados/", headers)
    respuesta_tipos = get(f"{API}/lineas/tipos/", headers)

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
            "tipos": lista(respuesta_tipos),
        }
    )


def lineaEditarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "codigo": codigo,
            "nombre": request.POST.get("nombre") or None,
            "descripcion": request.POST.get("descripcion") or None,
            "tipo": request.POST.get("tipo") or None,
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
    """Detalle de una línea con sus estaciones y sus supervisores."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)
    respuesta = get(f"{API}/lineas/{codigo}/", headers)

    # En un detalle no hay nada que pintar si la API falla: una pantalla de
    # campos en blanco confunde más que regresar a la lista con el motivo.
    if fallo(respuesta):
        messages.error(request, f"No se pudo cargar la línea {codigo}. {mensaje_error(respuesta)}")
        return redirect('lineas-lista')

    # Los supervisores van aparte porque salen de empleado_linea, no de la vista
    # de líneas. El endpoint devuelve en una sola llamada los que ya están
    # asignados y los que se pueden asignar, que es justo lo que pide la
    # pantalla: la tabla y el select del modal.
    respuesta_supervisores = get(f"{API}/lineas/{codigo}/supervisores/", headers)

    if fallo(respuesta_supervisores):
        messages.error(
            request,
            f"No se pudieron cargar los supervisores de la línea. {mensaje_error(respuesta_supervisores)}"
        )

    supervisores = objeto(respuesta_supervisores)

    return render(
        request,
        "lineas/linea_detalle.html",
        {
            "linea": objeto(respuesta),
            "supervisores": supervisores.get("asignados") or [],
            "supervisores_disponibles": supervisores.get("disponibles") or [],
        }
    )



# SUPERVISORES DE LA LINEA
#
# Se guardan en empleado_linea y la relación es M a M: una línea puede tener
# varios supervisores y un supervisor puede llevar varias líneas. Por eso
# asignar no reemplaza nada: agrega. Para dejar sin supervisor a una línea hay
# que quitarlo aquí a propósito.


def lineaSupervisorAsignarView(request, codigo):

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        empleado = request.POST.get("empleado")

        if not empleado:
            messages.error(request, "Selecciona un supervisor.")
            return redirect('linea-detalle', codigo=codigo)

        respuesta = requests.post(
            f"{API}/lineas/{codigo}/supervisores/",
            json={"empleado": empleado},
            headers=headers
        )

        if respuesta.status_code == 201:
            messages.success(request, "Supervisor asignado a la línea.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('linea-detalle', codigo=codigo)


def lineaSupervisorQuitarView(request, codigo, numero):
    """Quitar no borra el renglón: la API le pone fecha_fin y queda de historial."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/lineas/{codigo}/supervisores/{numero}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, "Supervisor quitado de la línea.")
        else:
            messages.error(request, mensaje_error(respuesta))

    return redirect('linea-detalle', codigo=codigo)



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
            datos = respuesta.json()
            codigo = datos.get("codigo") or datos.get("id")
            if codigo:
                messages.success(request, f"Estación registrada correctamente. Código: {codigo}")
            else:
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
            "codigo": codigo,
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
