# Client — TraceX

El cliente está partido en **tres paneles**, uno por rol. La idea es que tres
personas puedan trabajar al mismo tiempo sin pisarse: cada panel tiene sus
vistas, sus URLs, sus plantillas y su CSS.

```
                        /login/
                           │
                    (según el rol)
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  /panel/admin/     /panel/supervisor/  /panel/calidad/
     ADMIN                SUPER              OPCALI
```

## Quién toca qué

| Panel | Rol | URL | Carpeta de código | Carpeta de plantillas | CSS |
|---|---|---|---|---|---|
| Administrador | `ADMIN` | `/panel/admin/` | `panel_admin/` + apps `produccion/`, `calidad/`, `componentes/`, `lineas/`, `usuarios/` | `templates/panel_admin/` + `templates/{produccion,calidad,componentes,lineas,usuarios}/` | `static/css/panel_admin.css` |
| Supervisor | `SUPER` | `/panel/supervisor/` | `panel_supervisor/` | `templates/panel_supervisor/` | `static/css/panel_supervisor.css` |
| Calidad | `OPCALI` | `/panel/calidad/` | `panel_calidad/` | `templates/panel_calidad/` | `static/css/panel_calidad.css` |

Si sólo trabajas dentro de tu columna, no hay conflictos de merge con nadie.

### Por qué el admin tiene sus pantallas en otro lado

Las pantallas del admin (producción, calidad, materiales, planta, personal) se
quedaron en las apps originales del proyecto, porque son las que ya estaban
construidas cuando el cliente era uno solo. Son del admin y de nadie más: el
middleware no deja entrar a otro rol. Los paneles de supervisor y calidad tienen
su **propia copia** de las pantallas que les tocan, para poder cambiarlas sin
afectar al admin.

## Archivos compartidos — NO los cambies solo

Estos los leen los tres paneles. Cambiarlos afecta a todo el equipo, así que
avisa antes:

| Archivo                                 | Para qué es |
|-----------------------------------------|-----------------------------------------------|
| `core/roles.py`                         | Códigos de rol y a qué panel va cada uno      |
| `core/middleware.py`                    | Quién puede entrar a qué ruta                 |
| `core/guards.py`                        | Decorador y mixin de rol para vistas          |
| `core/api.py`                           | URL base, headers y lectura de respuestas     |
| `core/context_processors.py`            | Datos de sesión que ven todas las plantillas  |
| `home/views.py`                         | Login, logout y el repartidor por rol         |
| `templates/base/base_layout.html`       | Cascarón común: `<head>`, topbar, mensajes    |
| `static/css/panel.css`                  | Estilos comunes de los paneles                |
| `Client/settings.py`, `Client/urls.py`  | Configuración y montaje de los paneles        |

Si necesitas un hueco nuevo en el cascarón, agrega un `{% block %}` en
`base_layout.html` en lugar de escribir contenido dentro. Así el cambio no le
mueve nada a los demás.

## Cómo agregar una pantalla a tu panel

Ejemplo con el panel de supervisor:

1. **Vista** en `panel_supervisor/views_<modulo>.py`:

   ```python
   from core.guards import requiere_rol
   from core.roles import ROL_SUPERVISOR

   @requiere_rol(ROL_SUPERVISOR)
   def miPantallaView(request):
       return render(request, 'panel_supervisor/<modulo>/mi_pantalla.html', contexto)
   ```

2. **URL** en `panel_supervisor/urls.py`:

   ```python
   path('<modulo>/mi-pantalla/', views_<modulo>.miPantallaView, name='mi-pantalla'),
   ```

3. **Plantilla** en `templates/panel_supervisor/<modulo>/mi_pantalla.html`:

   ```django
   {% extends 'panel_supervisor/base.html' %}

   {% block titulo_pagina %}Mi Pantalla{% endblock %}
   {% block topbar_titulo %}Mi Pantalla{% endblock %}

   {% block content %}
       ...
   {% endblock %}
   ```

4. **Enlace** en `templates/panel_supervisor/_sidebar.html`.

### Los `{% url %}` van con namespace

Cada panel tiene su `app_name`, así que dentro de tus plantillas y vistas los
nombres van con prefijo:

```django
{% url 'panel_supervisor:laptops-lista' %}    ✅
{% url 'laptops-lista' %}                     ❌ (ése es del panel admin)
```

```python
redirect('panel_supervisor:laptops-lista')    # ✅
redirect('login')                             # ✅ login vive en home, sin namespace
```

Gracias al namespace los tres paneles pueden usar los mismos nombres de pantalla
sin estorbarse.

### Cuidado con las rutas escritas a mano en JS

