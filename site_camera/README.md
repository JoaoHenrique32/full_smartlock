# 🔐 SmartLock - Sistema de Reconhecimento Facial IoT

O **SmartLock** é um sistema de controle de acesso inteligente que integra Visão Computacional, Desenvolvimento Web e IoT. O projeto utiliza IA para identificar usuários cadastrados e comandar a abertura de uma fechadura solenoide via MQTT.

---

## 🚀 Funcionalidades

* **Reconhecimento Facial:** Identificação em tempo real utilizando a biblioteca `DeepFace`.
* **Gestão de Usuários:** Interface administrativa para cadastrar novos rostos e revogar acessos.
* **Integração IoT:** Comunicação com NodeMCU ESP8266 para controle de hardware.
* **Logs de Acesso:** Persistência de dados em banco MySQL para auditoria.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.x, Django Framework.
* **IA/Visão:** OpenCV, DeepFace (VGG-Face).
* **Banco de Dados:** MySQL (via Docker).
* **Comunicação:** MQTT (Broker EMQX via Docker).
* **Hardware:** NodeMCU ESP8266, Módulo Relé, Solenoide 12V.

---

## 📦 Configuração e Instalação

### 1. Clonar o Repositório
```bash
git clone [https://github.com/JoaoHenrique32/sistema_smartlock](https://github.com/JoaoHenrique32/sistema_smartlock)
cd sistema_smartlock


2. Configurar o Ambiente Python
Recomenda-se o uso de um ambiente virtual:

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
.\venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source venv/bin/activate


3. Instalar Dependências

pip install -r requirements.txt


4. Subir Serviços (Docker)
O projeto utiliza Docker para gerenciar o Banco de Dados e o Broker MQTT:

instale o Docker Desktop e rode este codigo:

Terminal

docker run -d --name emqx -p 18083:18083 -p 1883:1883 emqx/emqx:latest
docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:latest


Apos isso você precisa criar o Conector.

Acesse http://localhost:18083 (admin / public).

No menu lateral, vá em Integration -> Connectors.

Clique em Create e escolha MySQL.

Configurações cruciais:

Server Host: Se estiver no Docker, use o IP da sua máquina ou o nome do container.

Database: Nome do banco que você criou (ex: projeto_aula).

User/Password: root e a senha que você definiu.


A regra/rule define o que salvar. O EMQX usa um SQL próprio para filtrar as mensagens MQTT.

Exemplo de SQL da Regra:

SQL
SELECT
  topic,
  payload as dados,
  clientid
FROM
  "t/#"

SELECT: O que eu quero pegar da mensagem.

FROM "t/#": De quais tópicos eu quero ouvir (o # é um curinga para "qualquer coisa depois de t/").


4. O Destino: A Ação (Data Integration)
Dentro da regra, você adiciona uma Action. É aqui que você escreve o INSERT que vai para o MySQL.

Template de SQL da Ação:

INSERT INTO mensagens_recebidas (topico, payload) VALUES (${topic}, ${payload});


5. Executar o Sistema

Terminal
python manage.py migrate
python manage.py runserver

Acesse em: http://127.0.0.1:8000


🔌 Configuração de Hardware (NodeMCU)
Abra o código contido na pasta /hardware (ou o projeto Fechadura_NodeMCU git: https://github.com/JoaoHenrique32/Fechadura_NodeMCU).

Configure as variáveis de rede no código:

ssid: Nome do seu Wi-Fi (2.4GHz).

password: Senha do Wi-Fi.

mqtt_server: O endereço IP do seu computador na rede.

Faça o upload para o NodeMCU ESP8266.