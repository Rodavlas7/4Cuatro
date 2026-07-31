

from datetime import date, datetime, time

from django import template

register = template.Library()

FORMATO_FECHA = '%d-%m-%Y'
FORMATO_HORA = '%H:%M:%S'

# Formas en las que puede llegar una fecha desde la API.
PATRONES_FECHA = ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y')

# Idem para la hora. DRF manda HH:MM:SS, pero un <input type="time"> manda HH:MM
# y los microsegundos aparecen cuando el valor viene de un DateTimeField.
PATRONES_HORA = ('%H:%M:%S.%f', '%H:%M:%S', '%H:%M')


def _a_fecha(valor):
    """Convierte a date lo que se pueda; None si no se puede."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    # Un datetime completo ("2026-07-21T08:00:00") trae la fecha por delante.
    texto = texto.replace('T', ' ').split(' ')[0]

    for patron in PATRONES_FECHA:
        try:
            return datetime.strptime(texto, patron).date()
        except ValueError:
            continue
    return None


def _a_hora(valor):
    """Convierte a time lo que se pueda; None si no se puede."""
    if isinstance(valor, datetime):
        return valor.time()
    if isinstance(valor, time):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    # Si viene un datetime completo, la hora va después del separador.
    if 'T' in texto or ' ' in texto:
        texto = texto.replace('T', ' ').split(' ')[-1]

    for patron in PATRONES_HORA:
        try:
            return datetime.strptime(texto, patron).time()
        except ValueError:
            continue
    return None


@register.filter
def fecha(valor):
    """Fecha en DD-MM-AAAA.

    >>> fecha('2026-07-21')
    '21-07-2026'
    """
    if valor in (None, ''):
        return ''
    convertida = _a_fecha(valor)
    return convertida.strftime(FORMATO_FECHA) if convertida else str(valor)


@register.filter
def hora(valor):
    """Hora en HH:MM:SS. Completa los segundos si vienen recortados.

    >>> hora('08:00')
    '08:00:00'
    """
    if valor in (None, ''):
        return ''
    convertida = _a_hora(valor)
    return convertida.strftime(FORMATO_HORA) if convertida else str(valor)


@register.filter
def fecha_hora(valor, hora_valor=None):
    """Fecha y hora juntas en DD-MM-AAAA HH:MM:SS.

    Se usa con la hora como argumento, porque la API las manda en dos campos:

        {{ r.fecha_inicio|fecha_hora:r.hora_inicio }}

    Si sólo hay fecha, devuelve la fecha sola en vez de inventar 00:00:00: no es
    lo mismo "no se registró la hora" que "pasó a medianoche".

    >>> fecha_hora('2026-07-21', '08:00:00')
    '21-07-2026 08:00:00'
    """
    if valor in (None, '') and hora_valor in (None, ''):
        return ''

    partes = [p for p in (fecha(valor), hora(hora_valor)) if p]
    return ' '.join(partes)
