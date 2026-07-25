import requests

from datetime import datetime

from django.contrib import messages
from django.shortcuts import render, redirect

# URL base de la API (Servicios). Igual que en home/views.py y componentes/views.py.
API = "http://127.0.0.1:8000/api"

# Estados de laptop que YA no admiten registrar ensamblaje:
# EMBALA = Embalada, APROV = Aprobada (ya pasó calidad, va camino a embalaje).
ESTADOS_LAPTOP_EXCLUIDOS = {"EMBALA", "APROV"}

# Estados de componente.
EDO_COMP_DISPONIBLE = "EDC001"
EDO_COMP_EN_USO = "EDC002"


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
        return " | ".join(f"{campo}: {', '.join(map(str, errores))}"
                          for campo, errores in datos.items())
    return "Ocurrió un error al procesar la solicitud."


def _laptops_disponibles(headers):
    """Laptops que todavía pueden recibir ensamblaje (no embaladas ni ya aprobadas)."""
    laptops = requests.get(f"{API}/produccion/laptops/", headers=headers).json()
    if not isinstance(laptops, list):
        return []
    return [l for l in laptops
            if l.get("estado_codigo") not in ESTADOS_LAPTOP_EXCLUIDOS]


def _bom(headers, modelo_laptop):
    """Filas de modelo_laptop_componente para un modelo de laptop."""
    detalle = requests.get(
        f"{API}/produccion/modelos/{modelo_laptop}/",
        headers=headers,
    ).json()
    return detalle.get("componentes", []) if isinstance(detalle, dict) else []


def _capacidad_por_tipo(filas_bom):
    """Ranuras disponibles POR TIPO (no por modelo). Una laptop con 1 socket de
    procesador lleva UN procesador, sin importar cuántos modelos sean compatibles."""
    caps = {}
    for fila in filas_bom:
        tipo = fila.get("componente_tipo")
        caps[tipo] = max(caps.get(tipo, 0), fila.get("capacidad") or 1)
    return caps


def _todos_los_componentes(headers):
    comps = requests.get(f"{API}/componentes/", headers=headers).json()
    return comps if isinstance(comps, list) else []


def _componentes_libres(comps, linea=None):
    """Componentes físicos Disponibles y sin ensamblaje asignado, agrupados por
    modelo de componente. Si se pasa `linea`, solo cuenta el stock DE ESA LÍNEA:
    cada línea surte únicamente los tipos que sus estaciones instalan."""
    libres = {}
    for c in comps:
        if c.get("estado_codigo") != EDO_COMP_DISPONIBLE:
            continue
        if c.get("registro_ensamblaje"):
            continue
        if linea and c.get("linea_codigo") != linea:
            continue
        libres.setdefault(c.get("modelo_codigo"), []).append(c)
    return libres


def _registro_abierto(headers, laptop):
    """El ensamblaje SIN TERMINAR (sin fecha_fin) de esa laptop, si existe.
    Se reutiliza en vez de abrir uno nuevo en cada registro parcial."""
    regs = requests.get(f"{API}/produccion/registros-ensamblaje/", headers=headers).json()
    if not isinstance(regs, list):
        return None
    abiertos = [r for r in regs
                if str(r.get("laptop")) == str(laptop) and not r.get("fecha_fin")]
    return abiertos[-1] if abiertos else None


def _montado_por_modelo(comps, numero_registro):
    """Cuántas piezas de cada modelo ya están montadas en ese ensamblaje."""
    montado = {}
    if not numero_registro:
        return montado
    for c in comps:
        if str(c.get("registro_ensamblaje")) == str(numero_registro):
            modelo = c.get("modelo_codigo")
            montado[modelo] = montado.get(modelo, 0) + 1
    return montado