Algunas plantillas arman la URL de un formulario en JavaScript:

```javascript
document.getElementById('formEditar').action = "/panel/supervisor/produccion/paros/editar/" + numero + "/";
```

Esas no las revisa Django, así que si mueves una URL, búscalas con
`grep -rn 'action = "/' templates/panel_supervisor/`.

### Comentarios en plantillas

Django sólo acepta `{# ... #}` en **una línea**. Para varias líneas usa
`{% comment %} ... {% endcomment %}`, si no el texto se pinta en la página.

## Cómo leer respuestas de la API

**Nunca hagas `requests.get(...).json()` a pelo.** Usa los helpers de
`core/api.py`:

```python
from core.api import get, lista, objeto, fallo, mensaje_error

# Listas
respuesta = get(f"{API}/lineas/", headers)

if fallo(respuesta):
    messages.error(request, f"No se pudieron cargar las líneas. {mensaje_error(respuesta)}")

context = {"lineas": lista(respuesta)}   # siempre una lista, nunca un dict

# Detalles: si falla, no pintes campos en blanco, regresa a la lista
respuesta = get(f"{API}/lineas/{codigo}/", headers)

if fallo(respuesta):
    messages.error(request, f"No se pudo cargar la línea. {mensaje_error(respuesta)}")
    return redirect('lineas-lista')

context = {"linea": objeto(respuesta)}   # siempre un dict
```

Por qué importa: cuando el token vence, la API **no** responde una lista vacía,
responde `{"detail": "La sesión ha expirado"}`. Si ese diccionario llega a la
plantilla, el `{% for %}` itera sus CLAVES (la cadena `"detail"`), `"detail".codigo`
resuelve a cadena vacía, y un `{% url 'linea-detalle' '' %}` truena con
`NoReverseMatch`: error 500 en una pantalla que sólo debía verse vacía. `lista()`
y `objeto()` revisan el status **y** el tipo, así que eso ya no pasa.

`get()` además nunca lanza excepción: si la API está apagada devuelve `None` y los
helpers lo tratan como "no hay datos".

### La trampa del `if respuesta:`

Un `Response` de requests es **falsy** cuando el status no es 2xx
(`Response.__bool__` devuelve `self.ok`). Entonces:

```python
if respuesta:              # ❌ un 403 se va por el else
if not respuesta:          # ❌ confunde "403" con "la API no contestó"
if respuesta is None:      # ✅
if fallo(respuesta):       # ✅ lo de siempre
```

## Control de acceso

Hay dos candados y los dos importan:

1. **El middleware** (`core/middleware.py`) trabaja por prefijo de URL. Es el
   candado de fondo: cualquier pantalla nueva dentro de `/panel/tu-panel/` nace
   protegida sin que hagas nada.
2. **El guard por vista** (`core/guards.py`) es opcional y explícito. Sirve para
   dejar clara la intención y para el caso raro de una vista que quieras abrir a
   dos roles.

Y aparte, **la API valida por su cuenta**
(`Servicios/usuarios/permissions.py`). Lo de aquí es para que nadie navegue a
pantallas que no le tocan y para que el error salga bonito en lugar de un 403 de
la API a media pantalla. No es la seguridad de verdad.

### Agregar un rol nuevo

1. Dalo de alta en la API (`PERMISOS_ROL` y `roles_permitidos` del login).
2. Agrega su constante y su panel en `core/roles.py`.
3. Agrega su prefijo en `RUTAS_POR_ROL` de `core/middleware.py`.
4. Crea la app `panel_<rol>/` y sus plantillas.

Si un rol existe en la API pero no en `core/roles.py`, el login lo rechaza con
un mensaje claro en lugar de dejarlo entrar a ninguna parte.

## Usuarios

Están al final de `DB/datos.sql`, en la sección `17. USUARIOS`. Hay uno por cada
administrador, operador de calidad y supervisor.

