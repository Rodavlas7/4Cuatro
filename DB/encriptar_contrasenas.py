#!/usr/bin/env python
"""Encripta las contraseñas de la tabla `usuario` que estén en texto plano.

Para qué sirve
--------------
En `DB/datos.sql` las contraseñas se guardan legibles, para poder leerlas y
cambiarlas sin pelearse con un hash. Pero así NO se puede entrar al sistema:
`LoginAPIView` compara con `check_password`, que espera un hash de Django.

Este script cierra ese hueco. Se corre DESPUÉS de cargar datos.sql:

    mysql -u root cuatro < DB/datos.sql
    python DB/encriptar_contrasenas.py

Es idempotente: lo que ya está hasheado lo deja en paz, así que puedes correrlo
las veces que quieras sin arruinar nada. Eso también significa que si le agregas
un usuario nuevo a mano con su contraseña legible, basta volver a correrlo.

Cómo distingue un hash de un texto plano
----------------------------------------
No se adivina por la forma del texto: se le pregunta a Django con
`identify_hasher()`, que es quien sabe qué formatos entiende
(`algoritmo$iteraciones$salt$hash`). Si no lo reconoce, es texto plano.

Uso
---
    python DB/encriptar_contrasenas.py              # encripta
    python DB/encriptar_contrasenas.py --dry-run    # solo dice qué haría
    python DB/encriptar_contrasenas.py --verificar  # comprueba que ya esté todo
"""

import argparse
import os
import sys
from pathlib import Path

# El script vive en DB/, así que Servicios/ es la carpeta hermana. Se toma de ahí
# la configuración para no repetir los datos de conexión a la base.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'Servicios'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Servicios.settings')

import django

django.setup()

from django.contrib.auth.hashers import identify_hasher, make_password
from usuarios.models import Usuario


def esta_hasheada(valor):
    """True si el valor ya es un hash que Django reconoce."""
    if not valor:
        return False

    try:
        identify_hasher(valor)
    except ValueError:
        # Django no reconoce el formato: es texto plano.
        return False

    return True


def encriptar(dry_run=False):
    """Recorre los usuarios y hashea los que estén en texto plano."""
    usuarios = Usuario.objects.all().order_by('numero')

    if not usuarios:
        print('No hay usuarios en la tabla. ¿Ya corriste datos.sql?')
        return 1

    cambiados = 0
    ya_estaban = 0

    for u in usuarios:

        if esta_hasheada(u.contrasena):
            print(f'  ya hasheada   {u.usuario}')
            ya_estaban += 1
            continue

        if dry_run:
            print(f'  SE HASHEARÍA  {u.usuario}')
            cambiados += 1
            continue

        u.contrasena = make_password(u.contrasena)

        # update() y no save(): el modelo es managed=False sobre una tabla que ya
        # existe, y así se toca únicamente esta columna.
        Usuario.objects.filter(pk=u.pk).update(contrasena=u.contrasena)

        print(f'  hasheada      {u.usuario}')
        cambiados += 1

    print()
    if dry_run:
        print(f'Simulación: {cambiados} por hashear, {ya_estaban} ya estaban.')
    else:
        print(f'Listo: {cambiados} hasheadas, {ya_estaban} ya estaban.')

    return 0


def verificar():
    """Confirma que ninguna contraseña quedó en texto plano."""
    pendientes = [u.usuario for u in Usuario.objects.all().order_by('numero')
                  if not esta_hasheada(u.contrasena)]

    total = Usuario.objects.count()

    if pendientes:
        print(f'{len(pendientes)} de {total} siguen en texto plano:')
        for usuario in pendientes:
            print(f'  {usuario}')
        print()
        print('Corre el script sin --verificar para arreglarlo.')
        return 1

    print(f'Las {total} contraseñas están hasheadas.')
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Encripta las contraseñas en texto plano de la tabla usuario.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dice qué haría, sin tocar la base.',
    )
    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Sólo comprueba que ya no quede nada en texto plano.',
    )
    args = parser.parse_args()

    if args.verificar:
        return verificar()

    return encriptar(dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
