import requests

from datetime import datetime, time

from django.contrib import messages
from django.shortcuts import render, redirect
import requests
from django.views import generic


from .forms import get_choices_lineas_paro

# URL base de la API (Servicios). Igual que en home/views.py y componentes/views.py.
API = "http://127.0.0.1:8000/api"

# Estados de laptop que YA no admiten registrar ensamblaje:
# EMBALA = Embalada, APROV = Aprobada (ya pasó calidad, va camino a embalaje).
ESTADOS_LAPTOP_EXCLUIDOS = {"EMBALA", "APROV"}

# Estados de componente.
EDO_COMP_DISPONIBLE = "EDC001"
EDO_COMP_EN_USO = "EDC002"

# Estado con el que nace una orden de producción (edo_produccion).
EDO_ORDEN_PENDIENTE = "PEND"

# Laptop ya embalada: es la que de verdad cuenta como producida (ver el trigger
# tg_Control_Estado_Orden_Produccion en DB/triggers.sql).
EDO_LAPTOP_EMBALADA = "EMBALA"


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


# 
#   ORDENES DE PROCUCION
# 

def _laptops_de_orden(headers, folio):
    """Laptops registradas a esa orden. vista_laptops ya trae orden_folio, así
    que basta con filtrar la consulta general."""
    laptops = requests.get(f"{API}/produccion/laptops/", headers=headers).json()
    if not isinstance(laptops, list):
        return []
    propias = [l for l in laptops if str(l.get("orden_folio")) == str(folio)]
    return sorted(propias, key=lambda l: l.get("numero") or 0)


def _ensamblajes_por_laptop(headers):
    """Todos los registros de ensamblaje agrupados por laptop. Se piden de una
    sola vez para no llamar a la API una vez por renglón de la tabla."""
    regs = requests.get(f"{API}/produccion/registros-ensamblaje/", headers=headers).json()
    if not isinstance(regs, list):
        return {}
    por_laptop = {}
    for registro in sorted(regs, key=lambda r: r.get("numero") or 0):
        por_laptop.setdefault(str(registro.get("laptop")), []).append(registro)
    return por_laptop


def _avance_ensamblaje(registros):
    """Cómo va el ensamblaje de una laptop: sin registro, uno abierto (sin
    fecha_fin) o ya terminado. Devuelve el badge listo para la plantilla."""
    abierto = next((r for r in registros if not r.get("fecha_fin")), None)

    if abierto:
        return {
            "estado": "proceso",
            "texto": f"En proceso #{abierto.get('numero')}",
            "clase": "text-bg-warning",
            "detalle": f"Inició {abierto.get('fecha_inicio') or '—'} "
                       f"{abierto.get('hora_inicio') or ''}".strip(),
        }

    cerrados = [r for r in registros if r.get("fecha_fin")]
    if cerrados:
        ultimo = cerrados[-1]
        return {
            "estado": "terminado",
            "texto": f"Terminado #{ultimo.get('numero')}",
            "clase": "text-bg-success",
            "detalle": f"Terminó {ultimo.get('fecha_fin')} "
                       f"{ultimo.get('hora_fin') or ''}".strip(),
        }

    return {
        "estado": "sin_iniciar",
        "texto": "Sin iniciar",
        "clase": "text-bg-light",
        "detalle": "",
    }


