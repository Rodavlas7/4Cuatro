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
    
    # --- INICIO BLOQUE DEBUG ---
    print("\n--- DEBUG API EMBALAJE ---")
    url_prueba = f"{API}/embalaje/Embalaje/Listar/"
    print(f"Llamando a: {url_prueba}")
    
    respuesta_prueba = get(url_prueba, headers)
    if respuesta_prueba is not None:
        print(f"Status Code: {respuesta_prueba.status_code}")
        try:
            datos_json = respuesta_prueba.json()
            print(f"Tipo de dato recibido: {type(datos_json)}")
            if isinstance(datos_json, dict):
                print(f"Llaves del diccionario: {datos_json.keys()}")
        except ValueError:
            print("El resultado no es un JSON válido.")
    else:
        print("La función get() devolvió None. Revisa si el servidor backend está encendido y accesible.")
    print("--------------------------\n")
    # --- FIN BLOQUE DEBUG ---

    embalajes = _json(f"{API}/embalaje/Embalaje/Listar/", headers)
    laptops = _json(f"{API}/embalaje/Embalaje/Auxiliares/LaptopsDisponibles/", headers)
    tipos = _json(f"{API}/embalaje/Embalaje/Auxiliares/TiposEmbalaje/", headers)

    return render(
        request,
        "embalaje/embalaje_lista.html",
        {
            "embalajes": embalajes if isinstance(embalajes, list) else [],
            "laptops": laptops if isinstance(laptops, list) else [],
            "tipos": tipos if isinstance(tipos, list) else [],
        }
    )