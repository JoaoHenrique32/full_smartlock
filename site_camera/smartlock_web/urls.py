from django.contrib import admin
from django.urls import path
from camera_app import views
from camera_app.views import index, identify_face, register_face, delete_face
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('identify/', views.identify_face, name='identify_face'),
    path('register/', views.register_face, name='register_face'),
    path('delete/', views.delete_face, name='delete_face'),
]

# Isso ensina o Django a servir arquivos da pasta "rostos_cadastrados" apenas no ambiente de testes local
if settings.DEBUG:
    urlpatterns += static(
        '/rostos_cadastrados/', 
        document_root=os.path.join(settings.BASE_DIR, 'rostos_cadastrados')
    )