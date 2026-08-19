"""Producción, versión del panel de supervisor.

Órdenes de producción, laptops, ensamblaje y paros. El panel de administrador
tiene su propia copia en la app `produccion/`; ésta se puede cambiar sin
afectarla, porque el supervisor no necesita ver ni poder lo mismo que el admin.
"""

import requests

from datetime import datetime, time

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import generic

from core.api import get, lista, objeto
from core.filtros import contexto as contexto_de_filtros, filtrar, pedidos
from core.lineas import es_de_ensamblaje, solo_de_ensamblaje
from core.guards import RolRequeridoMixin, requiere_rol
from core.roles import ROL_SUPERVISOR

from .forms import get_choices_lineas_paro

# URL base de la API (Servicios). Igual que en home/views.py y componentes/views.py.
API = "http://127.0.0.1:8000/api"

# Estados de laptop que YA no admiten registrar ensamblaje:
# EMBALA = Embalada, APROV = Aprobada (ya pasó calidad, va camino a embalaje).
ESTADOS_LAPTOP_EXCLUIDOS = {"EMBALA", "APROV"}

# Estados de componente.
EDO_COMP_DISPONIBLE = "EDC001"
EDO_COMP_EN_USO = "EDC002"

# Mermado. Un componente así ya no vuelve al inventario, y sp_Liberar_Componentes_Laptop
# lo deja tal cual —con su vínculo al ensamblaje— para no perder el rastro de en
# qué laptop se perdió.
EDO_COMP_MERMADO = "EDC004"

# Estado con el que nace una orden de producción (edo_produccion).
EDO_ORDEN_PENDIENTE = "PEND"

# Laptop ya embalada: es la que de verdad cuenta como producida (ver el trigger
# tg_Registrar_Embalaje en DB/triggers.sql).
EDO_LAPTOP_EMBALADA = "EMBALA"


def _json(url, headers, params=None):
    """GET a la API que devuelve el JSON, o None si algo falló.

    Antes se hacía `requests.get(...).json()` a pelo. Eso funciona mientras la
    API contesta, pero si está apagada la excepción de requests sube hasta la
    vista y la pantalla revienta con un 500.

    Devolver None es suficiente porque todas las funciones de este módulo ya
    revisan el tipo (`isinstance(x, list)`) antes de usar el resultado, y None no
    pasa esa revisión."""
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
    laptops = _json(f"{API}/produccion/laptops/", headers)
    if not isinstance(laptops, list):
        return []
    return [l for l in laptops
            if l.get("estado_codigo") not in ESTADOS_LAPTOP_EXCLUIDOS]


def _bom(headers, modelo_laptop):
    """Filas de modelo_laptop_componente para un modelo de laptop."""
    detalle = _json(
        f"{API}/produccion/modelos/{modelo_laptop}/",
        headers,
    )
    return detalle.get("componentes", []) if isinstance(detalle, dict) else []


def _capacidad_por_tipo(filas_bom):
    """Ranuras disponibles POR TIPO (no por modelo). Una laptop con 1 socket de
    procesador lleva UN procesador, sin importar cuántos modelos sean compatibles."""
    caps = {}
    for fila in filas_bom:
        tipo = fila.get("componente_tipo")
        caps[tipo] = max(caps.get(tipo, 0), fila.get("capacidad") or 1)
    return caps


def _necesario_por_tipo(headers):
    """{tipo: tipo que tiene que estar montado ANTES}, tal cual está en
    tipo_comp.necesario. None = por ahí se empieza (el chasis)."""
    tipos = _json(f"{API}/componentes/tipos/", headers)
    if not isinstance(tipos, list):
        return {}
    return {t.get("codigo"): t.get("necesario") for t in tipos}


