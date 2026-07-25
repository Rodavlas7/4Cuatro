from django.shortcuts import render
from django.shortcuts import render, redirect
import requests


# Create your views here.

# Cookie de host donde se deja el token para que la API (:8000) también lo vea.
# Las cookies no distinguen puerto, así que con iniciar sesión aquí basta para
# navegar la API sin volver a loguearse. El nombre debe coincidir con
# TOKEN_COOKIE de Servicios/usuarios/authentication.py.
TOKEN_COOKIE = "token_4cuatro"

# El token dura 10 horas (ver LoginAPIView de la API); la cookie vence a la par.
TOKEN_COOKIE_MAX_AGE = 10 * 60 * 60


'''-----------------------------------------------------------------------------
    D A S H B O A R D   V I E W (luego dividir en carpetas correspondientes) 
-----------------------------------------------------------------------------'''
def dashboardView(request):

    if 'token' not in request.session:
        return redirect('login')

    return render(
        request,
        'dashboard/dashboard.html'
    )

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
            request.session['token'] = datos.get('token')
            request.session['usuario'] = usuario

            # El token va también en la cookie compartida, para no tener que
            # iniciar sesión otra vez al entrar a la API desde el navegador.
            respuesta_http = redirect('dashboard')
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