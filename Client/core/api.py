"""Acceso a la API (Servicios). Lo comparten los tres paneles.

Antes cada app repetía la URL de la API y el armado del header. Aquí queda en un
solo lugar para que cambiar de host o de puerto sea un renglón.

ES COMPARTIDO: si tocas este archivo afectas a los tres paneles.
"""

import requests

# URL base de la API. Todo lo demás se cuelga de aquí.
API = 'http://127.0.0.1:8000/api'


def headers_token(token):
    """Header de autorización a partir de un token suelto.

    Es la versión para código que recibe el token como argumento (los catálogos
    de los formularios, por ejemplo) y no tiene el request a la mano."""
    return {'Authorization': f'Bearer {token}'}


def headers(request):
    """Header de autorización con el token que quedó en la sesión."""
    return headers_token(request.session.get('token'))


def url(ruta):
    """Arma una URL de la API a partir de una ruta relativa.

    >>> url('produccion/laptops/')
    'http://127.0.0.1:8000/api/produccion/laptops/'
    """
    return f"{API}/{ruta.lstrip('/')}"


# ==================================================
# P E D I R   A   L A   A P I
# ==================================================
#
# OJO con una trampa de requests: un Response es FALSY cuando el status no es
# 2xx, porque Response.__bool__ devuelve self.ok. Entonces esto está mal:
#
#     if respuesta:            # ¡un 403 entra por el else!
#     if not respuesta:        # ¡confunde "403" con "la API no contestó"!
#
# Aquí siempre se compara con `is None`, que es lo único que distingue "no hubo
# respuesta" de "hubo respuesta y fue un error". Si escribes código nuevo que
# reciba estas respuestas, hazlo igual.


def get(url_completa, headers=None, params=None, timeout=10):
    """GET a la API que nunca lanza excepción.

    Si la API no contesta (apagada, timeout, DNS) devuelve None en lugar de dejar
    subir la excepción de requests y tumbar la pantalla con un 500. Los helpers
    de abajo tratan None como "no hay datos"."""
    try:
        return requests.get(url_completa, headers=headers, params=params, timeout=timeout)
    except requests.RequestException:
        return None


# ==================================================
# L E E R   R E S P U E S T A S
# ==================================================
#
# Por qué existen estas dos funciones:
#
# Cuando el token no sirve, la API no responde una lista vacía: responde un
# objeto de error, {"detail": "La sesión ha expirado"}. Si eso se le pasa tal
# cual a la plantilla, el {% for %} itera las CLAVES del diccionario, o sea la
# cadena "detail". Y como "detail".codigo no existe, Django lo resuelve a cadena
# vacía y un {% url 'linea-detalle' '' %} truena con NoReverseMatch: error 500 en
# una pantalla que sólo debía verse vacía.
#
# Por eso no basta con revisar el status: también hay que revisar que el JSON sea
# del tipo que la plantilla espera.


def lista(respuesta):
    """El JSON de la respuesta si de verdad es una lista; si no, [].

    Úsala para todo endpoint que devuelve un conjunto de registros. Con [] las
    plantillas caen en su {% empty %} en lugar de tronar."""
    if respuesta is None or respuesta.status_code != 200:
        return []

    try:
        datos = respuesta.json()
    except ValueError:
        # La API contestó algo que no es JSON (una página de error de Django,
        # por ejemplo).
        return []

    return datos if isinstance(datos, list) else []


def objeto(respuesta):
    """El JSON de la respuesta si de verdad es un diccionario; si no, {}.

    Úsala para los endpoints de detalle, que devuelven un solo registro."""
    if respuesta is None or respuesta.status_code != 200:
        return {}

    try:
        datos = respuesta.json()
    except ValueError:
        return {}

    return datos if isinstance(datos, dict) else {}


def fallo(respuesta):
    """True si la respuesta no sirve. Para decidir si avisarle al usuario.

    Un timeout o una conexión rechazada llegan aquí como None, porque quien
    llamó atrapó la excepción de requests."""
    return respuesta is None or respuesta.status_code != 200


def mensaje_error(respuesta):
    """Texto que explica por qué falló la respuesta, para mostrarlo al usuario."""
    if respuesta is None:
        return 'No se pudo comunicar con la API.'

    try:
        datos = respuesta.json()
    except ValueError:
        return f'La API respondió {respuesta.status_code}.'

    if isinstance(datos, dict):
        # DRF usa "detail"; esta API usa "mensaje" en sus vistas propias.
        for campo in ('mensaje', 'detail'):
            if campo in datos:
                return str(datos[campo])

        return ' | '.join(f'{c}: {v}' for c, v in datos.items())

    return f'La API respondió {respuesta.status_code}.'
