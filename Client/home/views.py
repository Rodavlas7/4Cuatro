from django.shortcuts import render
from django.shortcuts import render, redirect
import requests


# Create your views here.


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

            return redirect('dashboard')
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
    return redirect('login')