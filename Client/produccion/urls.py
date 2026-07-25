from django.urls import path
from . import views

urlpatterns = [
    # Ensamblaje
    path('ensamblaje/registrar/', views.ensamblajeRegistrarView, name='ensamblaje-registrar'),
]
