from datetime import datetime, time

from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages

# Core Imports (Consolidados)
from core.api import get, headers, lista, objeto, url
from core.guards import RolRequeridoMixin
from core.roles import ROL_ADMIN
from core.templatetags.formato import fecha_hora
# Importamos nuestros servicios de generación de reportes
from .reportes import generar_pdf_expediente, generar_excel_calidad, generar_excel_embalaje

# URL base de la API (Servicios)
API = "http://127.0.0.1:8000/api"

# Configuración
ORDENES_SUGERIDAS = 15
RESULTADOS = {
    1: ('Aprobada', 'ok'),
    0: ('Rechazada', 'mal'),
    2: ('Continuar', 'medio'),
}

# ==============================================================================
# HELPER FUNCTIONS (API Y FECHAS)
# ==============================================================================

def _headers(request):
    return {"Authorization": f"Bearer {request.session.get('token')}"}

def _json(url_endpoint, headers_dict, params=None):
    respuesta = get(url_endpoint, headers_dict, params=params)
    if respuesta is None or respuesta.status_code != 200:
        return None
    try:
        return respuesta.json()
    except ValueError:
        return None

def _momento(fecha, hora):
    if not fecha: return None
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
    if not minutos: return None
    if minutos < 60: return f"{minutos} min"
    horas, resto = divmod(minutos, 60)
    if horas < 24: return f"{horas} h {resto} min" if resto else f"{horas} h"
    dias, horas = divmod(horas, 24)
    return f"{dias} d {horas} h" if horas else f"{dias} d"

