from rest_framework import serializers

from django.contrib.auth.models import User
from api import models

        
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        fields = ['usuario', 'contrasena', 'estado', 'empleado']
        

        
        
