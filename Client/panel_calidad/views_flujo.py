"""Flujo guiado de calidad: una laptop, de principio a fin de la línea.

El operador de calidad no elige línea. Es la suya, la que sale de su empleado
(empleado_linea, ver core.lineas.de_la_sesion). Sobre ella hace tres pasos
seguidos:

    1. Elegir una laptop con ensamblaje ABIERTO en su línea.
    2. Registrar el ensamblaje: marcar las piezas que su línea instala, en el
       orden que dicta tipo_comp.necesario.
    3. Inspeccionar: marcar las que fallan, y aprobar o rechazar.

Lo que NO está aquí es el cierre del ensamblaje, y es a propósito: lo hace la
inspección. Al registrarla, tg_Actualizar_Estado_Laptop_Inspeccion_Calidad sella
la fecha y hora de fin del registro y, si la línea tiene una siguiente de
ensamblaje, abre el de esa. Por eso este panel no ofrece el botón "Registrar y
Terminar" que sí tienen producción y supervisión: cerrar por ahí dejaría el
registro cerrado sin relevo y la laptop atorada sin línea siguiente.

Las funciones de cálculo se importan de `produccion.views` en vez de copiarse.
Los otros paneles sí duplican sus vistas —a propósito, para poder divergir— pero
el orden de montaje y los topes por tipo no deben divergir nunca: son la misma
regla de negocio, y una segunda copia acabaría desincronizada.
"""

import requests
from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import generic

from core.guards import RolRequeridoMixin
from core.lineas import de_la_sesion
from core.roles import ROL_CALIDAD

from produccion.views import (
    API,
    EDO_COMP_DISPONIBLE,
    EDO_COMP_EN_USO,
    _bom,
    _capacidad_por_tipo,
    _componentes_libres,
    _headers,
    _json,
    _mensaje_api,
    _montado_por_modelo,
    _necesario_por_tipo,
    _orden_de_montaje,
    _registros_de_laptop,
    _todos_los_componentes,
    limpiar_fallos,
    motivo_ultimo_fallo,
)

API_INSPECCION = f"{API}/calidad/Inspeccion/"

# Resultados que este flujo ofrece. "Continuar ensamblaje" queda fuera a
# propósito: aquí la inspección siempre concluye la línea, y el trigger decide
# si eso significa pasar a la siguiente o aprobar en definitiva.
RESULTADO_APROBADA = "1"
RESULTADO_RECHAZADA = "0"


def _mi_linea(request):
    """La línea del operador de calidad que inició sesión, o None."""
    return de_la_sesion(request)


def _laptops_de_mi_linea(headers, linea):
    """Laptops con un ensamblaje ABIERTO en esa línea.

    Son las que están paradas ahí ahora mismo: la línea anterior ya las relevó
    y todavía no se les registra la inspección que las pasa a la siguiente.
    """
    registros = _json(f"{API}/produccion/registros-ensamblaje/", headers)
    if not isinstance(registros, list):
        return []

    abiertos = [r for r in registros
                if not r.get("fecha_fin") and str(r.get("linea")) == str(linea)]
    if not abiertos:
        return []

    laptops = _json(f"{API}/produccion/laptops/", headers)
    por_numero = {str(l.get("numero")): l for l in laptops} if isinstance(laptops, list) else {}

    pendientes = []
    for registro in abiertos:
        laptop = por_numero.get(str(registro.get("laptop")))
        if not laptop:
            continue
        pendientes.append({
            **laptop,
            "registro_numero": registro.get("numero"),
            "registro_inicio": registro.get("fecha_inicio"),
            "registro_hora": registro.get("hora_inicio"),
        })

    return sorted(pendientes, key=lambda l: l.get("numero") or 0)