| Usuario | Contraseña | Rol | Cae en | Empleado | Línea |
|---|---|---|---|---|---|
| `0001AMM` | `12345` | `ADMIN` | `/panel/admin/` | 2607029 Araceli Marcos Montes | — |
| `rodavlas` | `172509` | `ADMIN` | `/panel/admin/` | 2607030 Salvador Garcia Bojorquez | — |
| `0002LTV` | `LTV2026` | `OPCALI` | `/panel/calidad/` | 2607004 Lucía Torres Vargas | A |
| `0004RFS` | `RFS2026` | `OPCALI` | `/panel/calidad/` | 2607009 Roberto Flores Silva | B |
| `0006HPM` | `HPM2026` | `OPCALI` | `/panel/calidad/` | 2607014 Héctor Paz Mora | C |
| `0008CSM` | `CSM2026` | `OPCALI` | `/panel/calidad/` | 2607019 Carmen Sosa Molina | D |
| `0010RBC` | `RBC2026` | `OPCALI` | `/panel/calidad/` | 2607024 Ramón Blanco Cruz | E |
| `0003CMM` | `CMM2026` | `SUPER` | `/panel/supervisor/` | 2607005 Chelly Montes Marcos | A |
| `0005PNR` | `PNR2026` | `SUPER` | `/panel/supervisor/` | 2607010 Patricia Navarro Ríos | B |
| `0007DRB` | `DRB2026` | `SUPER` | `/panel/supervisor/` | 2607015 Diana Ríos Blanco | C |
| `0009GPS` | `GPS2026` | `SUPER` | `/panel/supervisor/` | 2607020 Gloria Peña Silva | D |
| `0011JCP` | `JCP2026` | `SUPER` | `/panel/supervisor/` | 2607025 Julia Cabrera Pérez | E |
| `0012AJC` | `AJC2026` | `SUPER` | `/panel/supervisor/` | 2607028 Arturo Jiménez Cruz | F |

- **Usuario** = 4 dígitos de secuencia + iniciales de nombre y apellidos
  (`0001AMM` = Araceli Marcos Montes).
- **Contraseña** de calidad y supervisor = las 3 letras del usuario + `2026`.
- Ninguno da de alta empleados nuevos: se cuelgan de empleados que ya existían
  con ese rol y ya estaban asignados a una línea.

Son credenciales de desarrollo y viven en el repositorio, así que son públicas.
No las lleves a un ambiente real.

### Las contraseñas se cargan en dos pasos

En `datos.sql` las contraseñas están **en texto plano**, para poder leerlas y
cambiarlas sin pelearse con un hash. Así NO se puede entrar: `LoginAPIView`
compara con `check_password`, que espera un hash de Django. Por eso hay un
segundo paso:

```bash
mysql -u root cuatro < DB/datos.sql && python DB/encriptar_contrasenas.py
```

`DB/encriptar_contrasenas.py` recorre la tabla `usuario` y reemplaza cada
contraseña en texto plano por su hash PBKDF2. Es **idempotente**: lo que ya está
hasheado lo deja igual, así que puedes correrlo cuantas veces quieras. Si le
agregas un usuario a mano con su contraseña legible, basta volver a correrlo.

```bash
python DB/encriptar_contrasenas.py --dry-run
```

```bash
python DB/encriptar_contrasenas.py --verificar
```

Para saber si algo es hash o texto plano no adivina por la forma: le pregunta a
Django con `identify_hasher()`.

### Cuidado al recargar datos.sql

`datos.sql` empieza con `TRUNCATE` de 29 tablas, así que **borra todo**: no sólo
los usuarios, también laptops, órdenes, componentes e inspecciones. Si nada más
quieres rehacer los usuarios, saca los `INSERT INTO usuario` de la sección 17 y
corre esos. Y si quieres los datos de prueba de vuelta, después de `datos.sql` va
`datos_pruebas.sql`.

## Correr el proyecto

La API (`Servicios`) va en el puerto 8000 y el cliente en el 8010:

```bash
cd /home/rodavlas/4Cuatro/Servicios && ../venv/bin/python manage.py runserver 127.0.0.1:8000
```

```bash
cd /home/rodavlas/4Cuatro/Client && ../venv/bin/python manage.py runserver 127.0.0.1:8010
```

## Qué falta

- **Calidad y supervisor no pueden REGISTRAR una inspección.** Pueden ver la
  lista, pero el select de inspector del formulario se queda vacío: el endpoint
  `usuarios/empleados-calidad-por-linea/` de la API pide el módulo `empleados`, y
  en `PERMISOS_ROL` (`Servicios/usuarios/permissions.py`) ese módulo sólo lo tiene
  `ADMIN`. Los datos sí existen; es nada más el permiso. Se arregla del lado de la
  API, decidiendo qué es lo correcto:
  - darle a `OPCALI` y `SUPER` acceso al módulo `empleados` (lo más simple, pero
    también les abre el resto de las pantallas de personal), o
  - sacar ese endpoint a un módulo propio y más angosto, tipo
    `consultas_empleados`, y dárselo sólo a quien lo necesita (más cerrado).
- **Embalaje**, **Trazabilidad** y **Reportes** están en los sidebars con
  `href="#"`: todavía no tienen pantalla.
- El panel de calidad sólo tiene inspecciones. El rol `OPCALI` también trae
  permiso de `consultas` en la API, que aquí no está usado.
