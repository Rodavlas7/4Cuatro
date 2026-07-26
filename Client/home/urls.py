from django.urls import path
from .views import indexView, loginView, dashboardView, logoutView

urlpatterns = [
    path('', indexView, name='index'),
    path('login/', loginView, name='login'),
    path('dashboard/', dashboardView, name='dashboard'),
    path('logout/', logoutView, name='logout'),
]