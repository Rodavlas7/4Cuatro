# TraceX

Sistema de **trazabilidad de producción de laptops**. Sigue una laptop desde que
se abre la orden de producción hasta que sale embalada, y guarda quién la armó,
con qué componentes, en qué línea, quién la inspeccionó y por qué se rechazó si
se rechazó.

La pregunta que contesta es: *"la laptop con número de serie X salió mala, ¿qué
le pusieron, quién y cuándo?"*.

## Las tres piezas

```
   ┌──────────────┐   HTTP + token   ┌──────────────┐   mysqlclient  ┌───────────┐
   │   Client     │ ───────────────► │  Servicios   │ ─────────────► │   MySQL   │
   │  (pantallas) │ ◄─────────────── │    (API)     │ ◄───────────── │  `cuatro` │
   └──────────────┘      JSON        └──────────────┘                └───────────┘
        :8001                             :8000                    triggers, vistas,
                                                                   procedimientos
```

| Carpeta      | Qué es | Puerto |
|---|---|---|
| `DB/`        | La base: tablas, catálogos, triggers, vistas y procedimientos, en `.sql` | — |
| `Servicios/` | La API REST (Django + DRF). Nadie más habla con la base | 8000 |
| `Client/`    | Las pantallas (Django). No toca la base, todo lo pide a la API por HTTP | 8001 |

**El cliente no tiene base de datos.** Cada pantalla arma una petición HTTP a la
API y pinta el JSON que le regresa. Por eso el cliente puede estar arriba con la
API apagada: las pantallas salen vacías con un mensaje, no truenan.

## Cómo funciona la planta

La producción va por **líneas** encadenadas: cada línea sabe cuál es su
`siguiente`, y la laptop va avanzando de una a otra. En cada línea se registra un
**ensamblaje** (qué componentes se montaron) y calidad decide si pasa.

```
  Orden de producción (folio)
        │
        ├── se registran las laptops del lote
        │
        ▼
   Línea A ──► Línea B ──► Línea C ──► ...      cada una: registro de ensamblaje
        │                                       + componentes montados
        ▼
   Inspección de calidad ──┬──► APROBADA  ──► Embalaje ──► número de serie final
                           └──► RECHAZADA ──► se anota QUÉ componente falló
                                              (tabla `detalle_inspeccion`)
```

Estados por los que pasa una laptop: `Registrada` → `En Ensamblaje` → `Aprobada`
o `Rechazada` → `Embalada`.

Los módulos del sistema son: **producción** (órdenes, laptops, ensamblaje,
paros), **materiales** (componentes, lotes, órdenes de material, compatibilidad
modelo-componente), **calidad** (inspecciones y piezas reprobadas), **embalaje**,
**planta** (líneas y estaciones), **personal** (empleados y usuarios) y
**trazabilidad** (expediente por laptop o por orden, con exportación a PDF y
Excel).

## Roles y paneles

El cliente está partido en **tres paneles, uno por rol**, para que tres personas
del equipo puedan trabajar en paralelo sin pisarse:

| Rol | Código | Panel | Qué ve |
|---|---|---|---|
| Administrador | `ADMIN` | `/panel/admin/` | Todo: planta, personal, materiales, producción, calidad, trazabilidad |
| Supervisor | `SUPER` | `/panel/supervisor/` | Producción, materiales y calidad de la(s) línea(s) que supervisa |
| Operador de calidad | `OPCALI` | `/panel/calidad/` | Flujo guiado laptop → ensamblaje → inspección, en su línea |

El login manda a cada quien a su panel solo. Un supervisor puede tener varias
líneas asignadas y elige desde el menú con cuál está trabajando.

El detalle de quién toca qué archivo está en [Client/README.md](Client/README.md).

## Levantarlo

### Lo que necesitas

- Python 3 y MySQL 8 corriendo en `localhost:3306`
- El cliente `mysql` de línea de comandos (`cargar.py` lo usa para los
  `DELIMITER` de triggers y procedimientos, que un cursor de Python no entiende)

### 1. Entorno

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

### 2. Base de datos

Un solo comando deja la base `cuatro` completa y lista para entrar:

```bash
./venv/bin/python DB/cargar.py
```

Carga en orden: `estructura.sql` → `datos.sql` → `triggers.sql` →
`datos_pruebas.sql` → `datos_pruebas2.sql` → `vistas.sql` → `procedimientos.sql`
→ `encriptar_contrasenas.py`.

