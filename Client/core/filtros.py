"""Filtrado de listas para las barras de búsqueda de las pantallas.

Se filtra en el cliente y no en la API porque casi ningún endpoint acepta query
params todavía. Cuando alguno aprenda a filtrar, esa pantalla puede pasarle los
parámetros al get() y dejar de usar esto; mientras tanto, aquí está la lógica
una sola vez en lugar de repetida en cada vista.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""


def pedidos(request, *nombres):
    """Los filtros que vienen en la URL, ya normalizados.

    Devuelve todas las claves aunque estén vacías: la plantilla las necesita
    para volver a marcar lo que el usuario había elegido."""
    return {nombre: (request.GET.get(nombre) or "").strip() for nombre in nombres}


def _coincide(registro, campos, texto):
    """True si el texto aparece en alguno de esos campos del registro."""
    return any(texto in str(registro.get(campo) or "").lower() for campo in campos)


def filtrar(registros, filtros, exactos=(), busqueda=()):
    """Deja los registros que cumplen TODOS los filtros activos.

    'exactos' son pares (nombre del filtro, clave del registro) que se comparan
    completos —los códigos de los catálogos—, y 'busqueda' son las claves donde
    se busca el texto libre que el usuario escribió en la caja 'q'."""
    resultado = registros

    for filtro, clave in exactos:
        valor = filtros.get(filtro)
        if valor:
            resultado = [r for r in resultado if str(r.get(clave) or "") == valor]

    texto = filtros.get("q", "").lower()
    if texto:
        resultado = [r for r in resultado if _coincide(r, busqueda, texto)]

    return resultado


def contexto(filtros, todos, mostrados):
    """Lo que las plantillas necesitan para pintar la barra de filtros."""
    return {
        "filtros": filtros,
        "hay_filtros": any(filtros.values()),
        "total": len(todos),
        "mostrados": len(mostrados),
    }


def por_codigo(catalogo):
    """Indexa un catálogo por su código, para resolver nombres sin repetir bucles."""
    return {c.get("codigo"): c for c in catalogo}