def _orden_de_montaje(necesario_de, tipos_bom):
    """Traduce tipo_comp.necesario al orden que aplica A ESTE modelo de laptop.

    Devuelve (requisito, profundidad, ciclicos):

      requisito[t]    Tipo que hay que colocar antes que `t`, saltándose los
                      que el modelo no lleva: si la cámara necesita pantalla y
                      este modelo no trae pantalla, sube por la cadena hasta el
                      primero que sí esté. None = con ése se arranca.
      profundidad[t]  Cuántos pasos hay de `t` hasta el arranque. Sirve para
                      listar primero lo que se monta primero.
      ciclicos        Tipos cuya cadena se muerde la cola (p. ej. TC004 → TC007
                      → TC012 → TC011 → TC001 → TC004, o TC008 apuntándose a sí
                      mismo). Eso es un error de captura en tipo_comp: no existe
                      un orden posible. Se tratan como arranque para no dejar la
                      pantalla trabada, y la vista los reporta para corregirlos.
    """
    # 1) Requisito directo, brincándose los tipos que este modelo no lleva.
    requisito = {}
    for tipo in tipos_bom:
        visitados = {tipo}
        actual = necesario_de.get(tipo)
        while actual and actual not in visitados and actual not in tipos_bom:
            visitados.add(actual)
            actual = necesario_de.get(actual)
        requisito[tipo] = actual if actual in tipos_bom else None

    # 2) Un tipo está en ciclo si siguiendo la cadena se vuelve a encontrar a sí
    #    mismo. Solo se rompen los del anillo; lo que cuelga de ellos se acomoda
    #    solo una vez que el anillo pasa a ser arranque.
    ciclicos = set()
    for tipo in requisito:
        actual = requisito.get(tipo)
        for _ in range(len(requisito)):
            if actual is None:
                break
            if actual == tipo:
                ciclicos.add(tipo)
                break
            actual = requisito.get(actual)
    for tipo in ciclicos:
        requisito[tipo] = None

    # 3) Ya sin ciclos: cuántos saltos faltan para llegar al arranque.
    profundidad = {}
    for tipo in requisito:
        pasos = 0
        actual = requisito.get(tipo)
        while actual is not None and pasos <= len(requisito):
            pasos += 1
            actual = requisito.get(actual)
        profundidad[tipo] = pasos

    return requisito, profundidad, ciclicos


def _todos_los_componentes(headers):
    comps = _json(f"{API}/componentes/", headers)
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


def _registros_de_laptop(headers, laptop):
    """TODOS los registros de ensamblaje de esa laptop.

    Son varios, uno por línea: la laptop cierra el de una línea y abre el de la
    siguiente conforme avanza. Por eso lo que lleva puesto está repartido entre
    todos ellos y no solo en el que está abierto."""
    regs = _json(f"{API}/produccion/registros-ensamblaje/", headers)
    if not isinstance(regs, list):
        return []
    return [r for r in regs if str(r.get("laptop")) == str(laptop)]


def _registro_abierto(headers, laptop):
    """El ensamblaje SIN TERMINAR (sin fecha_fin) de esa laptop, si existe.
    Es el de la línea en la que va ahora; se reutiliza en vez de abrir otro."""
    abiertos = [r for r in _registros_de_laptop(headers, laptop)
                if not r.get("fecha_fin")]
    return abiertos[-1] if abiertos else None


def _montado_por_modelo(comps, numeros_registro):
    """Cuántas piezas de cada modelo lleva PUESTAS la laptop.

    Se cuenta contra todos sus registros, no solo el abierto: la tarjeta madre
    que montó la línea B quedó pegada al registro de la B, que para cuando la
    laptop llega a la C ya está cerrado, y aun así sigue puesta. Mirando solo el
    registro abierto, la línea C vería la laptop vacía y el orden de montaje le
    bloquearía todo."""
    montado = {}
    numeros = {str(n) for n in (numeros_registro or []) if n is not None}
    if not numeros:
        return montado
    for c in comps:
        if str(c.get("registro_ensamblaje")) in numeros:
            modelo = c.get("modelo_codigo")
            montado[modelo] = montado.get(modelo, 0) + 1
    return montado


