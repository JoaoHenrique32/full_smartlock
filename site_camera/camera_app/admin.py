from django.contrib import admin
from .models import PerfilUsuario, LogAcesso

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'data_cadastro')
    search_fields = ('user__username',)

@admin.register(LogAcesso)
class LogAcessoAdmin(admin.ModelAdmin):
    # Mostra colunas bonitas no painel
    list_display = ('usuario', 'timestamp', 'autorizado', 'metodo')
    # Cria um menu lateral para você filtrar os acessos negados ou autorizados
    list_filter = ('autorizado', 'metodo', 'timestamp')
    search_fields = ('usuario__username',)