def ensamblajeRegistrarView(request):
    """Registra un ensamblaje: se elige línea y laptop y, según su modelo, se
    marcan los componentes compatibles (tabla modelo_laptop_componente) con la
    cantidad que lleva cada uno, sin pasarse de la capacidad POR TIPO.

    El ensamblaje abierto de la laptop se reutiliza; su fecha/hora de inicio se
    inicializan en el primer registro. Con el botón "Registrar y Terminar" se
    guarda además el timestamp de fin."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    # ------------------------------------------------------------------ POST
    if request.method == "POST":

        laptop = request.POST.get("laptop")
        linea = request.POST.get("linea") or None
        terminar = request.POST.get("accion") == "terminar"

        if not laptop:
            messages.error(request, "Selecciona una laptop.")
            return redirect('ensamblaje-registrar')

        # La línea define de qué stock se surte el ensamblaje, así que es obligatoria.
        if not linea:
            messages.error(request, "Selecciona la línea en la que se ensambla.")
            return redirect('ensamblaje-registrar')

        laptop_obj = next(
            (l for l in _laptops_disponibles(headers) if str(l.get("numero")) == str(laptop)),
            None
        )
        if not laptop_obj:
            messages.error(request, "Esa laptop ya no está disponible para ensamblaje.")
            return redirect('ensamblaje-registrar')

        filas_bom = _bom(headers, laptop_obj.get("modelo_codigo"))
        tipo_de = {f.get("componente_codigo"): f.get("componente_tipo") for f in filas_bom}
        nombre_tipo = {f.get("componente_tipo"): f.get("componente_tipo_nombre") for f in filas_bom}
        cap_tipo = _capacidad_por_tipo(filas_bom)

        comps = _todos_los_componentes(headers)
        registro = _registro_abierto(headers, laptop)
        ya_montado = _montado_por_modelo(comps, registro.get("numero") if registro else None)

        # Lo que se marcó en el formulario.
        seleccion = {}
        for clave in request.POST:
            if not clave.startswith("comp_"):
                continue
            codigo_modelo = clave[len("comp_"):]
            try:
                seleccion[codigo_modelo] = int(request.POST.get(f"cant_{codigo_modelo}") or 1)
            except ValueError:
                seleccion[codigo_modelo] = 1

        # Validar ANTES de tocar nada: lo ya montado + lo nuevo no puede pasar las
        # ranuras del TIPO. Se revisa aquí porque el JS del navegador se puede saltar.
        usado_por_tipo = {}
        for codigo_modelo, cantidad in list(ya_montado.items()):
            usado_por_tipo[tipo_de.get(codigo_modelo)] = \
                usado_por_tipo.get(tipo_de.get(codigo_modelo), 0) + cantidad
        for codigo_modelo, cantidad in seleccion.items():
            tipo = tipo_de.get(codigo_modelo)
            usado_por_tipo[tipo] = usado_por_tipo.get(tipo, 0) + cantidad

        excedidos = [
            f"{nombre_tipo.get(t) or t}: {usado} de {cap_tipo.get(t, 1)} permitido(s)"
            for t, usado in usado_por_tipo.items()
            if usado > cap_tipo.get(t, 1)
        ]
        if excedidos:
            messages.error(
                request,
                "No se registró: se excede la capacidad por tipo — " + "; ".join(excedidos)
            )
            return redirect('ensamblaje-registrar')

        ahora = datetime.now()
        fecha_hoy = ahora.date().isoformat()
        hora_ahora = ahora.strftime("%H:%M:%S")

        # 1) Reutilizar el ensamblaje abierto o abrir uno nuevo.
        if registro:
            numero_registro = registro.get("numero")
            # Si venía sin inicio, se inicializa ahora (este es su primer ensamblaje).
            parches = {}
            if not registro.get("fecha_inicio"):
                parches["fecha_inicio"] = fecha_hoy
            if not registro.get("hora_inicio"):
                parches["hora_inicio"] = hora_ahora
            if parches:
                requests.patch(
                    f"{API}/produccion/registros-ensamblaje/mod/{numero_registro}/",
                    json=parches, headers=headers,
                )
        else:
            respuesta = requests.post(
                f"{API}/produccion/registros-ensamblaje/",
                json={
                    "laptop": laptop,
                    "linea": linea,
                    "fecha_inicio": fecha_hoy,
                    "hora_inicio": hora_ahora,
                },
                headers=headers,
            )
            if respuesta.status_code not in (200, 201):
                messages.error(request, _mensaje_api(respuesta))
                return redirect('ensamblaje-registrar')
            numero_registro = respuesta.json().get("numero")

        # 2) Ligar las piezas físicas al registro.
        #    Por cada modelo marcado se toman las N piezas Disponibles DE ESA LÍNEA.
        libres = _componentes_libres(comps, linea)
        montados = 0
        faltantes = []

        for codigo_modelo, cantidad in seleccion.items():
            disponibles = libres.get(codigo_modelo, [])

            if len(disponibles) < cantidad:
                faltantes.append(
                    f"{codigo_modelo} (pediste {cantidad}, hay {len(disponibles)})"
                )

            for pieza in disponibles[:cantidad]:
                patch = requests.patch(
                    f"{API}/componentes/mod/{pieza['numero']}/",
                    json={
                        "registro_ensamblaje": numero_registro,
                        "estado": EDO_COMP_EN_USO,
                    },
                    headers=headers,
                )
                if patch.status_code in (200, 202):
                    montados += 1

        # 3) Si se pidió terminar, se sella el fin con el timestamp.
        if terminar:
            cierre = requests.patch(
                f"{API}/produccion/registros-ensamblaje/mod/{numero_registro}/",
                json={"fecha_fin": fecha_hoy, "hora_fin": hora_ahora},
                headers=headers,
            )
            if cierre.status_code in (200, 202):
                messages.success(
                    request,
                    f"Ensamblaje #{numero_registro} TERMINADO el {fecha_hoy} a las "
                    f"{hora_ahora} (se agregaron {montados} componente(s))."
                )
                return redirect('ensamblaje-registrar')
            messages.error(request, "Se registraron las piezas pero no se pudo marcar el fin.")
            return redirect('ensamblaje-registrar')

        aviso = f"Ensamblaje #{numero_registro}: {montados} componente(s) agregado(s)."
        if faltantes:
            messages.warning(request, aviso + " Sin stock suficiente de: " + "; ".join(faltantes))
        else:
            messages.success(request, aviso)

        return redirect('ensamblaje-registrar')

    # ------------------------------------------------------------------- GET
    laptops = _laptops_disponibles(headers)

    lineas = requests.get(f"{API}/lineas/", headers=headers).json()
    if not isinstance(lineas, list):
        lineas = []

    laptop_sel = request.GET.get("laptop") or ""
    linea_sel = request.GET.get("linea") or ""
    laptop_obj = None
    componentes_bom = []
    tipos_info = {}
    registro = None

    # Se necesitan las dos: la laptop define QUÉ componentes acepta (BOM) y
    # la línea define CUÁLES hay disponibles ahí.
    if laptop_sel and linea_sel:
        laptop_obj = next(
            (l for l in laptops if str(l.get("numero")) == str(laptop_sel)),
            None
        )

        if laptop_obj and laptop_obj.get("modelo_codigo"):
            filas_bom = _bom(headers, laptop_obj["modelo_codigo"])
            cap_tipo = _capacidad_por_tipo(filas_bom)

            comps = _todos_los_componentes(headers)
            libres = _componentes_libres(comps, linea_sel)

            registro = _registro_abierto(headers, laptop_sel)
            ya_montado = _montado_por_modelo(comps, registro.get("numero") if registro else None)

            # Cuánto lleva montado cada TIPO en este ensamblaje.
            montado_tipo = {}
            for fila in filas_bom:
                codigo = fila.get("componente_codigo")
                tipo = fila.get("componente_tipo")
                if ya_montado.get(codigo):
                    montado_tipo[tipo] = montado_tipo.get(tipo, 0) + ya_montado[codigo]

            for fila in filas_bom:
                codigo = fila.get("componente_codigo")
                tipo_codigo = fila.get("componente_tipo")
                disponibles = len(libres.get(codigo, []))
                capacidad = fila.get("capacidad") or 1
                cap_t = cap_tipo.get(tipo_codigo, capacidad)
                libres_tipo = cap_t - montado_tipo.get(tipo_codigo, 0)

                componentes_bom.append({
                    "codigo": codigo,
                    "nombre": fila.get("componente_nombre"),
                    # Nombre legible del tipo (Procesador, Memoria RAM, ...),
                    # con el código como respaldo por si viniera vacío.
                    "tipo": fila.get("componente_tipo_nombre") or tipo_codigo,
                    "tipo_codigo": tipo_codigo,
                    # Ranuras del TIPO: tope real compartido entre sus modelos.
                    "capacidad_tipo": cap_t,
                    "capacidad": capacidad,
                    "disponibles": disponibles,
                    "montado": ya_montado.get(codigo, 0),
                    # Tope real: ni más de lo que cabe en el tipo ni más de lo que hay.
                    "maximo": max(0, min(capacidad, disponibles, libres_tipo)),
                    "sin_stock": disponibles == 0,
                    # Ese tipo ya quedó lleno con lo montado antes.
                    "tipo_lleno": libres_tipo <= 0,
                })

                tipos_info.setdefault(tipo_codigo, {
                    "nombre": fila.get("componente_tipo_nombre") or tipo_codigo,
                    "capacidad": cap_t,
                    "montado": montado_tipo.get(tipo_codigo, 0),
                })

            # Primero los que más stock tienen en la línea (los que sí se pueden
            # montar quedan arriba y los "sin stock" al final); a igual stock,
            # en orden alfabético por nombre.
            componentes_bom.sort(
                key=lambda c: (-c["disponibles"], (c["nombre"] or c["codigo"]).lower())
            )

    return render(
        request,
        'produccion/ensamblaje_registrar.html',
        {
            "laptops": laptops,
            "lineas": lineas,
            "laptop_sel": str(laptop_sel),
            "linea_sel": str(linea_sel),
            "laptop_obj": laptop_obj,
            "componentes": componentes_bom,
            "tipos_info": tipos_info,
            "registro": registro,
        }
    )
