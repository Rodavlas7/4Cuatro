from django.urls import path
from .views import loginView, dashboardView, logoutView

urlpatterns = [
    path('login/', loginView, name='login'),
    path('dashboard/', dashboardView, name='dashboard'),
    path('logout/', logoutView, name='logout'),
]