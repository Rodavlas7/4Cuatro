#!/usr/bin/env python
"""Carga la base de TraceX completa, en el orden correcto.

Uso, desde la raíz del proyecto:

    python DB/cargar.py                 # pregunta antes de borrar
    python DB/cargar.py --si            # sin preguntar (para scripts)
    python DB/cargar.py --sin-pruebas   # sin los datos de prueba

OJO: BORRA TODO. `estructura.sql` hace DROP de las tablas y `datos.sql` las
trunca, así que lo que tengas capturado a mano se pierde.

El orden
--------
    1. estructura.sql      tablas
    2. datos.sql           catálogos y usuarios (empieza truncando)
    3. triggers.sql        reglas de negocio
    4. datos_pruebas.sql   datos transaccionales de ejemplo
    5. vistas.sql          vistas de consulta
    6. procedimientos.sql  operaciones en lote
    7. encriptar_contrasenas.py

Los datos de prueba entran DESPUÉS de los triggers a propósito: así los datos de
ejemplo pasan por las mismas reglas que va a haber en producción. Si un INSERT
de `datos_pruebas.sql` choca con un trigger, es que ese dato de ejemplo no era
válido y hay que arreglarlo, no saltarse el trigger.

El último paso no es opcional: `datos.sql` deja las contraseñas en texto plano y
`LoginAPIView` compara contra un hash. Sin ese paso nadie puede entrar.

Por qué llama al cliente `mysql` y no usa el cursor de Django
-------------------------------------------------------------
`triggers.sql` y `procedimientos.sql` usan `DELIMITER`, que NO es SQL: es una
instrucción del cliente de línea de comandos. Un cursor de Python la rechaza con
un error de sintaxis. Por eso cada archivo se manda al binario `mysql`, que sí
la entiende.

Sobre la base de destino
------------------------
No se puede elegir. Los siete .sql traen `USE cuatro;` escrito adentro, así que
se cargan en `cuatro` pase lo que pase: darle otra base al cliente `mysql` no
cambia nada, la instrucción de adentro manda. Por eso el script compara esa base
con la de `Servicios/settings.py` y se detiene si no coinciden, en lugar de
dejarte cargar en un lugar creyendo que cargaste en otro.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# El script vive en DB/, así que Servicios/ es la carpeta hermana. De ahí se
# toma la configuración para no repetir los datos de conexión.
RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / 'DB'

sys.path.insert(0, str(RAIZ / 'Servicios'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Servicios.settings')

import django

django.setup()

from django.conf import settings


# Los .sql en el orden en que se cargan. El último paso, el de las contraseñas,
# va aparte porque es un script de Python, no SQL.
ARCHIVOS = [
    ('estructura.sql', 'Tablas'),
    ('datos.sql', 'Catálogos y usuarios'),
    ('triggers.sql', 'Triggers'),
    ('datos_pruebas.sql', 'Datos de prueba'),
    ('vistas.sql', 'Vistas'),
    ('procedimientos.sql', 'Procedimientos'),
]

# Nombre del archivo de datos de prueba, para poder saltárselo con --sin-pruebas.
PRUEBAS = 'datos_pruebas.sql'

# Para leer el `USE <base>;` que traen los .sql adentro.
USE = re.compile(r'^\s*USE\s+`?(\w+)`?\s*;', re.IGNORECASE | re.MULTILINE)


def base_del_archivo(archivo):
    """La base que el .sql escribe con USE, o None si no trae ninguna."""
    contenido = (DB / archivo).read_text(encoding='utf-8', errors='replace')
    encontrado = USE.search(contenido)
    return encontrado.group(1) if encontrado else None


def revisar_destino(cfg):
    """Comprueba que los .sql carguen donde la API espera encontrar los datos.

    Devuelve el nombre de la base de los archivos, o None si hay conflicto."""
    faltantes = []
    bases = set()

    for archivo, _ in ARCHIVOS:
        ruta = DB / archivo

        if not ruta.exists():
            faltantes.append(archivo)
            continue

        base = base_del_archivo(archivo)
        if base:
            bases.add(base)

    if faltantes:
        print("  Faltan archivos en DB/: " + ', '.join(faltantes))
        return None

    if len(bases) > 1:
        print(f"  Los .sql no apuntan todos a la misma base: {', '.join(sorted(bases))}.")
        print("  Revisa el USE de cada uno antes de cargar.")
        return None

    if not bases:
        print("  Ningún .sql trae USE, así que no se sabe dónde cargarían.")
        return None

    base = bases.pop()

    if base != cfg['NAME']:
        print(f"  Los .sql cargan en '{base}', pero la API lee de '{cfg['NAME']}'")
        print(f"  (DATABASES['default']['NAME'] en Servicios/settings.py).")
        print(f"\n  Cargar así dejaría '{base}' llena y '{cfg['NAME']}' como estaba.")
        print("  Empata los dos nombres antes de seguir.")
        return None

    return base


def argumentos_de_mysql(cfg, base):
    """Los argumentos de conexión para el cliente `mysql`.

    La contraseña se pasa con `-p<clave>` pegado, sin espacio, que es como la
    espera el cliente. Si viene vacía no se manda el flag: mandar `-p` solo hace
    que el cliente la pida por teclado y el script se quedaría colgado."""
    args = ['-h', cfg['HOST'] or 'localhost',
            '-P', str(cfg['PORT'] or 3306),
            '-u', cfg['USER']]

    if cfg.get('PASSWORD'):
        args.append(f"-p{cfg['PASSWORD']}")

    return args + [base]


def correr_sql(archivo, cfg, base):
    """Manda un .sql al cliente `mysql`. Devuelve True si salió bien."""
    with open(DB / archivo, 'rb') as sql:
        resultado = subprocess.run(
            ['mysql'] + argumentos_de_mysql(cfg, base),
            stdin=sql,
            capture_output=True,
            text=True,
        )

    if resultado.returncode != 0:
        # El cliente escribe el error en stderr con el número de línea del .sql,
        # que es justo lo que se necesita para ir a arreglarlo.
        print(f"     {resultado.stderr.strip()}")
        return False

    return True


def correr_encriptar():
    """Hashea las contraseñas que datos.sql dejó en texto plano."""
    resultado = subprocess.run(
        [sys.executable, str(DB / 'encriptar_contrasenas.py')],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        print(f"     {(resultado.stderr or resultado.stdout).strip()}")
        return False

    # Del resumen sólo interesa la última línea ("Listo: N hasheadas..."); el
    # detalle usuario por usuario no aporta nada aquí.
    lineas = [l for l in resultado.stdout.strip().split('\n') if l.strip()]
    if lineas:
        print(f"     {lineas[-1].strip()}")

    return True


def confirmar(base):
    """Pide confirmación antes de borrar. Se escribe el nombre a mano, no un
    simple s/n: borrar la base por una tecla de más sería muy fácil."""
    print(f"\n  Se va a BORRAR y recargar por completo la base '{base}'.")
    print("  Todo lo que esté capturado ahí se pierde.\n")

    return input("  Escribe el nombre de la base para confirmar: ").strip() == base


def main():
    parser = argparse.ArgumentParser(
        description='Carga la base de TraceX completa. BORRA lo que haya.')
    parser.add_argument('--si', action='store_true',
                        help='no preguntar, cargar directo')
    parser.add_argument('--sin-pruebas', action='store_true',
                        help='omitir datos_pruebas.sql')
    opciones = parser.parse_args()

    cfg = settings.DATABASES['default']

    base = revisar_destino(cfg)
    if base is None:
        return 1

    if not opciones.si and not confirmar(base):
        print("\n  Cancelado: no se tocó nada.")
        return 1

    archivos = [(a, q) for a, q in ARCHIVOS
                if not (opciones.sin_pruebas and a == PRUEBAS)]

    print(f"\n  Cargando '{base}' en {cfg['HOST'] or 'localhost'}:{cfg['PORT'] or 3306}\n")

    for paso, (archivo, que) in enumerate(archivos, start=1):
        print(f"  {paso}. {archivo:<20} {que}")

        if not correr_sql(archivo, cfg, base):
            print(f"\n  Se detuvo en {archivo}. La base quedó a medias.")
            return 1

    # Este paso no se salta nunca: sin él las contraseñas quedan en texto plano
    # y el login rechaza a todo el mundo.
    print(f"  {len(archivos) + 1}. contraseñas          Hasheando")

    if not correr_encriptar():
        print("\n  Las tablas quedaron cargadas, pero las contraseñas siguen en")
        print("  texto plano: nadie va a poder entrar hasta que corras")
        print("\n      python DB/encriptar_contrasenas.py")
        return 1

    print("\n  Listo.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
