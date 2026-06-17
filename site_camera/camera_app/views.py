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
import time
import shutil
from datetime import datetime
from deepface import DeepFace

# --- FUNÇÃO QUE CUIDA DAS MENSAGENS RECEBIDAS ---
def on_message(client, userdata, msg):
    # 1. ADM respondeu se aprova ou nega o cadastro
    if msg.topic == "smartlock/respostas":
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            req_id = data.get("id")
            aprovado = data.get("aprovado")
            nome_usuario = data.get("nome")

            temp_path = os.path.join(settings.BASE_DIR, "temp_rostos", f"{req_id}.jpg")
            db_path = os.path.join(settings.BASE_DIR, "banco_rostos")

            if aprovado:
                print(f"📱 ADM APROVOU o cadastro de {nome_usuario}!")
                if os.path.exists(temp_path):
                    if not os.path.exists(db_path):
                        os.makedirs(db_path)
                    
                    final_path = os.path.join(db_path, f"{nome_usuario}.jpg")
                    shutil.move(temp_path, final_path)
                    
                    with open(final_path, "rb") as f:
                        img_bytes = f.read()
                    
                    user, created = User.objects.get_or_create(username=nome_usuario)
                    perfil, perfil_created = PerfilUsuario.objects.get_or_create(user=user)
                    perfil.foto_referencia.save(f"{nome_usuario}_db.jpg", ContentFile(img_bytes), save=True)
                    
                    # Pede pro app atualizar a lista de usuários automaticamente
                    client.publish("smartlock/pedir_usuarios", '{"update": true}')
            else:
                print(f"📱 ADM NEGOU o cadastro de {nome_usuario}.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"🚨 Erro na resposta: {e}")

    # 2. App pediu a lista de usuários cadastrados
    # 2. App pediu a lista de usuários cadastrados
    elif msg.topic == "smartlock/pedir_usuarios":
        db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
        usuarios = []
        if os.path.exists(db_path):
            for file in os.listdir(db_path):
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    nome = os.path.splitext(file)[0]
                    caminho = os.path.join(db_path, file)
                    
                    # 🔴 AQUI ESTÁ A NOVIDADE: Captura a data exata de criação do arquivo da foto
                    timestamp = os.path.getmtime(caminho)
                    data_cadastro = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
                    
                    # Lemos a imagem e diminuímos o tamanho dela para não travar a rede MQTT
                    img = cv2.imread(caminho)
                    if img is not None:
                        img_small = cv2.resize(img, (150, 150)) # Miniatura
                        _, buffer = cv2.imencode('.jpg', img_small)
                        foto_b64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # 🔴 AQUI ENVIAMOS A DATA JUNTO:
                        usuarios.append({
                            "nome": nome, 
                            "foto": foto_b64,
                            "data_cadastro": data_cadastro
                        })
        
        # Envia a lista completa de volta pro App
        client.publish("smartlock/lista_usuarios", json.dumps(usuarios), qos=1)

# --- CONFIGURAÇÃO MQTT ---
MQTT_BROKER = "coloque o IP do seu broker MQTT aqui" 
MQTT_PORT = 8883
MQTT_TOPIC = "t/fechadura"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

caminho_certificado = os.path.join(settings.BASE_DIR, 'certs_emqx', 'cacert.pem')

try:
    client.tls_set(ca_certs=caminho_certificado, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.tls_insecure_set(True) 
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Python escuta respostas e pedidos de lista
    client.subscribe("smartlock/respostas", qos=1)
    client.subscribe("smartlock/pedir_usuarios", qos=1)
    
    client.loop_start()
    
    print("✅ Python conectado ao MQTT Seguro com sucesso e escutando o App Flutter!")
    
except Exception as e:
    print(f"❌ Erro MQTT Python: {e}")
    
def index(request):
    db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
    usuarios_cadastrados = []
    if os.path.exists(db_path):
        for arquivo in os.listdir(db_path):
            if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                usuarios_cadastrados.append(os.path.splitext(arquivo)[0])
    return render(request, 'index.html', {'usuarios': usuarios_cadastrados})

@csrf_exempt
def delete_face(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        caminho = os.path.join(settings.BASE_DIR, "banco_rostos", f"{data.get('nome')}.jpg")
        if os.path.exists(caminho):
            os.remove(caminho)
            client.publish("smartlock/pedir_usuarios", '{"update": true}') # Atualiza App
            return JsonResponse({"status": "sucesso"})
    return JsonResponse({"status": "erro"})

@csrf_exempt 
def identify_face(request):
    # VOLTOU A SER COMO ERA ANTES: Identifica ou Bloqueia, sem chamar o App
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            img_bytes = base64.b64decode(data['image'].split(',')[1])
            frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            db_path = os.path.join(settings.BASE_DIR, "banco_rostos")
            
            if not os.path.exists(db_path) or len(os.listdir(db_path)) == 0:
                return JsonResponse({"status": "erro", "mensagem": "Banco de dados vazio!"})

            try:
                results = DeepFace.find(img_path=frame, db_path=db_path, enforce_detection=True, model_name="VGG-Face")
            except ValueError:
                client.publish(MQTT_TOPIC, '{"aluno": "Desconhecido", "status": "NEGADO"}')
                return JsonResponse({"status": "erro", "mensagem": "Nenhum rosto detectado."})

            if len(results) > 0 and not results[0].empty:
                usuario = os.path.splitext(os.path.basename(results[0]['identity'][0]))[0]
                user_obj = User.objects.filter(username=usuario).first()
                if user_obj: LogAcesso.objects.create(usuario=user_obj, autorizado=True, metodo="Facial")
                
                client.publish(MQTT_TOPIC, f'{{"aluno": "{usuario}", "status": "LIBERADO"}}')
                return JsonResponse({"status": "sucesso", "mensagem": f"Acesso Liberado: {usuario}."})
            else:
                LogAcesso.objects.create(usuario=None, autorizado=False, metodo="Facial")
                client.publish(MQTT_TOPIC, '{"aluno": "Desconhecido", "status": "NEGADO"}')
                return JsonResponse({"status": "erro", "mensagem": "Acesso Negado: Rosto não reconhecido."})

        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)})

@csrf_exempt 
def register_face(request):
    # A MÁGICA ESTÁ AQUI: Clicou em cadastrar? Manda pro App!
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(',')[1]
            nome_usuario = data['nome'].strip()

            img_bytes = base64.b64decode(image_data)
            req_id = str(int(time.time() * 1000))
            
            temp_dir = os.path.join(settings.BASE_DIR, "temp_rostos")
            if not os.path.exists(temp_dir): os.makedirs(temp_dir)
                
            with open(os.path.join(temp_dir, f"{req_id}.jpg"), "wb") as f:
                f.write(img_bytes)

            # Envia pro App e aguarda
            payload_app = {
                "id": req_id,
                "nome": nome_usuario, # Nome digitado no painel da web!
                "data": datetime.now().strftime("%d/%m/%Y - %H:%M"),
                "foto": image_data
            }
            client.publish("smartlock/pendentes", json.dumps(payload_app), qos=1)

            return JsonResponse({"status": "sucesso", "mensagem": "Aguardando aprovação do Administrador no App..."})

        except Exception as e:
            return JsonResponse({"status": "erro", "mensagem": str(e)})
    return JsonResponse({"status": "invalido"})