def ordenesProduccionListView(request):
    """Consulta general de órdenes de producción (lee de vista_ordenes_produccion)
    y alta de una nueva."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        payload = {
            "fecha": request.POST.get("fecha") or None,
            "hora": request.POST.get("hora") or None,
            "modelo_laptop": request.POST.get("modelo_laptop") or None,
            "lote": request.POST.get("lote") or None,
            "cant_planificada": request.POST.get("cant_planificada") or 0,
            # Nace en cero: lo producido se va contando conforme avanza la orden.
            "cant_producida": 0,
            # El estado no se captura: toda orden nueva nace Pendiente y de ahí
            # la mueven los triggers o el botón de cancelar.
            "estado": EDO_ORDEN_PENDIENTE,
        }

        respuesta = requests.post(f"{API}/produccion/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Orden de producción registrada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

        return redirect('ordenes-produccion-lista')

    ordenes = requests.get(f"{API}/produccion/", headers=headers).json()
    modelos = requests.get(f"{API}/produccion/modelos/", headers=headers).json()
    estados = requests.get(f"{API}/produccion/estados/", headers=headers).json()
    lotes = requests.get(f"{API}/produccion/lotes/", headers=headers).json()

    ahora = datetime.now()

    return render(
        request,
        "produccion/lista_ordenes.html",
        {
            "ordenes": ordenes if isinstance(ordenes, list) else [],
            "modelos": modelos if isinstance(modelos, list) else [],
            "estados": estados if isinstance(estados, list) else [],
            "lotes": lotes if isinstance(lotes, list) else [],
            # Valores por defecto del modal de alta.
            "hoy": ahora.date().isoformat(),
            "hora_ahora": ahora.strftime("%H:%M"),
        }
    )


def ordenProduccionEditarView(request, folio):
    """Se manda PATCH y no PUT porque cant_producida no se captura en el
    formulario: con un PUT parcial la API la dejaría vacía."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        payload = {
            "fecha": request.POST.get("fecha") or None,
            "hora": request.POST.get("hora") or None,
            "modelo_laptop": request.POST.get("modelo_laptop") or None,
            "lote": request.POST.get("lote") or None,
            "cant_planificada": request.POST.get("cant_planificada") or 0,
            "estado": request.POST.get("estado") or None,
        }

        respuesta = requests.patch(f"{API}/produccion/mod/{folio}/", json=payload, headers=headers)

        if respuesta.status_code in (200, 202):
            messages.success(request, "Orden de producción actualizada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('ordenes-produccion-lista')


def ordenProduccionCancelarView(request, folio):
    """El DELETE de la API no borra la orden: la deja en estado Cancelada (CANC)."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/produccion/mod/{folio}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, f"Orden #{folio} cancelada.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('ordenes-produccion-lista')


def ordenProduccionDetalleView(request, folio):
    """Ficha de la orden con las laptops que se le registraron y en qué va el
    ensamblaje de cada una."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    orden = requests.get(f"{API}/produccion/{folio}/", headers=headers).json()
    if not isinstance(orden, dict) or not orden.get("folio"):
        messages.error(request, "No se encontró esa orden de producción.")
        return redirect('ordenes-produccion-lista')

    registros = _ensamblajes_por_laptop(headers)

    laptops = []
    terminados = 0
    en_proceso = 0
    embaladas = 0

    for laptop in _laptops_de_orden(headers, folio):
        avance = _avance_ensamblaje(registros.get(str(laptop.get("numero")), []))

        if avance["estado"] == "terminado":
            terminados += 1
        elif avance["estado"] == "proceso":
            en_proceso += 1

        if laptop.get("estado_codigo") == EDO_LAPTOP_EMBALADA:
            embaladas += 1

        laptops.append({**laptop, "avance": avance})

    planificadas = orden.get("cant_planificada") or 0
    registradas = len(laptops)

    return render(
        request,
        "produccion/detalle_orden.html",
        {
            "orden": orden,
            "laptops": laptops,
            "planificadas": planificadas,
            "registradas": registradas,
            "terminados": terminados,
            "en_proceso": en_proceso,
            "embaladas": embaladas,
            # Se topa en 100 para que la barra no se desborde si se registraron too many
            "porcentaje": min(100, round(registradas * 100 / planificadas)) if planificadas else 0,
        }
    )


# 
#   LAPTOPS
# 

# Estados en los que la laptop ya cerró su ciclo productivo y no se le deben
# quitar piezas. Es el mismo criterio del trigger
# tg_Bloquear_Componentes_Laptop_Finalizada (ver DB/triggers.sql).
ESTADOS_LAPTOP_FINALIZADOS = {"APROV", "RECHA", "EMBALA"}

# Estado con el que nace una laptop.
EDO_LAPTOP_REGISTRADA = "REGIS"

# Órdenes que todavía admiten producción nueva. Contra una Completada o
# Cancelada ya no se registran laptops.
EDOS_ORDEN_ABIERTA = ("PEND", "PROC")


def _serie_temporal_sugerida(laptops):
    """Serie provisional para una laptop nueva, siguiendo la convención que ya
    trae la base (TMP-0001, TMP-0002...). La columna num_serie es NOT NULL y
    UNIQUE, así que no puede quedar vacía; el trigger
    tg_Generar_Numero_Serie_Final la reemplaza por la definitiva
    (TP-AAAAMMDD-NNNNNN) cuando calidad aprueba la laptop."""
    numeros = [l.get("numero") or 0 for l in laptops]
    return "TMP-{:04d}".format((max(numeros) + 1) if numeros else 1)


def _filtrar_laptops(laptops, filtros):
    """Aplica los filtros de la barra de búsqueda. Se filtra aquí y no en la API
    porque el endpoint de laptops no acepta query params."""
    resultado = laptops

    for campo, clave in (("estado", "estado_codigo"),
                         ("modelo", "modelo_codigo"),
                         ("linea", "linea_codigo"),
                         ("lote", "lote_codigo"),
                         ("orden", "orden_folio")):
        valor = filtros.get(campo)
        if valor:
            resultado = [l for l in resultado
                         if str(l.get(clave) or "") == str(valor)]

    texto = (filtros.get("q") or "").strip().lower()
    if texto:
        resultado = [l for l in resultado
                     if texto in str(l.get("num_serie") or "").lower()
                     or texto in str(l.get("numero") or "")]

    return resultado


def _componentes_montados(headers, registros):
    """Componentes físicos ligados a los ensamblajes de una laptop.

    Se leen de vista_componentes (/api/componentes/) y no del detalle de la
    laptop porque esa vista ya trae los nombres de modelo, fabricante y estado;
    el detalle solo devuelve los códigos."""
    numeros = {str(r.get("numero")) for r in registros}
    if not numeros:
        return []
    montados = [c for c in _todos_los_componentes(headers)
                if str(c.get("registro_ensamblaje")) in numeros]
    return sorted(montados,
                  key=lambda c: ((c.get("modelo_nombre") or "").lower(), c.get("numero") or 0))


# ---------------------------------------------------------------------------
#   Seguimiento de la laptop: calidad, embalaje, tiempos, avance y bitácora
# ---------------------------------------------------------------------------

def _momento(fecha, hora):
    """Junta la fecha y la hora que manda la API en un datetime, para poder
    ordenar y restar. Devuelve None si no hay fecha."""
    if not fecha:
        return None
    try:
        dia = datetime.strptime(str(fecha)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    try:
        reloj = datetime.strptime(str(hora or "00:00:00")[:8], "%H:%M:%S").time()
    except ValueError:
        reloj = time(0, 0)
    return datetime.combine(dia, reloj)


def _duracion_min(minutos):
    """Minutos a texto legible: '45 min', '3 h 30 min', '2 d 5 h'."""
    if not minutos:
        return None
    if minutos < 60:
        return f"{minutos} min"
    horas, resto = divmod(minutos, 60)
    if horas < 24:
        return f"{horas} h {resto} min" if resto else f"{horas} h"
    dias, horas = divmod(horas, 24)
    return f"{dias} d {horas} h" if horas else f"{dias} d"


def _duracion(desde, hasta):
    """Duración legible entre dos datetime. None si falta alguno o van al revés."""
    if not desde or not hasta or hasta < desde:
        return None
    return _duracion_min(int((hasta - desde).total_seconds() // 60))


def _inspecciones_de_laptop(headers, numero):
    """Inspecciones de calidad de la laptop.

    El endpoint de lista de calidad no devuelve `observaciones` ni `hora`, así
    que se usa solo para saber CUÁLES son de esta laptop y luego se pide el
    detalle de cada una, que sí trae todo. Son pocas por laptop, así que el
    costo es aceptable y no hay que tocar el módulo de calidad."""
    lista = requests.get(f"{API}/calidad/Inspeccion/Listar/", headers=headers).json()
    if not isinstance(lista, list):
        return []

    completas = []
    for fila in lista:
        if str(fila.get("laptop_numero")) != str(numero):
            continue
        detalle = requests.get(
            f"{API}/calidad/Inspeccion/Detalle/{fila.get('numero')}/",
            headers=headers,
        ).json()
        # Si el detalle falla nos quedamos con lo que traía la lista.
        completas.append(detalle if isinstance(detalle, dict) and detalle.get("numero") else fila)

    return sorted(completas, key=lambda i: (str(i.get("fecha") or ""), str(i.get("hora") or "")))


def _embalajes_de_laptop(headers, num_serie):
    """Embalajes de la laptop. El endpoint de lista no devuelve el número de
    laptop, pero sí su num_serie, y como esa columna es única (IUK_serie_laptop)
    alcanza para cruzar sin pedir el detalle de cada registro."""
    if not num_serie:
        return []
    lista = requests.get(f"{API}/embalaje/Embalaje/Listar/", headers=headers).json()
    if not isinstance(lista, list):
        return []
    propios = [e for e in lista
               if str(e.get("laptop_num_serie") or "") == str(num_serie)]
    return sorted(propios, key=lambda e: (str(e.get("fecha") or ""), str(e.get("hora") or "")))


def _avance_bom(headers, modelo_laptop, componentes):
    """Qué tan armada va la laptop contra la lista de materiales de su modelo.

    Se cuenta POR TIPO, que es el tope real: una laptop con un socket lleva un
    procesador aunque haya varios modelos compatibles. Devuelve None si el
    modelo no tiene BOM registrado."""
    filas = _bom(headers, modelo_laptop) if modelo_laptop else []
    if not filas:
        return None

    cap_tipo = _capacidad_por_tipo(filas)
    nombre_tipo = {f.get("componente_tipo"): (f.get("componente_tipo_nombre")
                                              or f.get("componente_tipo"))
                   for f in filas}
    tipo_de_modelo = {f.get("componente_codigo"): f.get("componente_tipo") for f in filas}

    montado_tipo = {}
    for c in componentes:
        tipo = tipo_de_modelo.get(c.get("modelo_codigo"))
        if tipo:
            montado_tipo[tipo] = montado_tipo.get(tipo, 0) + 1

    detalle = []
    for tipo, capacidad in cap_tipo.items():
        puestos = montado_tipo.get(tipo, 0)
        detalle.append({
            "tipo": nombre_tipo.get(tipo, tipo),
            "montado": puestos,
            "capacidad": capacidad,
            "faltan": max(0, capacidad - puestos),
            "completo": puestos >= capacidad,
        })

    # Primero lo que falta, para que salte a la vista; luego por nombre.
    detalle.sort(key=lambda d: (d["completo"], d["tipo"].lower()))
    completos = sum(1 for d in detalle if d["completo"])

    return {
        "detalle": detalle,
        "faltantes": [d for d in detalle if not d["completo"]],
        "tipos_totales": len(detalle),
        "tipos_completos": completos,
        "porcentaje": round(completos * 100 / len(detalle)) if detalle else 0,
        "completa": completos == len(detalle),
    }


def _tiempos(registros, embalajes):
    """Anota la duración de cada ensamblaje en su propio diccionario y calcula
    los tiempos agregados de la laptop.

    OJO: la tabla laptop no guarda cuándo se dio de alta, así que el ciclo se
    mide desde que ARRANCÓ SU PRIMER ENSAMBLAJE, no desde que se registró."""
    minutos_armado = 0

    for r in registros:
        inicio = _momento(r.get("fecha_inicio"), r.get("hora_inicio"))
        fin = _momento(r.get("fecha_fin"), r.get("hora_fin"))
        r["duracion"] = _duracion(inicio, fin)
        if inicio and fin and fin >= inicio:
            minutos_armado += int((fin - inicio).total_seconds() // 60)

    inicios = [m for m in (_momento(r.get("fecha_inicio"), r.get("hora_inicio"))
                           for r in registros) if m]
    cierres = [m for m in (_momento(e.get("fecha"), e.get("hora"))
                           for e in embalajes) if m]

    primer_inicio = min(inicios) if inicios else None
    embalado_en = max(cierres) if cierres else None

    return {
        # Suma de los ensamblajes ya cerrados: tiempo de trabajo real, sin
        # contar las esperas entre uno y otro.
        "armado_efectivo": _duracion_min(minutos_armado),
        "primer_inicio": primer_inicio,
        "embalado_en": embalado_en,
        "ciclo": _duracion(primer_inicio, embalado_en),
        "abiertos": sum(1 for r in registros if not r.get("fecha_fin")),
    }


def _bitacora(registros, inspecciones, embalajes):
    """Todos los eventos de la laptop en una sola lista cronológica: arranques y
    cierres de ensamblaje, inspecciones de calidad y embalaje."""
    eventos = []

    for r in registros:
        numero = r.get("numero")
        eventos.append({
            "momento": _momento(r.get("fecha_inicio"), r.get("hora_inicio")),
            "fecha": r.get("fecha_inicio"),
            "hora": r.get("hora_inicio"),
            "titulo": f"Ensamblaje #{numero} iniciado",
            "detalle": f"Línea {r.get('linea_nombre') or r.get('linea') or '—'}",
            "icono": "bi-play-circle",
            "clase": "primary",
        })
        if r.get("fecha_fin"):
            dur = r.get("duracion")
            eventos.append({
                "momento": _momento(r.get("fecha_fin"), r.get("hora_fin")),
                "fecha": r.get("fecha_fin"),
                "hora": r.get("hora_fin"),
                "titulo": f"Ensamblaje #{numero} terminado",
                "detalle": f"Duró {dur}" if dur else "",
                "icono": "bi-check-circle",
                "clase": "success",
            })

    for i in inspecciones:
        # resultado: 1 aprobada, 0 rechazada, 2 continuar (ver calidad/models.py)
        resultado = i.get("resultado")
        nombre = i.get("resultado_nombre") or "Inspección"
        if resultado == 1:
            icono, clase = "bi-patch-check", "success"
        elif resultado == 0:
            icono, clase = "bi-x-octagon", "danger"
        else:
            icono, clase = "bi-arrow-repeat", "warning"

        partes = []
        if i.get("empleado_nombre"):
            partes.append(i["empleado_nombre"])
        if i.get("linea_nombre"):
            partes.append(i["linea_nombre"])

        eventos.append({
            "momento": _momento(i.get("fecha"), i.get("hora")),
            "fecha": i.get("fecha"),
            "hora": i.get("hora"),
            "titulo": f"Inspección #{i.get('numero')} · {nombre}",
            "detalle": " · ".join(partes),
            "observaciones": i.get("observaciones"),
            "icono": icono,
            "clase": clase,
        })

    for e in embalajes:
        eventos.append({
            "momento": _momento(e.get("fecha"), e.get("hora")),
            "fecha": e.get("fecha"),
            "hora": e.get("hora"),
            "titulo": f"Embalada · embalaje #{e.get('numero')}",
            "detalle": e.get("tipo_nombre") or "",
            "icono": "bi-box-seam",
            "clase": "dark",
        })

    # Los eventos sin fecha se van al final en vez de romper el orden.
    eventos.sort(key=lambda ev: (ev["momento"] is None, ev["momento"] or datetime.min))
    return eventos


def _registros_enriquecidos(headers, nombres_linea):
    """Todos los registros de ensamblaje de la planta con el contexto que el
    endpoint no trae: de qué laptop son, el nombre de la línea, cuánto duraron
    y cuántas piezas llevan montadas."""
    regs = requests.get(f"{API}/produccion/registros-ensamblaje/", headers=headers).json()
    if not isinstance(regs, list):
        return []

    laptops = requests.get(f"{API}/produccion/laptops/", headers=headers).json()
    laptops = {str(l.get("numero")): l for l in laptops} if isinstance(laptops, list) else {}

    # Piezas por registro, contadas de una sola pasada sobre el inventario.
    piezas = {}
    for c in _todos_los_componentes(headers):
        clave = c.get("registro_ensamblaje")
        if clave:
            piezas[str(clave)] = piezas.get(str(clave), 0) + 1

    enriquecidos = []
    for r in regs:
        laptop = laptops.get(str(r.get("laptop"))) or {}
        inicio = _momento(r.get("fecha_inicio"), r.get("hora_inicio"))
        fin = _momento(r.get("fecha_fin"), r.get("hora_fin"))
        minutos = (int((fin - inicio).total_seconds() // 60)
                   if inicio and fin and fin >= inicio else None)

        enriquecidos.append({
            **r,
            "linea_nombre": nombres_linea.get(r.get("linea")) or r.get("linea"),
            "laptop_serie": laptop.get("num_serie"),
            "laptop_modelo": laptop.get("modelo_nombre"),
            "laptop_estado": laptop.get("estado_nombre"),
            "laptop_estado_codigo": laptop.get("estado_codigo"),
            "duracion": _duracion_min(minutos),
            "minutos": minutos,
            "piezas": piezas.get(str(r.get("numero")), 0),
            "abierto": not r.get("fecha_fin"),
        })

    # Los abiertos primero, que son los que urgen; dentro de cada grupo, lo más
    # reciente arriba.
    enriquecidos.sort(key=lambda e: (not e["abierto"], -(e.get("numero") or 0)))
    return enriquecidos


def _filtrar_ensamblajes(registros, filtros):
    """Filtros de la pantalla de seguimiento. Se aplican aquí porque el endpoint
    de registros de ensamblaje no acepta query params."""
    resultado = registros

    situacion = filtros.get("situacion")
    if situacion == "abierto":
        resultado = [r for r in resultado if r["abierto"]]
    elif situacion == "terminado":
        resultado = [r for r in resultado if not r["abierto"]]

    if filtros.get("linea"):
        resultado = [r for r in resultado
                     if str(r.get("linea") or "") == str(filtros["linea"])]

    texto = (filtros.get("q") or "").strip().lower()
    if texto:
        resultado = [r for r in resultado
                     if texto in str(r.get("numero") or "")
                     or texto in str(r.get("laptop") or "")
                     or texto in str(r.get("laptop_serie") or "").lower()]

    return resultado


def ensamblajeSeguimientoView(request):
    """Seguimiento de ensamblaje: todos los registros de la planta, con filtros
    y acceso al expediente de cada laptop. Responde de un vistazo qué se está
    armando ahora mismo y qué ya cerró."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    lineas = requests.get(f"{API}/lineas/", headers=headers).json()
    lineas = lineas if isinstance(lineas, list) else []
    nombres_linea = {l.get("codigo"): l.get("nombre") for l in lineas}

    registros = _registros_enriquecidos(headers, nombres_linea)

    filtros = {
        "situacion": request.GET.get("situacion") or "",
        "linea": request.GET.get("linea") or "",
        "q": request.GET.get("q") or "",
    }
    filtrados = _filtrar_ensamblajes(registros, filtros)

    # Promedio solo de los que ya cerraron: los abiertos no tienen duración.
    cerrados = [r["minutos"] for r in registros if r["minutos"] is not None]
    promedio = _duracion_min(round(sum(cerrados) / len(cerrados))) if cerrados else None

    return render(
        request,
        "produccion/seguimiento_ensamblaje.html",
        {
            "registros": filtrados,
            "total": len(registros),
            "mostrados": len(filtrados),
            "abiertos": sum(1 for r in registros if r["abierto"]),
            "terminados": sum(1 for r in registros if not r["abierto"]),
            "promedio": promedio,
            "filtros": filtros,
            "hay_filtros": any(filtros.values()),
            "lineas": lineas,
        }
    )


def _catalogos_laptop(headers):
    """Los catálogos que alimentan los selects de alta, edición y filtros.

    `ordenes` trae todas (los filtros de la lista necesitan poder buscar por
    cualquiera) y `ordenes_abiertas` solo las que admiten producción nueva."""
    def lista(url):
        datos = requests.get(url, headers=headers).json()
        return datos if isinstance(datos, list) else []

    ordenes = lista(f"{API}/produccion/")

    return {
        "modelos": lista(f"{API}/produccion/modelos/"),
        "estados": lista(f"{API}/produccion/estados-laptop/"),
        "lineas": lista(f"{API}/lineas/"),
        "lotes": lista(f"{API}/produccion/lotes/"),
        "ordenes": ordenes,
        # Solo contra estas se puede registrar: una Completada o Cancelada ya
        # no admite laptops nuevas.
        "ordenes_abiertas": [o for o in ordenes
                             if o.get("estado_codigo") in EDOS_ORDEN_ABIERTA],
    }


def laptopsListView(request):
    """Consulta general de laptops (lee de vista_laptops) con filtros, y alta
    de una nueva."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        laptops_actuales = requests.get(f"{API}/produccion/laptops/", headers=headers).json()
        if not isinstance(laptops_actuales, list):
            laptops_actuales = []

        orden = request.POST.get("orden") or None
        if not orden:
            messages.error(request, "Selecciona la orden de producción: de ahí "
                                    "salen el modelo y el lote de la laptop.")
            return redirect('laptops-lista')

        # Ni modelo ni lote ni estado se capturan: los dos primeros los hereda de
        # su orden (la API los resuelve) y el estado siempre es Registrada.
        payload = {
            "num_serie": (request.POST.get("num_serie") or "").strip()
                         or _serie_temporal_sugerida(laptops_actuales),
            "descripcion": request.POST.get("descripcion") or None,
            "orden": orden,
            "estado": EDO_LAPTOP_REGISTRADA,
            "linea": request.POST.get("linea") or None,
        }

        respuesta = requests.post(f"{API}/produccion/laptops/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Laptop registrada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

        return redirect('laptops-lista')

    laptops = requests.get(f"{API}/produccion/laptops/", headers=headers).json()
    laptops = laptops if isinstance(laptops, list) else []

    filtros = {
        "estado": request.GET.get("estado") or "",
        "modelo": request.GET.get("modelo") or "",
        "linea": request.GET.get("linea") or "",
        "lote": request.GET.get("lote") or "",
        "orden": request.GET.get("orden") or "",
        "q": request.GET.get("q") or "",
    }

    filtradas = _filtrar_laptops(laptops, filtros)

    contexto = _catalogos_laptop(headers)
    contexto.update({
        "laptops": filtradas,
        "total": len(laptops),
        "mostradas": len(filtradas),
        "filtros": filtros,
        "hay_filtros": any(filtros.values()),
        "serie_sugerida": _serie_temporal_sugerida(laptops),
        "estado_inicial": EDO_LAPTOP_REGISTRADA,
    })

    return render(request, "produccion/lista_laptops.html", contexto)


def laptopDetalleView(request, numero):
    """Expediente completo de la laptop: sus datos editables, el seguimiento de
    todo su paso por la planta (ensamblajes, calidad y embalaje), los tiempos,
    qué le falta contra su lista de materiales y los componentes que trae
    montados, con la opción de liberarlos."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    laptop = requests.get(f"{API}/produccion/laptops/{numero}/", headers=headers).json()
    if not isinstance(laptop, dict) or not laptop.get("numero"):
        messages.error(request, "No se encontró esa laptop.")
        return redirect('laptops-lista')

    registros = laptop.get("registros_ensamblaje") or []
    componentes = _componentes_montados(headers, registros)

    # Las otras dos etapas del ciclo. Cada módulo pide su propio permiso
    # (calidad / embalaje): si el rol no lo tiene, los helpers devuelven lista
    # vacía y la sección se muestra sin datos en vez de tronar.
    inspecciones = _inspecciones_de_laptop(headers, numero)
    embalajes = _embalajes_de_laptop(headers, laptop.get("num_serie"))

    contexto = _catalogos_laptop(headers)

    # El registro de ensamblaje solo guarda el código de la línea; se le pega el
    # nombre para no mostrar "LIN001" pelón en la bitácora y en la tabla.
    nombres_linea = {l.get("codigo"): l.get("nombre") for l in contexto.get("lineas", [])}
    for r in registros:
        r["linea_nombre"] = nombres_linea.get(r.get("linea")) or r.get("linea")

    # _tiempos anota la duración dentro de cada registro, así que va antes.
    tiempos = _tiempos(registros, embalajes)
    avance = _avance_bom(headers, laptop.get("modelo_codigo"), componentes)
    bitacora = _bitacora(registros, inspecciones, embalajes)

    # Estados a los que puede pasar un componente al desmontarlo. Se excluye
    # "En Uso": si sigue En Uso es que no se liberó.
    estados_comp = requests.get(f"{API}/componentes/estados/", headers=headers).json()
    estados_comp = ([e for e in estados_comp if e.get("codigo") != EDO_COMP_EN_USO]
                    if isinstance(estados_comp, list) else [])

    contexto.update({
        "laptop": laptop,
        "registros": registros,
        "componentes": componentes,
        "inspecciones": inspecciones,
        "embalajes": embalajes,
        "tiempos": tiempos,
        "avance": avance,
        "bitacora": bitacora,
        # La última inspección manda: es la que explica el estado actual.
        "ultima_inspeccion": inspecciones[-1] if inspecciones else None,
        "estados_componente": estados_comp,
        # Aprobada, Rechazada o Embalada: se muestran las piezas pero ya no se
        # pueden quitar, para no romper la trazabilidad.
        "finalizada": laptop.get("estado_codigo") in ESTADOS_LAPTOP_FINALIZADOS,
        "estado_disponible": EDO_COMP_DISPONIBLE,
    })

    return render(request, "produccion/detalle_laptop.html", contexto)


def laptopEditarView(request, numero):
    """Guarda los datos de la laptop. Se manda PATCH para tocar solo lo que
    viene en el formulario."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        # Tres campos quedan fuera del payload a propósito:
        #   num_serie     — se fija al registrar y solo la reescribe el trigger
        #                   tg_Generar_Numero_Serie_Final al aprobar en calidad.
        #   modelo y lote — se heredan de la orden; la API los recalcula sola en
        #                   cada guardado, así que mandarlos no serviría de nada.
        payload = {
            "descripcion": request.POST.get("descripcion") or None,
            "orden": request.POST.get("orden") or None,
            "estado": request.POST.get("estado") or None,
            "linea": request.POST.get("linea") or None,
        }

        respuesta = requests.patch(
            f"{API}/produccion/laptops/mod/{numero}/", json=payload, headers=headers)

        if respuesta.status_code in (200, 202):
            messages.success(request, "Laptop actualizada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('laptop-detalle', numero=numero)


def laptopRechazarView(request, numero):
    """El DELETE de la API no borra la laptop: la deja Rechazada (RECHA)."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.delete(f"{API}/produccion/laptops/mod/{numero}/", headers=headers)

        if respuesta.status_code == 204:
            messages.success(request, f"Laptop #{numero} marcada como Rechazada.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('laptops-lista')


def laptopComponenteLiberarView(request, numero, componente):
    """Desmonta un componente de la laptop: lo desliga de su registro de
    ensamblaje y lo deja en el estado elegido — Disponible si vuelve al stock,
    o Dañado/Mermado si salió defectuoso."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        # Se vuelve a consultar el estado de la laptop: el bloqueo no puede
        # depender de que el botón no se haya pintado, el POST se puede forzar.
        laptop = requests.get(f"{API}/produccion/laptops/{numero}/", headers=headers).json()
        laptop = laptop if isinstance(laptop, dict) else {}

        if laptop.get("estado_codigo") in ESTADOS_LAPTOP_FINALIZADOS:
            messages.error(
                request,
                "No se pueden quitar componentes: la laptop está "
                f"{laptop.get('estado_nombre') or 'finalizada'}."
            )
            return redirect('laptop-detalle', numero=numero)

        nuevo_estado = request.POST.get("estado") or EDO_COMP_DISPONIBLE
        if nuevo_estado == EDO_COMP_EN_USO:
            messages.error(request, "Un componente liberado no puede quedar En Uso.")
            return redirect('laptop-detalle', numero=numero)

        respuesta = requests.patch(
            f"{API}/componentes/mod/{componente}/",
            json={"registro_ensamblaje": None, "estado": nuevo_estado},
            headers=headers,
        )

        if respuesta.status_code in (200, 202):
            messages.success(
                request, f"Componente #{componente} liberado de la laptop #{numero}.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('laptop-detalle', numero=numero)


#--------------------------------------------------------------------------------
#                         P A R O S
#---------------------------------------------------------------------------------


API_PARO = "http://127.0.0.1:8000/api/produccion/paros/"


class ListaParos(generic.View):
    template_name = "produccion/paros.html"

    def get(self, request):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        buscar = request.GET.get("buscar", "").strip()
        fecha_desde = request.GET.get("fecha_desde", "")
        fecha_hasta = request.GET.get("fecha_hasta", "")

        params = {}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta

        if buscar:
            params["buscar"] = buscar
            response = requests.get(API_PARO + "buscar/", headers=headers, params=params)
        else:
            response = requests.get(API_PARO, headers=headers, params=params)

        paros = response.json() if response.status_code == 200 else []

        context = {
            "paros": paros,
            "lineas": get_choices_lineas_paro(token),
            "buscar": buscar,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        }
        return render(request, self.template_name, context)


class CrearParo(generic.View):
    def post(self, request):
        token = request.session.get("token")
        ahora = datetime.now()

        data = {
            "razon": request.POST.get("razon"),
            "fecha_inicio": ahora.strftime("%Y-%m-%d"),
            "hora_inicio": ahora.strftime("%H:%M:%S"),
            "linea": request.POST.get("linea"),
        }

        response = requests.post(
            API_PARO,
            headers={"Authorization": f"Bearer {token}"},
            data=data
        )

        if response.status_code == 201:
            messages.success(request, "Paro registrado correctamente.")
        else:
            error_data = response.json()
            mensaje = error_data.get("mensaje") or str(error_data)
            messages.error(request, mensaje)

        return redirect("lista_paros")


class EditarParo(generic.View):
    def post(self, request, numero):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        det_resp = requests.get(API_PARO + f"{numero}/", headers=headers)
        detalle = det_resp.json() if det_resp.status_code == 200 else {}

        data = {
            "razon": request.POST.get("razon"),
            "fecha_inicio": detalle.get("fecha_inicio"),
            "hora_inicio": detalle.get("hora_inicio"),
            "linea": detalle.get("linea_codigo"),
        }

        response = requests.put(
            API_PARO + f"mod/{numero}/",
            headers=headers,
            data=data
        )

        if response.status_code == 200:
            messages.success(request, "Paro actualizado correctamente.")
        else:
            error_data = response.json()
            mensaje = error_data.get("mensaje") or str(error_data)
            messages.error(request, mensaje)

        return redirect("lista_paros")


class CerrarParo(generic.View):
    def post(self, request, numero):
        token = request.session.get("token")

        response = requests.delete(
            API_PARO + f"mod/{numero}/",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code in (200, 204):
            messages.success(request, "Paro cerrado correctamente.")
        else:
            error_data = response.json()
            messages.error(request, error_data.get("mensaje", "No se pudo cerrar el paro."))

        return redirect("lista_paros")