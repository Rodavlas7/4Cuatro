import requests
from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

# Asumimos que tienes estas funciones importadas desde core, tal como en tu ejemplo.
from core.api import get 
from core.templatetags.formato import fecha_hora

API = "http://127.0.0.1:8000/api"

def _json(url, headers, params=None):
    respuesta = get(url, headers, params=params)
    if respuesta is None or respuesta.status_code != 200:
        return None
    try:
        return respuesta.json()
    except ValueError:
        return None

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
        return " | ".join(f"{campo}: {', '.join(map(str, errores))}"
                          for campo, errores in datos.items())
    return "Ocurrió un error al procesar la solicitud."


def _filtrar_embalajes(embalajes, filtros):
    """Filtra la lista de embalajes en memoria según los parámetros del GET."""
    resultado = embalajes

    # Filtro Rango de Fechas
    fecha_inicio = filtros.get("fecha_inicio")
    if fecha_inicio:
        resultado = [e for e in resultado if str(e.get("fecha") or "") >= fecha_inicio]

    fecha_fin = filtros.get("fecha_fin")
    if fecha_fin:
        resultado = [e for e in resultado if str(e.get("fecha") or "") <= fecha_fin]

    # Filtro de Búsqueda de texto
    buscar = (filtros.get("buscar") or "").strip().lower()
    if buscar:
        resultado = [e for e in resultado
                     if buscar in str(e.get("numero") or "")
                     or buscar in str(e.get("laptop_num_serie") or "").lower()
                     or buscar in str(e.get("tipo_nombre") or "").lower()
                     or buscar in str(e.get("tipo_codigo") or "").lower()]

    return resultado

# ------------------------------------------------------------------
# VISTA PRINCIPAL DE EMBALAJE
# ------------------------------------------------------------------
def embalajeListarView(request):
    """Consulta general de registros de embalaje y alta de uno nuevo."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    # ------------------------------------------------------------------ POST
    if request.method == "POST":
        laptop = request.POST.get("laptop")
        tipo = request.POST.get("tipo")

        if not laptop or not tipo:
            messages.error(request, "Selecciona la laptop y el tipo de embalaje.")
            return redirect('embalaje-lista')

        ahora = datetime.now()
        fecha_hoy = ahora.date().isoformat()
        hora_ahora = ahora.strftime("%H:%M:%S")

        payload = {
            "laptop": laptop,
            "tipo": tipo,
            "fecha": fecha_hoy,
            "hora": hora_ahora
        }

        respuesta = requests.post(
            f"{API}/embalaje/Embalaje/Registrar/", 
            json=payload, 
            headers=headers
        )

        if respuesta.status_code == 201:
            numero = respuesta.json().get("numero", "")
            messages.success(request, f"Embalaje #{numero} registrado correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

        return redirect('embalaje-lista')

    # ------------------------------------------------------------------- GET
    embalajes_crudos = _json(f"{API}/embalaje/Embalaje/Listar/", headers)
    embalajes_crudos = embalajes_crudos if isinstance(embalajes_crudos, list) else []

    filtros = {
        "buscar": request.GET.get("buscar") or "",
        "fecha_inicio": request.GET.get("fecha_inicio") or "",
        "fecha_fin": request.GET.get("fecha_fin") or "",
    }

    embalajes_filtrados = _filtrar_embalajes(embalajes_crudos, filtros)

    laptops = _json(f"{API}/embalaje/Embalaje/Auxiliares/LaptopsDisponibles/", headers)
    tipos = _json(f"{API}/embalaje/Embalaje/Auxiliares/TiposEmbalaje/", headers)

    return render(
        request,
        "embalaje/embalaje_lista.html",
        {
            "embalajes": embalajes_filtrados,
            "laptops": laptops if isinstance(laptops, list) else [],
            "tipos": tipos if isinstance(tipos, list) else [],
            "buscar": filtros["buscar"],
            "fecha_inicio": filtros["fecha_inicio"],
            "fecha_fin": filtros["fecha_fin"],
        }
    )


def embalajeEditarView(request, numero):
    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":
        headers = _headers(request)
        tipo = request.POST.get("tipo")

        if not tipo:
            messages.error(request, "Selecciona un tipo de embalaje válido.")
            return redirect('embalaje-lista')

        payload = {"tipo": tipo}
        respuesta = requests.put(
            f"{API}/embalaje/Embalaje/Actualizar/{numero}/", 
            json=payload, 
            headers=headers
        )

        if respuesta.status_code in (200, 202):
            messages.success(request, f"Embalaje #{numero} actualizado correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('embalaje-lista')