def _contexto_checklist(headers, laptop_obj, linea):
    """El mismo cálculo que la pantalla de ensamblaje de producción.

    Devuelve (componentes, tipos_info, ocultos, tipos_ciclicos, registro).
    """
    filas_bom = _bom(headers, laptop_obj.get("modelo_codigo"))
    cap_tipo = _capacidad_por_tipo(filas_bom)
    nombre_de_tipo = {f.get("componente_tipo"): f.get("componente_tipo_nombre")
                      for f in filas_bom}

    requisito_tipo, profundidad_tipo, ciclicos = _orden_de_montaje(
        _necesario_por_tipo(headers), set(cap_tipo)
    )

    comps = _todos_los_componentes(headers)
    libres = _componentes_libres(comps, linea)

    registros = _registros_de_laptop(headers, laptop_obj.get("numero"))
    registro = next((r for r in reversed(registros) if not r.get("fecha_fin")), None)
    ya_montado = _montado_por_modelo(comps, [r.get("numero") for r in registros])

    montado_tipo = {}
    for fila in filas_bom:
        codigo = fila.get("componente_codigo")
        if ya_montado.get(codigo):
            tipo = fila.get("componente_tipo")
            montado_tipo[tipo] = montado_tipo.get(tipo, 0) + ya_montado[codigo]

    componentes, tipos_info, ocultos = [], {}, 0
    for fila in filas_bom:
        codigo = fila.get("componente_codigo")
        tipo_codigo = fila.get("componente_tipo")
        disponibles = len(libres.get(codigo, []))
        capacidad = fila.get("capacidad") or 1
        cap_t = cap_tipo.get(tipo_codigo, capacidad)
        libres_tipo = cap_t - montado_tipo.get(tipo_codigo, 0)
        requiere = requisito_tipo.get(tipo_codigo)

        tipos_info.setdefault(tipo_codigo, {
            "nombre": fila.get("componente_tipo_nombre") or tipo_codigo,
            "capacidad": cap_t,
            "montado": montado_tipo.get(tipo_codigo, 0),
            "requiere": requiere,
        })

        if disponibles == 0:
            ocultos += 1
            continue

        componentes.append({
            "codigo": codigo,
            "nombre": fila.get("componente_nombre"),
            "tipo": fila.get("componente_tipo_nombre") or tipo_codigo,
            "tipo_codigo": tipo_codigo,
            "capacidad_tipo": cap_t,
            "capacidad": capacidad,
            "disponibles": disponibles,
            "montado": ya_montado.get(codigo, 0),
            "maximo": max(0, min(capacidad, disponibles, libres_tipo)),
            "sin_stock": False,
            "tipo_lleno": libres_tipo <= 0,
            "requiere_tipo": requiere or "",
            "requiere_nombre": nombre_de_tipo.get(requiere) or requiere or "",
            "profundidad": profundidad_tipo.get(tipo_codigo, 0),
            "orden_pendiente": bool(requiere) and montado_tipo.get(requiere, 0) < 1,
        })

    componentes.sort(key=lambda c: (c["profundidad"], -c["disponibles"],
                                    (c["nombre"] or c["codigo"]).lower()))

    ciclicos_nombres = sorted(nombre_de_tipo.get(t) or t for t in ciclicos)
    return componentes, tipos_info, ocultos, ciclicos_nombres, registro


def _piezas_montadas(headers, laptop):
    """Las piezas que la laptop lleva puestas AHORA, de todas sus líneas.

    Es lo que el inspector puede reprobar: no solo lo que montó su línea, porque
    una falla puede venir de cualquier etapa anterior.
    """
    comps = _todos_los_componentes(headers)
    numeros = {str(r.get("numero")) for r in _registros_de_laptop(headers, laptop)}

    puestas = [c for c in comps
               if str(c.get("registro_ensamblaje")) in numeros
               and c.get("estado_codigo") == EDO_COMP_EN_USO]

    return sorted(puestas, key=lambda c: (c.get("tipo_nombre") or "",
                                          c.get("modelo_nombre") or ""))


