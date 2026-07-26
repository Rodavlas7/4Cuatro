"""
Crea (o actualiza) un usuario propio para probar la API.

Uso, desde la carpeta Servicios/ con el venv activo:
    python crear_usuario.py
Te pedirá la contraseña de forma segura (no se ve al escribir ni queda en el
historial) y la guarda hasheada, igual que el registro oficial.

Puedes editar los datos de abajo antes de correrlo.
"""
import os
import django
import getpass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Servicios.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from usuarios.models import Empleado, Usuario, Rol, Turno

# ----------------- EDITA ESTO -----------------
USUARIO  = "jperez1"   # con esto inicias sesión
NOMBRE   = "Carlos"   # nombre de pila del empleado
APELLIDO = "Garcia"     # primer apellido
ROL      = "ADMIN"      # ADMIN / SUPER / OPCALI pueden iniciar sesión
TURNO    = "MAT"        # MAT / VES
# ----------------------------------------------

pw = getpass.getpass(f"Contraseña para '{USUARIO}': ")
if not pw:
    raise SystemExit("Contraseña vacía; cancelado.")

existente = Usuario.objects.filter(usuario=USUARIO).first()

if existente:
    existente.contrasena = make_password(pw)
    existente.estado = True
    existente.save()
    print(f"Usuario '{USUARIO}' ya existía -> contraseña actualizada y activado.")
else:
    rol = Rol.objects.get(codigo=ROL)
    turno = Turno.objects.get(codigo=TURNO)
    empleado = Empleado.objects.create(
        nombrepila=NOMBRE,
        primerapell=APELLIDO,
        rol=rol,
        turno=turno,
        activo=True,
    )
    Usuario.objects.create(
        usuario=USUARIO,
        contrasena=make_password(pw),
        estado=True,
        empleado=empleado,
    )
    print(f"Usuario '{USUARIO}' creado con empleado #{empleado.numero} (rol {ROL}).")

print("Listo. Ahora haz login en POST /api/usuarios/login/ para obtener tu token.")