**Ojo: borra todo.** `estructura.sql` hace `DROP DATABASE`. Si algo se rompe a
media sesión, esto mismo la deja como nueva.

```bash
./venv/bin/python DB/cargar.py --si            # sin preguntar
```

```bash
./venv/bin/python DB/cargar.py --sin-pruebas   # se salta datos_pruebas2.sql
```

Los datos de prueba entran **después** de los triggers a propósito: así los datos
de ejemplo pasan por las mismas reglas que va a haber en producción. Si un
`INSERT` choca con un trigger, el dato de ejemplo estaba mal, no el trigger.

El último paso tampoco es opcional: `datos.sql` deja las contraseñas en texto
plano y el login compara contra un hash. Sin `encriptar_contrasenas.py` nadie
entra.

### 3. Los dos servidores

Cada uno en su terminal:

```bash
cd Servicios && ../venv/bin/python manage.py runserver 127.0.0.1:8000
```

```bash
cd Client && ../venv/bin/python manage.py runserver 127.0.0.1:8001
```

Y entras a **http://127.0.0.1:8001/**.

### 4. Usuarios

Hay uno por cada administrador, supervisor y operador de calidad de los datos de
prueba. Para empezar:

| Usuario | Contraseña | Cae en |
|---|---|---|
| `0001AMM` | `12345` | `/panel/admin/` |
| `0003CMM` | `CMM2026` | `/panel/supervisor/` |
| `0002LTV` | `LTV2026` | `/panel/calidad/` |

