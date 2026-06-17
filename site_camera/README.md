# 🧠 Módulo Backend & Motor de IA (Site-camera)

Este diretório contém o cérebro central do ecossistema SmartLock. Construído em **Python** e estruturado com o framework **Django**, este módulo é responsável por processar o feed de vídeo, executar a validação biométrica e atuar como o publicador (Publisher) das decisões de acesso na rede MQTT.

---

## ⚙️ O que este módulo faz?

* **Visão Computacional:** Utiliza o OpenCV para capturar a webcam e a biblioteca `DeepFace` (modelo VGG-Face) para extrair os embeddings faciais e comparar com o banco de rostos local.
* **Painel Administrativo Web:** Interface para monitoramento do terminal em tempo real.
* **Cliente MQTT Integrado:** Utiliza a biblioteca `paho-mqtt` com suporte a certificados mTLS para enviar o veredito (`LIBERADO` ou `NEGADO`) para o barramento de dados instantaneamente.
* **API de Sincronização:** Aguarda comandos do aplicativo móvel (Flutter) para salvar novos rostos no File System e persistir o cadastro de usuários no SQLite.

---

## 🛠️ Instalação e Execução Local

Este passo a passo é focado apenas na execução do servidor Django. Certifique-se de que o Broker MQTT (EMQX) já esteja rodando na sua máquina.

### 1. Criar o Ambiente Virtual
Recomenda-se isolar as dependências deste módulo usando o `venv`:
```bash
python -m venv venv

# Ativar no Windows:
.\venv\Scripts\activate

# Ativar no Linux/Mac:
source venv/bin/activate

```

### 2. Instalar as Bibliotecas

Como lidamos com modelos pesados de Inteligência Artificial, a instalação das dependências pode levar alguns minutos:

```bash
pip install -r requirements.txt

```

### 3. Preparar o Banco de Dados (SQLite)

Aplique as migrações necessárias para a criação das tabelas de logs e usuários:

```bash
python manage.py makemigrations
python manage.py migrate

```

### 4. Rodar o Servidor Web

Inicie o processo do Django. Ao iniciar a primeira vez, o DeepFace poderá fazer o download automático dos pesos do modelo VGG-Face (aprox. 500MB).

```bash
python manage.py runserver

```

> Acesse a interface web em: `http://127.0.0.1:8000`

---

## 📁 Estrutura do Diretório

* `/banco_rostos/` -> Armazenamento persistente (File System) das faces autorizadas (.jpg).
* `/temp_rostos/` -> Cache temporário de rostos aguardando a aprovação do administrador via App.
* `/certs_emqx/` -> Certificados criptográficos (CA) para autorização da conexão mTLS.
* `views.py` -> Contém a lógica principal do DeepFace e os callbacks do MQTT.
