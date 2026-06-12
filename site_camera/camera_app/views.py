import ssl

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from .models import LogAcesso, PerfilUsuario
from django.core.files.base import ContentFile
import json
import base64
import numpy as np
import cv2
import paho.mqtt.client as mqtt
import os
from deepface import DeepFace

# ... (mantenha os imports e as funções de API identify_face e register_face que já fizemos)

# --- CONFIGURAÇÃO MQTT ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 8883
MQTT_TOPIC = "t/fechadura"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

caminho_certificado = os.path.join(settings.BASE_DIR, '..', 'phase-1-mocking', 'docker', 'emqx', 'certs', 'cacert.pem')

try:
    # Ativa a criptografia usando o seu cartório
    client.tls_set(ca_certs=caminho_certificado, tls_version=ssl.PROTOCOL_TLSv1_2)
    # Ignora a verificação estrita de domínio (igual ao setInsecure() do C++)
    client.tls_insecure_set(True) 
    
    # Conecta e inicia
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("✅ Python conectado ao MQTT Seguro com sucesso!")
except Exception as e:
    print(f"❌ Erro fatal no MQTT do Python: {e}")
    
def index(request):
    """Renderiza a página principal com a lista de usuários cadastrados"""
    db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
    usuarios_cadastrados = []
    
    if os.path.exists(db_path):
        # Lista arquivos .jpg e remove a extensão para exibir o nome
        for arquivo in os.listdir(db_path):
            if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                nome = os.path.splitext(arquivo)[0]
                usuarios_cadastrados.append(nome)
                
    return render(request, 'index.html', {'usuarios': usuarios_cadastrados})

@csrf_exempt
def delete_face(request):
    """Recebe o nome via POST e deleta a foto correspondente"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nome_usuario = data.get('nome')
            
            # Caminho da foto (ajuste a extensão se necessário)
            caminho_arquivo = os.path.join(settings.BASE_DIR, "banco_rostos", f"{nome_usuario}.jpg")
            
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
                return JsonResponse({"status": "sucesso", "mensagem": f"Usuário {nome_usuario} removido!"})
            else:
                return JsonResponse({"status": "erro", "mensagem": "Arquivo não encontrado."})
                
        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)})

    return JsonResponse({"status": "invalido"})

# O @csrf_exempt permite que o site envie dados sem dar erro de segurança na fase de testes
@csrf_exempt 
def identify_face(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]

            # Converte a imagem do site para o padrão OpenCV
            img_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # Aponta para a pasta onde o botão azul está salvando as fotos
            db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
            
            # Trava de segurança: e se a pasta estiver vazia?
            if not os.path.exists(db_path) or len(os.listdir(db_path)) == 0:
                return JsonResponse({"status": "erro", "mensagem": "O banco de dados está vazio. Cadastre alguém primeiro!"})

            print("Procurando rosto no banco de dados...")
            
            # O coração da IA: Compara a foto da câmera com a pasta
            results = DeepFace.find(img_path=frame, db_path=db_path, enforce_detection=False, model_name="VGG-Face")

            # Verifica se encontrou alguém (O DeepFace retorna uma lista de DataFrames)
            # ... (código do DeepFace buscando o rosto) ...

            if len(results) > 0 and not results[0].empty:
                    # 1. Extrai o nome do usuário
                    caminho_completo = results[0]['identity'][0]
                    nome_arquivo = os.path.basename(caminho_completo)
                    usuario = os.path.splitext(nome_arquivo)[0]
                    
                    # 2. Salva no Log de Acessos
                    user_obj = User.objects.filter(username=usuario).first()
                    if user_obj:
                        LogAcesso.objects.create(usuario=user_obj, autorizado=True, metodo="Reconhecimento Facial")
                    
                    # 3. Manda o sinal pro NodeMCU abrir a porta
                    msg = f'{{"aluno": "{usuario}", "status": "LIBERADO"}}'
                    client.publish(MQTT_TOPIC, msg)
                    
                    # 4. A CORREÇÃO: Esse return DEVE estar aqui para interromper a descida!
                    return JsonResponse({"status": "sucesso", "mensagem": f"Acesso Liberado! Bem-vindo(a), {usuario}."})
                
            else:
                    # 1. Salva a tentativa falha no Log
                    LogAcesso.objects.create(usuario=None, autorizado=False, metodo="Reconhecimento Facial")
                    
                    # 2. Manda o sinal pro NodeMCU travar a porta
                    msg = '{"aluno": "Desconhecido", "status": "NEGADO"}'
                    client.publish(MQTT_TOPIC, msg)
                    
                    # 3. A CORREÇÃO: Esse return DEVE estar aqui também!
                    return JsonResponse({"status": "erro", "mensagem": "Acesso Negado: Rosto não reconhecido."})

        except Exception as e:
                print(f"Erro na identificação: {e}")
                return JsonResponse({"status": "erro", "mensagem": str(e)})

        # Só cai neste "invalido" se a requisição não for POST ou der algo muito errado
        return JsonResponse({"status": "invalido"})

@csrf_exempt 
def register_face(request):
    if request.method == 'POST':
        try:
            # 1. Recebe os dados
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]
            nome_usuario = data['nome'].strip() # Tira espaços em branco do nome

            # 2. Usa a pasta raiz do seu projeto Django para o DeepFace
            db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
            
            # Cria a pasta se não existir
            if not os.path.exists(db_path):
                os.makedirs(db_path)
                print(f"📁 Pasta criada em: {db_path}")

            # 3. Converte e Salva na pasta física
            img_bytes = base64.b64decode(image_data)
            caminho_arquivo = os.path.join(db_path, f"{nome_usuario}.jpg")

            with open(caminho_arquivo, "wb") as arquivo_foto:
                arquivo_foto.write(img_bytes)

            # ==========================================================
            # 4. A PONTE: Salva no Banco de Dados SQLite para o Painel Admin
            # ==========================================================
            user, created = User.objects.get_or_create(username=nome_usuario)
            perfil, perfil_created = PerfilUsuario.objects.get_or_create(user=user)
            # Anexa a foto também no registro do banco de dados
            perfil.foto_referencia.save(f"{nome_usuario}_db.jpg", ContentFile(img_bytes), save=True)

            # Avisa no terminal do VS Code
            print(f"✅ SUCESSO! {nome_usuario} salvo na pasta e registrado no banco de dados.")

            return JsonResponse({"status": "sucesso", "mensagem": f"Rosto de {nome_usuario} salvo com sucesso!"})

        except Exception as e:
            print(f"❌ ERRO NO PYTHON: {e}")
            return JsonResponse({"status": "erro", "mensagem": str(e)})

    return JsonResponse({"status": "invalido"})
