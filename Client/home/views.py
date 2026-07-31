from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import render, redirect
import requests

from core.roles import panel_inicio


# Create your views here.

# URL base de la API (Servicios).
API = "http://127.0.0.1:8000/api"

# Cookie de host donde se deja el token para que la API (:8000) también lo vea.
# Las cookies no distinguen puerto, así que con iniciar sesión aquí basta para
# navegar la API sin volver a loguearse. El nombre debe coincidir con
# TOKEN_COOKIE de Servicios/usuarios/authentication.py.
TOKEN_COOKIE = "token_4cuatro"

# El token dura 10 horas (ver LoginAPIView de la API); la cookie vence a la par.
TOKEN_COOKIE_MAX_AGE = 10 * 60 * 60

# Mensajes con los que la API avisa que el token ya no sirve.
#
# Se comparan por texto y no por código HTTP porque la API NUNCA responde 401:
# su TokenAuthentication no implementa authenticate_header(), así que DRF
# degrada el 401 a 403. Y con 403 llega también la falta de permisos de módulo
# ("No cuenta con las credenciales para acceder."), que NO es sesión vencida:
# si nos guiáramos solo por el código, sacaríamos del sistema a un usuario que
# sí está dentro pero no tiene acceso a ese módulo.
MENSAJES_SESION_MUERTA = (
    "la sesión ha expirado",
    "token inválido",
    "formato de token inválido",
    "authentication credentials were not provided",
)


def _token_vigente(token):
    """Le pregunta a la API si el token todavía sirve.

    Se usa un catálogo barato (turnos, 2 renglones). Ese endpoint es AllowAny,
    así que un 200 solo puede significar que la autenticación pasó; cualquier
    fallo de token se cae antes, en TokenAuthentication."""
    if not token:
        return False

    try:
        respuesta = requests.get(
            f"{API}/usuarios/Turno/Listar/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except requests.RequestException:
        # Si la API no contesta no se puede afirmar que el token esté vencido.
        # Sacar a alguien por un tropiezo de red sería peor que dejarlo pasar.
        return True

    if respuesta.status_code == 200:
        return True

    try:
        detalle = str(respuesta.json().get("detail", "")).lower()
    except ValueError:
        detalle = ""

    return not any(m in detalle for m in MENSAJES_SESION_MUERTA)


'''-----------------------------------------------------------------------------
    I N D E X   V I E W
-----------------------------------------------------------------------------'''
def indexView(request):
    """Puerta de entrada del sitio.

    No basta con que haya token en la sesión: puede estar vencido, y entonces el
    dashboard se pinta pero todo lo de adentro falla. Por eso primero se le
    pregunta a la API si sigue sirviendo; si no, se limpia la sesión y se manda
    al login."""

    token = request.session.get('token')

    if not token:
        return redirect('login')

    if not _token_vigente(token):
        # Se limpia aquí para no volver a preguntar en cada entrada y para que
        # la cookie compartida no siga dando acceso a la API por su cuenta.
        request.session.flush()
        respuesta = redirect('login')
        respuesta.delete_cookie(TOKEN_COOKIE)
        messages.info(request, "Tu sesión expiró. Vuelve a iniciar sesión.")
        return respuesta

    return redirect('dashboard')


'''-----------------------------------------------------------------------------
    D A S H B O A R D   V I E W
-----------------------------------------------------------------------------'''
def dashboardView(request):
    """Repartidor: manda a cada rol al dashboard de su panel.

    Ya no pinta nada. El dashboard de verdad vive en panel_admin,
    panel_calidad o panel_supervisor, según el rol. Esta vista se conserva para
    que cualquier enlace viejo a /dashboard/ siga llegando a buen lugar."""

    if 'token' not in request.session:
        return redirect('login')

    destino = panel_inicio(request.session.get('rol'))

    if not destino:
        # Sin rol reconocido no hay panel que mostrar. Puede ser una sesión
        # creada antes de que el cliente se dividiera en paneles.
        request.session.flush()
        respuesta = redirect('login')
        respuesta.delete_cookie(TOKEN_COOKIE)
        messages.info(request, "Vuelve a iniciar sesión.")
        return respuesta

    return redirect(destino)

'''def dashboardView(request):

    if 'token' not in request.session:
        return redirect('login')

    token = request.session.get('token')

    respuesta = requests.get(
        "http://127.0.0.1:8001/api/ordenes/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    datos = respuesta.json()

    return render(
        request,
        'home/dashboard.html',
        {
            "ordenes": datos
        }
    )'''



'''-----------------------------------------------------------------------------
    L O G I N   V I E W (luego dividir en carpetas correspondientes) 
-----------------------------------------------------------------------------'''
def loginView(request):

    if request.method == "POST":

        usuario = request.POST.get('usuario')
        contrasena = request.POST.get('contrasena')


        respuesta = requests.post(
            "http://127.0.0.1:8000/api/usuarios/login/",
            json={
                "usuario": usuario,
                "contrasena": contrasena
            }
        )
        datos = respuesta.json()

        if respuesta.status_code == 200:
            rol = datos.get('rol')
            destino = panel_inicio(rol)

            if not destino:
                # La API ya filtra los roles con acceso, así que llegar aquí
                # significa que allá se dio de alta un rol que en el cliente
                # todavía no tiene panel (ver core/roles.py).
                return render(
                    request,
                    'home/login.html',
                    {
                        'error': "Tu rol no tiene un panel asignado. "
                                 "Contacta al administrador."
                    }
                )

            request.session['token'] = datos.get('token')
            request.session['usuario'] = usuario

            # El rol define a qué panel entra y qué puede ver, así que se guarda
            # en la sesión: es lo que revisan el middleware y los sidebars.
            request.session['rol'] = rol
            request.session['nombre'] = datos.get('nombre')
            request.session['empleado'] = datos.get('empleado')

            # El token va también en la cookie compartida, para no tener que
            # iniciar sesión otra vez al entrar a la API desde el navegador.
            respuesta_http = redirect(destino)
            respuesta_http.set_cookie(
                TOKEN_COOKIE,
                datos.get('token'),
                max_age=TOKEN_COOKIE_MAX_AGE,
                httponly=True,
                samesite='Lax',
            )
            return respuesta_http
        else:
            return render(
                request,
                'home/login.html',
                {
                    'error': datos.get('mensaje')
                }
            )

    return render(request,'home/login.html')


'''-----------------------------------------------------------------------------
    L O G O U T  V I E W (luego dividir en carpetas correspondientes) 
-----------------------------------------------------------------------------'''
def logoutView(request):
    request.session.flush()

    # Borra también la cookie compartida, si no la API te seguiría dando por
    # dentro aunque aquí ya hayas salido.
    respuesta_http = redirect('login')
    respuesta_http.delete_cookie(TOKEN_COOKIE)
    return respuesta_http