@requiere_rol(ROL_SUPERVISOR)
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
            return redirect('panel_supervisor:ensamblaje-registrar')

        # La línea define de qué stock se surte el ensamblaje, así que es obligatoria.
        if not linea:
            messages.error(request, "Selecciona la línea en la que se ensambla.")
            return redirect('panel_supervisor:ensamblaje-registrar')

        # Y tiene que ser de ensamblaje. Se revisa aquí y no sólo en la API porque
        # cuando la laptop ya trae un ensamblaje abierto este flujo no vuelve a
        # POSTear el registro: se iría derecho a surtir piezas de una línea que no
        # las tiene y el supervisor leería "0 componentes" en vez del motivo real.
        catalogo_lineas = _json(f"{API}/lineas/", headers)
        if isinstance(catalogo_lineas, list):
            linea_obj = next(
                (l for l in catalogo_lineas if str(l.get("codigo")) == str(linea)),
                None
            )
            if not es_de_ensamblaje(linea_obj):
                messages.error(
                    request,
                    "Solo se puede registrar ensamblaje en líneas de tipo Ensamblaje."
                )
                return redirect('panel_supervisor:ensamblaje-registrar')

        laptop_obj = next(
            (l for l in _laptops_disponibles(headers) if str(l.get("numero")) == str(laptop)),
            None
        )
        if not laptop_obj:
            messages.error(request, "Esa laptop ya no está disponible para ensamblaje.")
            return redirect('panel_supervisor:ensamblaje-registrar')

        filas_bom = _bom(headers, laptop_obj.get("modelo_codigo"))
        tipo_de = {f.get("componente_codigo"): f.get("componente_tipo") for f in filas_bom}
        nombre_tipo = {f.get("componente_tipo"): f.get("componente_tipo_nombre") for f in filas_bom}
        cap_tipo = _capacidad_por_tipo(filas_bom)

        comps = _todos_los_componentes(headers)
        registros_laptop = _registros_de_laptop(headers, laptop)
        registro = next((r for r in reversed(registros_laptop) if not r.get("fecha_fin")), None)
        ya_montado = _montado_por_modelo(comps, [r.get("numero") for r in registros_laptop])

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
            return redirect('panel_supervisor:ensamblaje-registrar')

        # Y que se respete el orden de montaje (tipo_comp.necesario): un tipo solo
        # entra si el que va antes ya lleva al menos una pieza —montada de antes o
        # marcada en este mismo envío—. Se revisa aquí y no solo en el navegador
        # porque el JS se puede saltar con las herramientas de desarrollo.
        requisito_tipo, _, _ = _orden_de_montaje(
            _necesario_por_tipo(headers), set(cap_tipo)
        )

        seleccion_por_tipo = {}
        for codigo_modelo, cantidad in seleccion.items():
            tipo = tipo_de.get(codigo_modelo)
            seleccion_por_tipo[tipo] = seleccion_por_tipo.get(tipo, 0) + cantidad

        fuera_de_orden = [
            f"{nombre_tipo.get(t) or t} va después de "
            f"{nombre_tipo.get(requisito_tipo[t]) or requisito_tipo[t]}"
            for t in seleccion_por_tipo
            if requisito_tipo.get(t) and usado_por_tipo.get(requisito_tipo[t], 0) < 1
        ]
        if fuera_de_orden:
            messages.error(
                request,
                "No se registró: hay que respetar el orden de montaje — "
                + "; ".join(fuera_de_orden)
            )
            return redirect('panel_supervisor:ensamblaje-registrar')

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
                return redirect('panel_supervisor:ensamblaje-registrar')
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
                return redirect('panel_supervisor:ensamblaje-registrar')
            messages.error(request, "Se registraron las piezas pero no se pudo marcar el fin.")
            return redirect('panel_supervisor:ensamblaje-registrar')

        aviso = f"Ensamblaje #{numero_registro}: {montados} componente(s) agregado(s)."
        if faltantes:
            messages.warning(request, aviso + " Sin stock suficiente de: " + "; ".join(faltantes))
        else:
            messages.success(request, aviso)

        return redirect('panel_supervisor:ensamblaje-registrar')

    # ------------------------------------------------------------------- GET
    laptops = _laptops_disponibles(headers)

    # Solo las de ENSAMBLAJE: en una línea de embalaje no se arma nada, y la API
    # y el trigger de la base rechazarían el registro de todas formas.
    lineas = solo_de_ensamblaje(_json(f"{API}/lineas/", headers))

    laptop_sel = request.GET.get("laptop") or ""
    linea_sel = request.GET.get("linea") or ""
    laptop_obj = None
    componentes_bom = []
    tipos_info = {}
    tipos_ciclicos = []
    # Componentes del modelo que esta línea no instala y por eso no se listan.
    ocultos_por_linea = 0
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

            nombre_de_tipo = {f.get("componente_tipo"): f.get("componente_tipo_nombre")
                              for f in filas_bom}

            # Orden de montaje: qué tipo va antes de cuál y a cuántos pasos está
            # cada uno del arranque.
            requisito_tipo, profundidad_tipo, ciclicos = _orden_de_montaje(
                _necesario_por_tipo(headers), set(cap_tipo)
            )
            tipos_ciclicos = sorted(nombre_de_tipo.get(t) or t for t in ciclicos)

            comps = _todos_los_componentes(headers)
            libres = _componentes_libres(comps, linea_sel)

            registros_laptop = _registros_de_laptop(headers, laptop_sel)
            registro = next((r for r in reversed(registros_laptop) if not r.get("fecha_fin")), None)
            ya_montado = _montado_por_modelo(comps, [r.get("numero") for r in registros_laptop])

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

                # Tipo que va antes que éste. Al cargar la pantalla nada está
                # marcado todavía, así que lo único que puede cubrirlo es lo que
                # ya venía montado; de ahí en adelante manda el JS.
                requiere = requisito_tipo.get(tipo_codigo)

                # tipos_info va con el BOM COMPLETO a propósito: el contador y el
                # botón de terminar miden la laptop entera, no lo que le toca a
                # esta línea. Si midieran solo lo de la línea, la primera en
                # acabar lo suyo cerraría el ensamblaje a media producción.
                tipos_info.setdefault(tipo_codigo, {
                    "nombre": fila.get("componente_tipo_nombre") or tipo_codigo,
                    "capacidad": cap_t,
                    "montado": montado_tipo.get(tipo_codigo, 0),
                    # El JS lo usa para habilitar/trabar casillas en vivo.
                    "requiere": requiere,
                })

                # La tabla, en cambio, solo lleva lo que ESTA línea puede
                # instalar. Por ahora eso se deduce del stock: cada línea surte
                # únicamente los tipos que sus estaciones montan, así que lo que
                # no tiene existencias aquí es que no le toca.
                # TODO: cuando exista la relación estación/línea ↔ tipo_comp,
                # filtrar por ahí. El stock confunde "no me toca" con "me quedé
                # sin material".
                if disponibles == 0:
                    ocultos_por_linea += 1
                    continue

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
                    # Orden de montaje.
                    "requiere_tipo": requiere or "",
                    "requiere_nombre": nombre_de_tipo.get(requiere) or requiere or "",
                    "profundidad": profundidad_tipo.get(tipo_codigo, 0),
                    "orden_pendiente": bool(requiere) and montado_tipo.get(requiere, 0) < 1,
                })

            # Primero lo que va primero: los que están a menos pasos del arranque
            # de la cadena de montaje. A igual paso, los que más stock tienen en
            # la línea (los "sin stock" al final) y luego alfabético por nombre.
            componentes_bom.sort(
                key=lambda c: (c["profundidad"], -c["disponibles"],
                               (c["nombre"] or c["codigo"]).lower())
            )

    return render(
        request,
        'panel_supervisor/produccion/ensamblaje_registrar.html',
        {
            "laptops": laptops,
            "lineas": lineas,
            "laptop_sel": str(laptop_sel),
            "linea_sel": str(linea_sel),
            "laptop_obj": laptop_obj,
            "componentes": componentes_bom,
            "tipos_info": tipos_info,
            "tipos_ciclicos": tipos_ciclicos,
            "ocultos_por_linea": ocultos_por_linea,
            "registro": registro,
        }
    )