class _BaseFlujo(RolRequeridoMixin, generic.View):
    """Todo el flujo exige rol de calidad y una línea asignada."""

    roles_permitidos = (ROL_CALIDAD,)

    def linea_o_redirect(self, request):
        # Cada pantalla arranca limpia: si una consulta falla, el motivo tiene
        # que ser el de ESTA petición y no el que dejó la anterior.
        limpiar_fallos()

        linea = _mi_linea(request)
        if not linea:
            messages.error(
                request,
                "Tu usuario no tiene una línea asignada, así que no se puede "
                "saber qué laptops te tocan. Pídele a un administrador que te "
                "asigne a una línea."
            )
            return None
        return linea

    def avisar_si_fallo(self, request):
        """Si alguna consulta se cayó, decir por qué en vez de pintar vacío.

        Sin esto una pantalla sin datos y una pantalla sin permisos se ven igual,
        y el operador no tiene forma de saber cuál de las dos le tocó."""
        fallo = motivo_ultimo_fallo()
        if fallo:
            messages.error(
                request,
                f"No se pudieron cargar todos los datos: {fallo['motivo']} "
                f"(al consultar {fallo['url']})"
            )


class SeleccionarLaptop(_BaseFlujo):
    """Paso 1 — las laptops paradas en mi línea."""

    template_name = "panel_calidad/flujo_laptops.html"

    def get(self, request):
        linea = self.linea_o_redirect(request)
        if not linea:
            return redirect("panel_calidad:dashboard")

        headers = _headers(request)
        laptops = _laptops_de_mi_linea(headers, linea["codigo"])
        self.avisar_si_fallo(request)

        return render(request, self.template_name, {
            "linea": linea,
            "laptops": laptops,
        })


