from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_referencia = models.ImageField(upload_to='rostos_cadastrados/')
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

class LogAcesso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    autorizado = models.BooleanField()
    metodo = models.CharField(max_length=50, default="Reconhecimento Facial")

    def __str__(self):
        status = "Autorizado" if self.autorizado else "Negado"
        return f"{self.timestamp} - {self.usuario} ({status})"