# 
#   ORDENES DE PROCUCION
# 

def _laptops_de_orden(headers, folio):
    """Laptops registradas a esa orden. vista_laptops ya trae orden_folio, así
    que basta con filtrar la consulta general."""
    laptops = _json(f"{API}/produccion/laptops/", headers)
    if not isinstance(laptops, list):
        return []
    propias = [l for l in laptops if str(l.get("orden_folio")) == str(folio)]
    return sorted(propias, key=lambda l: l.get("numero") or 0)


def _ensamblajes_por_laptop(headers):
    """Todos los registros de ensamblaje agrupados por laptop. Se piden de una
    sola vez para no llamar a la API una vez por renglón de la tabla."""
    regs = _json(f"{API}/produccion/registros-ensamblaje/", headers)
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


def _filtrar_ordenes(ordenes, filtros):
    """Aplica los filtros de la barra de búsqueda de la lista de órdenes.

    Se filtra aquí y no en la API porque /api/produccion/ no acepta query
    params; el resto de la lógica vive en core/filtros.py, que es la que
    comparten las demás listas."""
    filtradas = filtrar(
        ordenes,
        filtros,
        exactos=(("estado", "estado_codigo"),
                 ("modelo", "modelo_codigo"),
                 ("lote", "lote_codigo")),
        busqueda=("folio", "modelo_nombre", "modelo_codigo", "lote_codigo"),
    )

    # El rango de fechas no es una coincidencia exacta, va aparte. Las fechas
    # llegan como AAAA-MM-DD, que se ordena bien comparándolas como texto.
    if filtros["desde"]:
        filtradas = [o for o in filtradas if (o.get("fecha") or "") >= filtros["desde"]]
    if filtros["hasta"]:
        filtradas = [o for o in filtradas if (o.get("fecha") or "") <= filtros["hasta"]]

    return filtradas