class RegistrarEnsamblaje(_BaseFlujo):
    """Paso 2 — el checklist de la línea, en el orden de montaje."""

    template_name = "panel_calidad/flujo_ensamblaje.html"

    def get(self, request, laptop):
        linea = self.linea_o_redirect(request)
        if not linea:
            return redirect("panel_calidad:dashboard")

        headers = _headers(request)
        laptop_obj = _json(f"{API}/produccion/laptops/{laptop}/", headers)
        if not isinstance(laptop_obj, dict):
            messages.error(request, "No se encontró esa laptop.")
            return redirect("panel_calidad:flujo-laptops")

        componentes, tipos_info, ocultos, ciclicos, registro = _contexto_checklist(
            headers, laptop_obj, linea["codigo"]
        )

        if not registro:
            messages.error(
                request,
                f"La laptop #{laptop} no tiene un ensamblaje abierto en {linea['codigo']}."
            )
            return redirect("panel_calidad:flujo-laptops")

        return render(request, self.template_name, {
            "linea": linea,
            "laptop_obj": laptop_obj,
            "componentes": componentes,
            "tipos_info": tipos_info,
            "ocultos_por_linea": ocultos,
            "tipos_ciclicos": ciclicos,
            "registro": registro,
        })

    def post(self, request, laptop):
        linea = self.linea_o_redirect(request)
        if not linea:
            return redirect("panel_calidad:dashboard")

        headers = _headers(request)
        laptop_obj = _json(f"{API}/produccion/laptops/{laptop}/", headers)
        laptop_obj = laptop_obj if isinstance(laptop_obj, dict) else {}

        filas_bom = _bom(headers, laptop_obj.get("modelo_codigo"))
        tipo_de = {f.get("componente_codigo"): f.get("componente_tipo") for f in filas_bom}
        nombre_tipo = {f.get("componente_tipo"): f.get("componente_tipo_nombre")
                       for f in filas_bom}
        cap_tipo = _capacidad_por_tipo(filas_bom)

        comps = _todos_los_componentes(headers)
        registros = _registros_de_laptop(headers, laptop)
        registro = next((r for r in reversed(registros) if not r.get("fecha_fin")), None)
        if not registro:
            messages.error(request, "Esa laptop ya no tiene un ensamblaje abierto.")
            return redirect("panel_calidad:flujo-laptops")

        ya_montado = _montado_por_modelo(comps, [r.get("numero") for r in registros])

        seleccion = {}
        for clave in request.POST:
            if not clave.startswith("comp_"):
                continue
            codigo = clave[len("comp_"):]
            try:
                seleccion[codigo] = int(request.POST.get(f"cant_{codigo}") or 1)
            except ValueError:
                seleccion[codigo] = 1

        if not seleccion:
            messages.info(request, "No marcaste ninguna pieza.")
            return redirect("panel_calidad:flujo-ensamblaje", laptop=laptop)

        # Mismas dos validaciones que producción, por si alguien fuerza el POST:
        # ni pasarse de las ranuras del tipo ni saltarse el orden de montaje.
        usado_por_tipo = {}
        for codigo, cantidad in list(ya_montado.items()):
            tipo = tipo_de.get(codigo)
            usado_por_tipo[tipo] = usado_por_tipo.get(tipo, 0) + cantidad
        for codigo, cantidad in seleccion.items():
            tipo = tipo_de.get(codigo)
            usado_por_tipo[tipo] = usado_por_tipo.get(tipo, 0) + cantidad

        excedidos = [
            f"{nombre_tipo.get(t) or t}: {usado} de {cap_tipo.get(t, 1)} permitido(s)"
            for t, usado in usado_por_tipo.items()
            if usado > cap_tipo.get(t, 1)
        ]
        if excedidos:
            messages.error(request, "No se registró: se excede la capacidad por tipo — "
                           + "; ".join(excedidos))
            return redirect("panel_calidad:flujo-ensamblaje", laptop=laptop)

        requisito_tipo, _prof, _cic = _orden_de_montaje(
            _necesario_por_tipo(headers), set(cap_tipo)
        )
        seleccion_por_tipo = {}
        for codigo, cantidad in seleccion.items():
            tipo = tipo_de.get(codigo)
            seleccion_por_tipo[tipo] = seleccion_por_tipo.get(tipo, 0) + cantidad

        fuera_de_orden = [
            f"{nombre_tipo.get(t) or t} va después de "
            f"{nombre_tipo.get(requisito_tipo[t]) or requisito_tipo[t]}"
            for t in seleccion_por_tipo
            if requisito_tipo.get(t) and usado_por_tipo.get(requisito_tipo[t], 0) < 1
        ]
        if fuera_de_orden:
            messages.error(request, "No se registró: hay que respetar el orden de montaje — "
                           + "; ".join(fuera_de_orden))
            return redirect("panel_calidad:flujo-ensamblaje", laptop=laptop)

        libres = _componentes_libres(comps, linea["codigo"])
        montados, faltantes = 0, []

        for codigo, cantidad in seleccion.items():
            disponibles = libres.get(codigo, [])
            if len(disponibles) < cantidad:
                faltantes.append(f"{codigo} (pediste {cantidad}, hay {len(disponibles)})")

            for pieza in disponibles[:cantidad]:
                respuesta = requests.patch(
                    f"{API}/componentes/mod/{pieza['numero']}/",
                    json={"registro_ensamblaje": registro.get("numero"),
                          "estado": EDO_COMP_EN_USO},
                    headers=headers,
                )
                if respuesta.status_code in (200, 202):
                    montados += 1

        aviso = f"{montados} componente(s) agregado(s) a la laptop #{laptop}."
        if faltantes:
            messages.warning(request, aviso + " Sin stock suficiente de: " + "; ".join(faltantes))
        else:
            messages.success(request, aviso)

        return redirect("panel_calidad:flujo-ensamblaje", laptop=laptop)