La lista completa está en [Client/README.md](Client/README.md#usuarios) y en la
sección 17 de `DB/datos.sql`. Son credenciales de desarrollo, viven en el repo y
por lo tanto son públicas: no las lleves a un ambiente real.

## La lógica de negocio vive en la base

Esto es **decisión de diseño, no deuda técnica**. 
La base tiene **31 tablas, 11 triggers, 21 vistas y 5 procedimientos**, y ahí es donde
están las reglas.

| En la base | Para qué |
|---|---|
| **Triggers** (`DB/triggers.sql`) | Reglas que no se pueden saltar: generar el número de serie final, sincronizar la cantidad producida de la orden, bloquear componentes de una laptop terminada, impedir ensamblar en una línea que no es de ensamblaje |
| **Vistas** (`DB/vistas.sql`) | Los `JOIN` de consulta ya resueltos: `vista_laptops`, `vista_ordenes_produccion`, las `vista_dash_*` de los dashboards y las `vista_traza_*` de trazabilidad |
| **Procedimientos** (`DB/procedimientos.sql`) | Operaciones que se resuelven enteras de un golpe: cancelar una orden, iniciar el ensamblaje de una orden, recibir una orden de material, liberar los componentes de una laptop |

Consecuencias prácticas:

- Los modelos de Django son **`managed = False`**. La estructura la manda el
  `.sql`, no las migraciones. Si cambia una tabla, se cambia en `DB/` y de ahí se
  refleja en el modelo — nunca al revés.
- Los procedimientos se llaman a mano con `api/procedimientos.py`, no por el ORM.
- Cuando un trigger rechaza algo, manda un `SIGNAL` con el motivo redactado en
  español. `api/errores.py` lo traduce a un 400 con `{"mensaje": "..."}`, que es
  justo lo que el cliente sabe pintar. Por eso los errores de negocio se leen
  bien en pantalla en lugar de salir como un 500.

Hay un mapa visual de la estructura en `DB/estructura.html` (ábrelo en el
navegador).

## Cómo se autentica

1. El cliente hace `POST /api/usuarios/login/` y recibe un **token** (dura 10
   horas, tabla `sesion`).
2. El token se guarda en la sesión del cliente **y** en una cookie de host
   (`token_4cuatro`). Las cookies no distinguen puerto, así que con iniciar
   sesión en `:8001` también puedes navegar la API en `:8000` desde el navegador
   sin loguearte otra vez.
3. Cada petición del cliente manda `Authorization: Bearer <token>`.
4. La API valida el token y, además, que el **rol** tenga permiso sobre el módulo
   de esa vista (`Servicios/usuarios/permissions.py`, `PERMISOS_ROL`).

El candado real es el de la API. El middleware del cliente
(`Client/core/middleware.py`) bloquea por prefijo de URL para que nadie navegue a
pantallas que no le tocan y para que el error salga bonito, pero no es la
seguridad de verdad.

**Dato importante para el cliente:** cuando el token vence, la API responde
`{"detail": "La sesión ha expirado"}`, **no** una lista vacía. Por eso las vistas
del cliente nunca hacen `requests.get(...).json()` a pelo: usan los helpers de
`Client/core/api.py` (`lista()`, `objeto()`, `fallo()`), que revisan el status
**y** el tipo. Está explicado con detalle en
[Client/README.md](Client/README.md#cómo-leer-respuestas-de-la-api).

## Estructura del repo

```
4Cuatro/
├── DB/                     La base de datos, en .sql
│   ├── estructura.sql          31 tablas
│   ├── datos.sql               catálogos y usuarios
│   ├── datos_pruebas2.sql      datos transaccionales de ejemplo
│   ├── triggers.sql            11 triggers
│   ├── vistas.sql              21 vistas
│   ├── procedimientos.sql      5 procedimientos
│   ├── cargar.py               carga todo en orden
│   ├── encriptar_contrasenas.py    hashea las contraseñas (idempotente)
│   └── estructura.html         mapa visual de la base
│
├── Servicios/              La API (:8000) — nadie más toca la base
│   ├── api/                    modelos, serializers y helpers compartidos
│   ├── usuarios/               login, tokens, permisos por rol, empleados
│   ├── lineas/                 líneas y estaciones
│   ├── produccion/             órdenes, laptops, ensamblaje, paros
│   ├── componentes/            componentes, lotes, órdenes de material
│   ├── calidad/                inspecciones
│   ├── embalaje/               registros de embalaje
│   └── dashboard/              resúmenes y trazabilidad
│
├── Client/                 Las pantallas (:8001) — habla con la API por HTTP
│   ├── core/                   COMPARTIDO: roles, middleware, api.py, filtros
│   ├── home/                   login, logout y el repartidor por rol
│   ├── panel_admin/            \
│   ├── panel_supervisor/        > un panel por rol, cada uno con su namespace
│   ├── panel_calidad/          /
│   ├── produccion/ lineas/ usuarios/ componentes/ calidad/ embalaje/
│   │                           pantallas del admin (ya estaban cuando el
│   │                           cliente era uno solo, se quedaron ahí)
│   ├── trazabilidad/           expedientes y reportes (PDF y Excel)
│   ├── templates/  static/
│   └── README.md               ← guía de trabajo del equipo, léela
│
├── compartir.sh            abre un túnel público hacia el Client
└── requirements.txt
```

## Compartir el proyecto con el equipo

`compartir.sh` levanta un túnel de Cloudflare hacia el cliente para que los
compañeros entren desde sus casas sin instalar nada:

```bash
./compartir.sh
```

No levanta el servidor, solo hace de proxy: el `runserver` del cliente tiene que
estar ya arriba en el 8001. Ctrl+C cierra el túnel y con él el acceso de fuera.
Puedes seguir editando código mientras están dentro.

## Convenciones que importan

- **Fechas y horas para el usuario van en `DD-MM-AAAA HH:MM:SS`**, con los
  filtros de `Client/core/templatetags/formato.py`. No uses el filtro `date` de
  Django: las fechas llegan como **cadena** dentro del JSON, y `date` con una
  cadena devuelve `""` — o sea, borra la fecha de la pantalla sin avisar.
- **Los `<input type="date">` se quedan en ISO** (`AAAA-MM-DD`). Con otro formato
  el navegador muestra el campo vacío.
- **Cada panel del cliente tiene su namespace**: `{% url 'panel_supervisor:laptops-lista' %}`,
  no `{% url 'laptops-lista' %}`.
- Los archivos de `Client/core/` y `templates/base/` los leen los tres paneles:
  avisa antes de cambiarlos.

## Qué falta

- **Falta aplicar el formato de fecha fuera de producción.** Los filtros ya
  existen y producción ya los usa; el resto de las pantallas siguen pintando ISO.
- **La configuración está escrita en `settings.py`**, incluidos `SECRET_KEY`,
  `DEBUG = True` y la contraseña de MySQL. Hay archivos `.env` con la plantilla
  de lo que debería salir de ahí (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DB_*`…),
  pero **ningún `settings.py` los lee todavía**: editarlos no cambia nada. Si
  alguna vez esto se sirve fuera de la red local, ese es el primer pendiente.
- **Casi no hay pruebas automatizadas.** La única suite es
  `Client/usuarios/tests.py`; los demás `tests.py` están vacíos.
