from django.urls import path
from . import views

urlpatterns = [
    path('empaquetado/', views.embalajeListarView, name='embalaje-lista'),
    path('empaquetado/editar/<int:numero>/', views.embalajeEditarView, name='embalaje-editar'),
]