@requiere_rol(ROL_SUPERVISOR)
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
            # Nacen en cero: lo producido y lo rechazado se van contando conforme
            # avanza la orden, y quien los cuenta son los triggers de la base.
            "cant_producida": 0,
            "cant_rechazada": 0,
            # El estado no se captura: toda orden nueva nace Pendiente y de ahí
            # la mueven los triggers o el botón de cancelar.
            "estado": EDO_ORDEN_PENDIENTE,
        }

        respuesta = requests.post(f"{API}/produccion/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Orden de producción registrada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

        return redirect('panel_supervisor:ordenes-produccion-lista')

    ordenes = _json(f"{API}/produccion/", headers)
    modelos = _json(f"{API}/produccion/modelos/", headers)
    estados = _json(f"{API}/produccion/estados/", headers)
    lotes = _json(f"{API}/produccion/lotes/", headers)

    ordenes = ordenes if isinstance(ordenes, list) else []

    filtros = pedidos(request, "q", "estado", "modelo", "lote", "desde", "hasta")
    filtradas = _filtrar_ordenes(ordenes, filtros)

    ahora = datetime.now()

    contexto = {
        "ordenes": filtradas,
        "modelos": modelos if isinstance(modelos, list) else [],
        "estados": estados if isinstance(estados, list) else [],
        "lotes": lotes if isinstance(lotes, list) else [],
        # Valores por defecto del modal de alta.
        "hoy": ahora.date().isoformat(),
        "hora_ahora": ahora.strftime("%H:%M"),
    }
    contexto.update(contexto_de_filtros(filtros, ordenes, filtradas))

    return render(request, "panel_supervisor/produccion/lista_ordenes.html", contexto)


@requiere_rol(ROL_SUPERVISOR)
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

    return redirect('panel_supervisor:ordenes-produccion-lista')


@requiere_rol(ROL_SUPERVISOR)
def ordenProduccionCancelarView(request, folio):
    """Cancela la orden y deja la planta consistente.

    Antes esto era un DELETE que sólo movía el estado a Cancelada y dejaba el
    material apartado en laptops que ya nadie iba a terminar. Ahora lo resuelve
    sp_Cancelar_Orden_Produccion, que además libera los componentes de las
    laptops a medias y las rechaza, todo en una transacción. Las Aprobadas y
    Embaladas se respetan: ya pasaron calidad."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.post(f"{API}/produccion/{folio}/cancelar/", json={}, headers=headers)

        if respuesta.status_code == 200:
            resumen = respuesta.json()
            messages.success(
                request,
                f"Orden #{folio} cancelada. "
                f"{resumen.get('laptops_rechazadas', 0)} laptop(s) rechazada(s), "
                f"{resumen.get('componentes_liberados', 0)} componente(s) devuelto(s) al inventario"
                + (f", {resumen['laptops_respetadas']} laptop(s) terminada(s) sin tocar."
                   if resumen.get('laptops_respetadas') else ".")
            )
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('panel_supervisor:ordenes-produccion-lista')


@requiere_rol(ROL_SUPERVISOR)
def ordenProduccionIniciarEnsamblajeView(request, folio):
    """Da de alta de un jalón las laptops que le faltan a la orden.

    No se manda línea: la laptop no la guarda. En cuál se arma cada una lo dice
    su registro de ensamblaje, y el supervisor lo abre después desde su propia
    pantalla, ya contra su línea."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)
        respuesta = requests.post(
            f"{API}/produccion/{folio}/iniciar-ensamblaje/",
            json={},
            headers=headers,
        )

        if respuesta.status_code == 200:
            creadas = respuesta.json().get('laptops_creadas', 0)
            messages.success(
                request,
                f"Se registraron {creadas} laptop(s) para la orden #{folio}."
            )
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('panel_supervisor:orden-produccion-detalle', folio=folio)


@requiere_rol(ROL_SUPERVISOR)
def ordenProduccionDetalleView(request, folio):
    """Ficha de la orden con las laptops que se le registraron y en qué va el
    ensamblaje de cada una."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    orden = _json(f"{API}/produccion/{folio}/", headers)
    if not isinstance(orden, dict) or not orden.get("folio"):
        messages.error(request, "No se encontró esa orden de producción.")
        return redirect('panel_supervisor:ordenes-produccion-lista')

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
    # Las rechazadas se leen de la orden (cant_rechazada, que llevan los
    # triggers) y no se recuentan aquí: es el mismo número, y ya viene en la
    # misma respuesta.
    rechazadas = orden.get("cant_rechazada") or 0

    return render(
        request,
        "panel_supervisor/produccion/detalle_orden.html",
        {
            "orden": orden,
            "laptops": laptops,
            "planificadas": planificadas,
            "registradas": registradas,
            "terminados": terminados,
            "en_proceso": en_proceso,
            "embaladas": embaladas,
            "rechazadas": rechazadas,
            # Se topa en 100 para que la barra no se desborde si se registraron too many
            "porcentaje": min(100, round(registradas * 100 / planificadas)) if planificadas else 0,
            # Para las dos acciones del encabezado: sólo tienen sentido mientras
            # la orden siga abierta.
            "abierta": orden.get("estado_codigo") in EDOS_ORDEN_ABIERTA,
            "faltantes": max(0, planificadas - registradas),
        }
    )


# 
#   LAPTOPS
# 

# Estados en los que la laptop ya cerró su ciclo productivo y no se le deben
# quitar piezas. Es el mismo criterio del trigger
# tg_Validar_Apertura_Ensamblaje (ver DB/triggers.sql).
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
    inspecciones = _json(f"{API}/calidad/Inspeccion/Listar/", headers)
    if not isinstance(inspecciones, list):
        return []

    completas = []
    for fila in inspecciones:
        if str(fila.get("laptop_numero")) != str(numero):
            continue
        detalle = _json(
            f"{API}/calidad/Inspeccion/Detalle/{fila.get('numero')}/",
            headers,
        )
        # Si el detalle falla nos quedamos con lo que traía la lista.
        completas.append(detalle if isinstance(detalle, dict) and detalle.get("numero") else fila)

    return sorted(completas, key=lambda i: (str(i.get("fecha") or ""), str(i.get("hora") or "")))


def _embalajes_de_laptop(headers, num_serie):
    """Embalajes de la laptop. El endpoint de lista no devuelve el número de
    laptop, pero sí su num_serie, y como esa columna es única (IUK_serie_laptop)
    alcanza para cruzar sin pedir el detalle de cada registro."""
    if not num_serie:
        return []
    embalajes = _json(f"{API}/embalaje/Embalaje/Listar/", headers)
    if not isinstance(embalajes, list):
        return []
    propios = [e for e in embalajes
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
    regs = _json(f"{API}/produccion/registros-ensamblaje/", headers)
    if not isinstance(regs, list):
        return []

    laptops = _json(f"{API}/produccion/laptops/", headers)
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


@requiere_rol(ROL_SUPERVISOR)
def ensamblajeSeguimientoView(request):
    """Seguimiento de ensamblaje: todos los registros de la planta, con filtros
    y acceso al expediente de cada laptop. Responde de un vistazo qué se está
    armando ahora mismo y qué ya cerró."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    lineas = _json(f"{API}/lineas/", headers)
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
        "panel_supervisor/produccion/seguimiento_ensamblaje.html",
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
    def catalogo(url):
        datos = _json(url, headers)
        return datos if isinstance(datos, list) else []

    ordenes = catalogo(f"{API}/produccion/")

    return {
        "modelos": catalogo(f"{API}/produccion/modelos/"),
        "estados": catalogo(f"{API}/produccion/estados-laptop/"),
        "lineas": catalogo(f"{API}/lineas/"),
        "lotes": catalogo(f"{API}/produccion/lotes/"),
        "ordenes": ordenes,
        # Solo contra estas se puede registrar: una Completada o Cancelada ya
        # no admite laptops nuevas.
        "ordenes_abiertas": [o for o in ordenes
                             if o.get("estado_codigo") in EDOS_ORDEN_ABIERTA],
    }


@requiere_rol(ROL_SUPERVISOR)
def laptopsListView(request):
    """Consulta general de laptops (lee de vista_laptops) con filtros, y alta
    de una nueva."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    if request.method == "POST":

        laptops_actuales = _json(f"{API}/produccion/laptops/", headers)
        if not isinstance(laptops_actuales, list):
            laptops_actuales = []

        orden = request.POST.get("orden") or None
        if not orden:
            messages.error(request, "Selecciona la orden de producción: de ahí "
                                    "salen el modelo y el lote de la laptop.")
            return redirect('panel_supervisor:laptops-lista')

        # Ni modelo ni lote ni estado se capturan: los dos primeros los hereda de
        # su orden (la API los resuelve) y el estado siempre es Registrada.
        # La línea tampoco: la laptop no la guarda. Se sabrá en qué línea va
        # cuando se le abra su registro de ensamblaje.
        payload = {
            "num_serie": (request.POST.get("num_serie") or "").strip()
                         or _serie_temporal_sugerida(laptops_actuales),
            "orden": orden,
            "estado": EDO_LAPTOP_REGISTRADA,
        }

        respuesta = requests.post(f"{API}/produccion/laptops/", json=payload, headers=headers)

        if respuesta.status_code == 201:
            messages.success(request, "Laptop registrada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

        return redirect('panel_supervisor:laptops-lista')

    laptops = _json(f"{API}/produccion/laptops/", headers)
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

    return render(request, "panel_supervisor/produccion/lista_laptops.html", contexto)


@requiere_rol(ROL_SUPERVISOR)
def laptopDetalleView(request, numero):
    """Expediente completo de la laptop: sus datos editables, el seguimiento de
    todo su paso por la planta (ensamblajes, calidad y embalaje), los tiempos,
    qué le falta contra su lista de materiales y los componentes que trae
    montados, con la opción de liberarlos."""

    if 'token' not in request.session:
        return redirect('login')

    headers = _headers(request)

    laptop = _json(f"{API}/produccion/laptops/{numero}/", headers)
    if not isinstance(laptop, dict) or not laptop.get("numero"):
        messages.error(request, "No se encontró esa laptop.")
        return redirect('panel_supervisor:laptops-lista')

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
    estados_comp = _json(f"{API}/componentes/estados/", headers)
    estados_comp = ([e for e in estados_comp if e.get("codigo") != EDO_COMP_EN_USO]
                    if isinstance(estados_comp, list) else [])

    contexto.update({
        "laptop": laptop,
        "registros": registros,
        "componentes": componentes,
        # Hay algo que soltar sólo si queda un componente que no esté mermado:
        # los mermados se quedan pegados al ensamblaje a propósito, y sin esto el
        # botón de desarmar seguiría ahí sin nada que hacer.
        "desarmable": any(c.get("estado_codigo") != EDO_COMP_MERMADO for c in componentes),
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

    return render(request, "panel_supervisor/produccion/detalle_laptop.html", contexto)


@requiere_rol(ROL_SUPERVISOR)
def laptopEditarView(request, numero):
    """Guarda los datos de la laptop. Se manda PATCH para tocar solo lo que
    viene en el formulario."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        # Cuatro campos quedan fuera del payload a propósito:
        #   num_serie     — se fija al registrar y solo la reescribe el trigger
        #                   tg_Generar_Numero_Serie_Final al aprobar en calidad.
        #   modelo y lote — se heredan de la orden; la API los recalcula sola en
        #                   cada guardado, así que mandarlos no serviría de nada.
        #   linea         — la laptop no la guarda: sale de su registro de
        #                   ensamblaje, que se edita en su propia pantalla.
        payload = {
            "orden": request.POST.get("orden") or None,
            "estado": request.POST.get("estado") or None,
        }

        respuesta = requests.patch(
            f"{API}/produccion/laptops/mod/{numero}/", json=payload, headers=headers)

        if respuesta.status_code in (200, 202):
            messages.success(request, "Laptop actualizada correctamente.")
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('panel_supervisor:laptop-detalle', numero=numero)


@requiere_rol(ROL_SUPERVISOR)
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

    return redirect('panel_supervisor:laptops-lista')


@requiere_rol(ROL_SUPERVISOR)
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
        laptop = _json(f"{API}/produccion/laptops/{numero}/", headers)
        laptop = laptop if isinstance(laptop, dict) else {}

        if laptop.get("estado_codigo") in ESTADOS_LAPTOP_FINALIZADOS:
            messages.error(
                request,
                "No se pueden quitar componentes: la laptop está "
                f"{laptop.get('estado_nombre') or 'finalizada'}."
            )
            return redirect('panel_supervisor:laptop-detalle', numero=numero)

        nuevo_estado = request.POST.get("estado") or EDO_COMP_DISPONIBLE
        if nuevo_estado == EDO_COMP_EN_USO:
            messages.error(request, "Un componente liberado no puede quedar En Uso.")
            return redirect('panel_supervisor:laptop-detalle', numero=numero)

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

    return redirect('panel_supervisor:laptop-detalle', numero=numero)


@requiere_rol(ROL_SUPERVISOR)
def laptopDesarmarView(request, numero):
    """Desarma la laptop completa: suelta TODOS sus componentes de un golpe.

    Es el hermano mayor de laptopComponenteLiberarView, que quita uno solo. Lo
    resuelve sp_Liberar_Componentes_Laptop, que además cierra el registro de
    ensamblaje.

    OJO: al cerrarlo, tg_Validar_Apertura_Ensamblaje ya no deja abrirle otro,
    o sea que la laptop no se vuelve a armar. Por eso la plantilla lo pregunta
    con todas sus letras antes de mandar el POST."""

    if 'token' not in request.session:
        return redirect('login')

    if request.method == "POST":

        headers = _headers(request)

        nuevo_estado = request.POST.get("estado") or EDO_COMP_DISPONIBLE
        if nuevo_estado == EDO_COMP_EN_USO:
            messages.error(request, "Un componente liberado no puede quedar En Uso.")
            return redirect('panel_supervisor:laptop-detalle', numero=numero)

        respuesta = requests.post(
            f"{API}/produccion/laptops/{numero}/liberar-componentes/",
            json={"estado": nuevo_estado},
            headers=headers,
        )

        if respuesta.status_code == 200:
            resumen = respuesta.json()
            mermados = resumen.get('mermados_conservados', 0)
            messages.success(
                request,
                f"Laptop #{numero} desarmada: "
                f"{resumen.get('componentes_liberados', 0)} componente(s) liberado(s)"
                + (f" ({mermados} mermado(s) se quedaron como estaban)." if mermados else ".")
            )
        else:
            messages.error(request, _mensaje_api(respuesta))

    return redirect('panel_supervisor:laptop-detalle', numero=numero)


#--------------------------------------------------------------------------------
#                         P A R O S
#---------------------------------------------------------------------------------


API_PARO = "http://127.0.0.1:8000/api/produccion/paros/"


class ListaParos(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)

    template_name = "panel_supervisor/produccion/paros.html"

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
            response = get(API_PARO + "buscar/", headers, params=params)
        else:
            response = get(API_PARO, headers, params=params)

        paros = lista(response)

        context = {
            "paros": paros,
            "lineas": get_choices_lineas_paro(token),
            "buscar": buscar,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        }
        return render(request, self.template_name, context)


class CrearParo(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)

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

        return redirect("panel_supervisor:lista_paros")


class EditarParo(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)

    def post(self, request, numero):
        token = request.session.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        det_resp = get(API_PARO + f"{numero}/", headers)
        detalle = objeto(det_resp)

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

        return redirect("panel_supervisor:lista_paros")


class CerrarParo(RolRequeridoMixin, generic.View):
    roles_permitidos = (ROL_SUPERVISOR,)

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

        return redirect("panel_supervisor:lista_paros")