class Inspeccionar(_BaseFlujo):
    """Paso 3 — la inspección, que es la que cierra la línea."""

    template_name = "panel_calidad/flujo_inspeccion.html"

    def get(self, request, laptop):
        linea = self.linea_o_redirect(request)
        if not linea:
            return redirect("panel_calidad:dashboard")

        headers = _headers(request)
        laptop_obj = _json(f"{API}/produccion/laptops/{laptop}/", headers)
        if not isinstance(laptop_obj, dict):
            messages.error(request, "No se encontró esa laptop.")
            return redirect("panel_calidad:flujo-laptops")

        estados = _json(f"{API}/componentes/estados/", headers)
        estados = ([e for e in estados
                    if e.get("codigo") not in (EDO_COMP_EN_USO, EDO_COMP_DISPONIBLE)]
                   if isinstance(estados, list) else [])

        return render(request, self.template_name, {
            "linea": linea,
            "laptop_obj": laptop_obj,
            "piezas": _piezas_montadas(headers, laptop),
            "estados_componente": estados,
        })

    def post(self, request, laptop):
        linea = self.linea_o_redirect(request)
        if not linea:
            return redirect("panel_calidad:dashboard")

        headers = _headers(request)
        empleado = request.session.get("empleado")
        ahora = datetime.now()

        # Piezas marcadas como fallidas.
        fallas = []
        for clave in request.POST:
            if not clave.startswith("falla_"):
                continue
            numero = clave[len("falla_"):]
            fallas.append({
                "componente": numero,
                "estado": request.POST.get(f"estado_{numero}"),
                "observacion": request.POST.get(f"obs_{numero}") or "",
            })

        # Una pieza marcada es un rechazo. No se deja aprobar un equipo del que
        # el propio inspector acaba de decir que trae una pieza mala.
        resultado = RESULTADO_RECHAZADA if fallas else request.POST.get("resultado")
        if resultado not in (RESULTADO_APROBADA, RESULTADO_RECHAZADA):
            messages.error(request, "Elige si la laptop se aprueba o se rechaza.")
            return redirect("panel_calidad:flujo-inspeccion", laptop=laptop)

        # 1) La inspección. Su alta dispara el trigger que cierra el registro de
        #    esta línea y, si aprueba y hay siguiente de ensamblaje, abre el de
        #    esa. Si rechaza, la laptop pasa a RECHA y ahí termina.
        respuesta = requests.post(
            API_INSPECCION + "Registrar/",
            headers=headers,
            data={
                "resultado": resultado,
                "observaciones": request.POST.get("observaciones") or "",
                "fecha": ahora.strftime("%Y-%m-%d"),
                "hora": ahora.strftime("%H:%M:%S"),
                "laptop": laptop,
                "empleado": empleado,
                "linea": linea["codigo"],
            },
        )
        if respuesta.status_code != 201:
            messages.error(request, _mensaje_api(respuesta))
            return redirect("panel_calidad:flujo-inspeccion", laptop=laptop)

        numero_inspeccion = (respuesta.json() or {}).get("numero")

        # 2) Los renglones de la inspección, ANTES de tocar las piezas: la API
        #    valida que el componente siga montado en esa laptop, y el paso 3 lo
        #    desmonta.
        if fallas and numero_inspeccion:
            detalle = requests.post(
                API_INSPECCION + "Detalle/Registrar/",
                headers=headers,
                json=[{"inspeccion": numero_inspeccion,
                       "componente": f["componente"],
                       "observacion": f["observacion"]} for f in fallas],
            )
            if detalle.status_code != 201:
                messages.warning(
                    request,
                    "La inspección se registró, pero no se pudo guardar el detalle "
                    "de las piezas: " + _mensaje_api(detalle)
                )

        # 3) Y ahora sí, las piezas malas salen de la laptop con su estado.
        for falla in fallas:
            requests.patch(
                f"{API}/componentes/mod/{falla['componente']}/",
                json={"registro_ensamblaje": None,
                      "estado": falla["estado"] or None},
                headers=headers,
            )

        if resultado == RESULTADO_RECHAZADA:
            messages.success(
                request,
                f"Laptop #{laptop} rechazada en {linea['codigo']}"
                + (f", con {len(fallas)} pieza(s) marcada(s)." if fallas else ".")
            )
        else:
            messages.success(
                request,
                f"Laptop #{laptop} aprobada en {linea['codigo']}. "
                "Si hay línea siguiente, su ensamblaje ya quedó abierto ahí."
            )

        return redirect("panel_calidad:flujo-laptops")