def _duracion(desde, hasta):
    if not desde or not hasta or hasta < desde: return None
    return _duracion_min(int((hasta - desde).total_seconds() // 60))

# ==============================================================================
# RECOLECTORES DE DATOS PARA LA LAPTOP
# ==============================================================================

def _inspecciones_de_laptop(headers_dict, numero):
    inspecciones = _json(f"{API}/calidad/Inspeccion/Listar/", headers_dict)
    if not isinstance(inspecciones, list): return []

    completas = []
    for fila in inspecciones:
        if str(fila.get("laptop_numero")) != str(numero): continue
        detalle = _json(f"{API}/calidad/Inspeccion/Detalle/{fila.get('numero')}/", headers_dict)
        completas.append(detalle if isinstance(detalle, dict) and detalle.get("numero") else fila)

    return sorted(completas, key=lambda i: (str(i.get("fecha") or ""), str(i.get("hora") or "")))

def _embalajes_de_laptop(headers_dict, num_serie):
    if not num_serie: return []
    embalajes = _json(f"{API}/embalaje/Embalaje/Listar/", headers_dict)
    if not isinstance(embalajes, list): return []
    
    propios = [e for e in embalajes if str(e.get("laptop_num_serie") or "") == str(num_serie)]
    return sorted(propios, key=lambda e: (str(e.get("fecha") or ""), str(e.get("hora") or "")))

def _bitacora(registros, inspecciones, embalajes):
    eventos = []
    for r in registros:
        numero = r.get("numero")
        eventos.append({
            "momento": _momento(r.get("fecha_inicio"), r.get("hora_inicio")),
            "fecha": r.get("fecha_inicio"), "hora": r.get("hora_inicio"),
            "titulo": f"Ensamblaje #{numero} iniciado",
            "detalle": f"Línea {r.get('linea_nombre') or r.get('linea') or '—'}",
            "icono": "bi-play-circle", "clase": "primary",
        })
        if r.get("fecha_fin"):
            eventos.append({
                "momento": _momento(r.get("fecha_fin"), r.get("hora_fin")),
                "fecha": r.get("fecha_fin"), "hora": r.get("hora_fin"),
                "titulo": f"Ensamblaje #{numero} terminado",
                "detalle": f"Duró {r.get('duracion')}" if r.get("duracion") else "",
                "icono": "bi-check-circle", "clase": "success",
            })

    for i in inspecciones:
        resultado = i.get("resultado")
        icono, clase = ("bi-patch-check", "success") if resultado == 1 else ("bi-x-octagon", "danger") if resultado == 0 else ("bi-arrow-repeat", "warning")
        partes = [p for p in (i.get("empleado_nombre"), i.get("linea_nombre")) if p]

        eventos.append({
            "momento": _momento(i.get("fecha"), i.get("hora")),
            "fecha": i.get("fecha"), "hora": i.get("hora"),
            "titulo": f"Inspección #{i.get('numero')} · {i.get('resultado_nombre') or 'Inspección'}",
            "detalle": " · ".join(partes),
            "observaciones": i.get("observaciones"),
            "icono": icono, "clase": clase,
        })

    for e in embalajes:
        eventos.append({
            "momento": _momento(e.get("fecha"), e.get("hora")),
            "fecha": e.get("fecha"), "hora": e.get("hora"),
            "titulo": f"Embalada · embalaje #{e.get('numero')}",
            "detalle": e.get("tipo_nombre") or "",
            "icono": "bi-box-seam", "clase": "dark",
        })

    eventos.sort(key=lambda ev: (ev["momento"] is None, ev["momento"] or datetime.min))
    return eventos

def _todos_los_componentes(headers_dict):
    comps = _json(f"{API}/componentes/", headers_dict)
    return comps if isinstance(comps, list) else []

def _componentes_montados(headers_dict, registros):
    numeros = {str(r.get("numero")) for r in registros}
    if not numeros: return []
    montados = [c for c in _todos_los_componentes(headers_dict) if str(c.get("registro_ensamblaje")) in numeros]
    return sorted(montados, key=lambda c: ((c.get("modelo_nombre") or "").lower(), c.get("numero") or 0))

def _obtener_supervisor_linea(headers_dict, linea_codigo):
    if not linea_codigo: 
        return "Sin línea asignada"
        
    # ¡Aprovechamos tu VistaEmpleado que ya tiene todo cruzado!
    empleados = _json(f"{API}/usuarios/Empleado/Listar/", headers_dict)
    
    if not isinstance(empleados, list): 
        return "No asignado"
        
    linea_buscada = str(linea_codigo).strip()
    
    for emp in empleados:
        # Extraemos directamente los datos de la VistaEmpleado
        linea_emp = str(emp.get("linea_codigo") or "").strip()
        rol_emp = str(emp.get("rol_codigo") or "").strip().upper()
        estado_emp = str(emp.get("estado_empleado") or "").strip().upper()
        
        # Validamos que esté en la línea correcta, sea SUPERVISOR y siga activo
        if linea_emp == linea_buscada and rol_emp == "SUPER" and estado_emp != "BAJA":
            return emp.get("nombre_completo") or "Supervisor (Sin nombre)"
            
    return "Supervisor no encontrado"

# ==============================================================================
# RECOLECTORES DE DATOS PARA LA ORDEN
# ==============================================================================

def _resultado(valor):
    return RESULTADOS.get(valor, ('Sin inspección', 'neutro'))

def _laptops(filas):
    for fila in filas:
        texto, clase = _resultado(fila.get('ultimo_resultado'))
        fila['resultado_texto'] = texto
        fila['resultado_clase'] = clase
    return filas

def _componentes(filas):
    tope = max([(f.get('piezas') or 0) for f in filas], default=0)
    for fila in filas:
        piezas = fila.get('piezas') or 0
        fila['ancho'] = round(100 * piezas / tope) if tope else 0
    return filas

def _avance(orden):
    planificada = orden.get('cant_planificada') or 0
    if not planificada: return []

    tramos = [
        ('Embaladas', 'embaladas', orden.get('laptops_embaladas') or 0),
        ('Aprobadas', 'aprobadas', orden.get('laptops_aprobadas') or 0),
        ('En ensamblaje', 'proceso', orden.get('laptops_en_ensamblaje') or 0),
        ('Rechazadas', 'rechazadas', orden.get('laptops_rechazadas') or 0),
    ]

    barra = []
    acumulado = 0
    for etiqueta, clase, cantidad in tramos:
        if not cantidad: continue
        ancho = min(round(100 * cantidad / planificada), max(0, 100 - acumulado))
        if not ancho: continue
        barra.append({'etiqueta': etiqueta, 'clase': clase, 'cantidad': cantidad, 'ancho': ancho})
        acumulado += ancho
    return barra

# ==============================================================================
# VISTAS PRINCIPALES (ENDPOINTS DEL CLIENTE)
# ==============================================================================

def trazabilidadView(request):
    """
    Buscador Inteligente Unificado.
    Detecta si es un Folio (Orden) o Serie (Laptop) y redirige.
    """
    if 'token' not in request.session:
        return redirect('login')

    query = (request.GET.get("q") or "").strip()
    if query:
        if query.isdigit():
            # ¡Aquí agregamos el namespace trazabilidad!
            return redirect('trazabilidad:trazabilidad_x_orden', folio=query)
        
        # ¡Aquí también agregamos el namespace trazabilidad!
        return redirect('trazabilidad:trazabilidad_x_laptop', num_serie=query)

    return render(request, "trazabilidad/trazabilidad.html")


def trazabilidadLaptopView(request, num_serie):
    """Auditoría completa de una unidad física (RF43 - RF50)."""
    if 'token' not in request.session:
        return redirect('login')

    headers_dict = _headers(request)
    
    # 1. Base Laptop (RF43)
    laptops = _json(f"{API}/produccion/laptops/", headers_dict)
    laptop_base = None
    if isinstance(laptops, list):
        laptop_base = next((l for l in laptops if str(l.get("num_serie")).lower() == num_serie.lower() or str(l.get("numero")) == num_serie), None)

    if not laptop_base:
        messages.error(request, f"No se encontró ninguna unidad con el identificador '{num_serie}'.")
        return render(request, "trazabilidad/trazabilidad.html", {"error": True, "query": num_serie})

    numero = laptop_base.get("numero")
    laptop = _json(f"{API}/produccion/laptops/{numero}/", headers_dict)

    # 2. Orden (RF44)
    orden = _json(f"{API}/produccion/{laptop.get('orden_folio')}/", headers_dict) if laptop.get('orden_folio') else {}
    if not isinstance(orden, dict): orden = {}

    # 3. Línea y Estaciones (RF45, RF46)
    registros = laptop.get("registros_ensamblaje") or []
    linea_codigo = laptop.get("linea_codigo") or (registros[-1].get("linea") if registros else None)
    
    linea_detalle = _json(f"{API}/lineas/{linea_codigo}/", headers_dict) if linea_codigo else {}
    estaciones = linea_detalle.get("estaciones", []) if isinstance(linea_detalle, dict) else []

    # 4. Componentes (RF47)
    componentes = _componentes_montados(headers_dict, registros)

    # 5. Supervisor (RF48)
    supervisor = _obtener_supervisor_linea(headers_dict, linea_codigo) if linea_codigo else "Sin línea asignada"

    # 6. Inspector (RF49)
    inspecciones = _inspecciones_de_laptop(headers_dict, numero)
    ultima_inspeccion = inspecciones[-1] if inspecciones else None
    inspector = ultima_inspeccion.get("empleado_nombre") if ultima_inspeccion else "Sin inspección registrada"

    # 7. Bitácora (RF50)
    embalajes = _embalajes_de_laptop(headers_dict, laptop.get("num_serie"))
    bitacora = _bitacora(registros, inspecciones, embalajes)

    return render(
        request,
        "trazabilidad/trazabilidad.html",
        {
            "laptop": laptop, "orden": orden, "linea": linea_detalle,
            "estaciones": estaciones, "componentes": componentes,
            "supervisor": supervisor, "inspector": inspector,
            "ultima_inspeccion": ultima_inspeccion, "bitacora": bitacora,
        }
    )


class TrazabilidadOrden(RolRequeridoMixin, generic.View):
    """Auditoría de un lote completo de producción (Folio)."""
    roles_permitidos = (ROL_ADMIN,)
    template_name = 'trazabilidad/trazabilidad_orden.html'

    def get(self, request, folio=None):
        cabeceras = _headers(request)

        if folio is None:
            escrito = (request.GET.get('folio') or '').strip()
            folio = int(escrito) if escrito.isdigit() else None

        contexto = {
            'folio': folio,
            'ordenes': lista(get(url('dashboard/trazabilidad/'), cabeceras))[:ORDENES_SUGERIDAS],
        }

        if folio is None:
            return render(request, self.template_name, contexto)

        respuesta = get(url(f'dashboard/trazabilidad/{folio}/'), cabeceras)
        datos = objeto(respuesta)

        if not datos:
            contexto['error'] = f'No existe la orden con folio {folio}.' if respuesta is not None and respuesta.status_code == 404 else 'No se pudo consultar la trazabilidad en este momento.'
            return render(request, self.template_name, contexto)

        orden = datos.get('orden') or {}

        contexto.update({
            'orden': orden,
            'laptops': _laptops(datos.get('laptops') or []),
            'componentes': _componentes(datos.get('componentes') or []),
            'paros': datos.get('paros') or [],
            'avance': _avance(orden),
        })

        return render(request, self.template_name, contexto)
    

def centroReportesView(request):
    """Renderiza la interfaz del Centro Unificado de Reportes."""
    if 'token' not in request.session:
        return redirect('login')
    
    return render(request, "trazabilidad/centro_reportes.html")
    
    
def exportarLaptopPDFView(request, num_serie):
    """RF51: Prepara los datos del expediente y solicita la generación del PDF."""
    if 'token' not in request.session:
        return redirect('login')

    headers_dict = _headers(request)
    
  
    laptops = _json(f"{API}/produccion/laptops/", headers_dict)
    laptop_base = next((l for l in laptops if str(l.get("num_serie")).lower() == num_serie.lower() or str(l.get("numero")) == num_serie), None) if isinstance(laptops, list) else None

    if not laptop_base:
        messages.error(request, f"No se encontró la unidad '{num_serie}'.")
        return redirect('trazabilidad:trazabilidad')

    numero = laptop_base.get("numero")
    laptop = _json(f"{API}/produccion/laptops/{numero}/", headers_dict)
    orden = _json(f"{API}/produccion/{laptop.get('orden_folio')}/", headers_dict) if laptop.get('orden_folio') else {}
    if not isinstance(orden, dict): orden = {}

    registros = laptop.get("registros_ensamblaje") or []
    linea_codigo = laptop.get("linea_codigo") or (registros[-1].get("linea") if registros else None)
    linea_detalle = _json(f"{API}/lineas/{linea_codigo}/", headers_dict) if linea_codigo else {}
    estaciones = linea_detalle.get("estaciones", []) if isinstance(linea_detalle, dict) else []

    componentes = _componentes_montados(headers_dict, registros)
    supervisor = _obtener_supervisor_linea(headers_dict, linea_codigo) if linea_codigo else "Sin línea asignada"

    inspecciones = _inspecciones_de_laptop(headers_dict, numero)
    ultima_inspeccion = inspecciones[-1] if inspecciones else None
    inspector = ultima_inspeccion.get("empleado_nombre") if ultima_inspeccion else "Sin inspección"

    embalajes = _embalajes_de_laptop(headers_dict, laptop.get("num_serie"))
    bitacora = _bitacora(registros, inspecciones, embalajes)

    # Armamos el diccionario
    contexto = {
        "laptop": laptop, "orden": orden, "linea": linea_detalle,
        "estaciones": estaciones, "componentes": componentes,
        "supervisor": supervisor, "inspector": inspector,
        "ultima_inspeccion": ultima_inspeccion, "bitacora": bitacora,
        "fecha_impresion": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    return generar_pdf_expediente(request, contexto, laptop.get("num_serie", num_serie))


def exportarCalidadExcelView(request):
    """RF52: Filtra los datos de calidad y solicita la generación del Excel."""
    if 'token' not in request.session:
        return redirect('login')

    headers_dict = _headers(request)
    
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')
    resultado = request.GET.get('resultado')

    inspecciones = _json(f"{API}/calidad/Inspeccion/Listar/", headers_dict)
    if not isinstance(inspecciones, list):
        inspecciones = []

    if fecha_desde:
        inspecciones = [i for i in inspecciones if (i.get('fecha') or "") >= fecha_desde]
    if fecha_hasta:
        inspecciones = [i for i in inspecciones if (i.get('fecha') or "") <= fecha_hasta]
    if resultado:
        inspecciones = [i for i in inspecciones if str(i.get('resultado')) == resultado]

  
    return generar_excel_calidad(inspecciones)


def exportarEmbalajeExcelView(request):
    """RF53: Filtra los datos de embalaje y solicita la generación del Excel."""
    if 'token' not in request.session:
        return redirect('login')

    headers_dict = _headers(request)
    
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')

    # Consultamos tu endpoint de Embalaje
    embalajes = _json(f"{API}/embalaje/Embalaje/Listar/", headers_dict)
    if not isinstance(embalajes, list):
        embalajes = []

    # Aplicamos los filtros de fecha
    if fecha_desde:
        embalajes = [e for e in embalajes if (e.get('fecha') or "") >= fecha_desde]
    if fecha_hasta:
        embalajes = [e for e in embalajes if (e.get('fecha') or "") <= fecha_hasta]

    
    return generar_excel_embalaje(embalajes)