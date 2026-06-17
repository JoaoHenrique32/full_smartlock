# 🔒 Documentação Oficial: SmartLock IA

> **Status:** Operacional (Ambiente de Produção Local)
> **Versão:** 1.0.0

[ IMAGEM: Inserir aqui a foto principal do sistema / banner do projeto ]

---

## 📖 Índice
1. [Visão Geral do Sistema](#-visão-geral-do-sistema)
2. [Arquitetura e Tecnologias](#-arquitetura-e-tecnologias)
3. [Segurança e Criptografia (mTLS)](#-segurança-e-criptografia-mtls)
4. [Guia de Execução (Passo a Passo)](#-guia-de-execução-passo-a-passo)
5. [Fluxo de Operação e Cadastro](#-fluxo-de-operação-e-cadastro)
6. [Sobre o Autor](#-sobre-o-autor)

---

## 🎯 Visão Geral do Sistema

O **SmartLock IA** é uma solução completa de controle de acesso físico baseada em Internet das Coisas (IoT) e Visão Computacional. Projetado para rodar de forma 100% local (sem dependência de nuvem externa para processamento crítico), o sistema oferece liberação de portas em tempo real via reconhecimento facial, além de um painel de administração mobile para gestão de permissões.

---

## 🛠️ Arquitetura e Tecnologias

O ecossistema foi desenhado em uma topologia Cliente-Servidor altamente desacoplada, utilizando o protocolo MQTT como barramento principal de mensagens.

[ IMAGEM: Inserir diagrama da arquitetura (Câmera -> Python -> EMQX -> NodeMCU / App Flutter) ]

* **Microcontrolador (Hardware):** Placa NodeMCU ESP8266 programada em **C++** (PlatformIO) com relé de acionamento.
* **Cérebro de IA:** Servidor backend em **Python + Django**, utilizando a biblioteca **DeepFace** (Modelo VGG-Face) para análise e extração de biometria facial via OpenCV.
* **Mensageria em Tempo Real:** Broker **EMQX** isolado em um container **Docker**.
* **Painel Administrativo:** Aplicativo Mobile/Desktop desenvolvido em **Flutter (Dart)**.

---

## 🔐 Segurança e Criptografia (mTLS)

Para evitar interceptação de dados ou acionamentos falsos na rede Wi-Fi, o broker MQTT foi configurado com **Mutual TLS (mTLS)**. Isso significa que o servidor e os clientes (Fechadura, Python e App) precisam apresentar um "passaporte" criptográfico válido para se comunicarem.

### Como os Certificados Foram Criados
A infraestrutura de chaves públicas (PKI) foi construída localmente utilizando o `OpenSSL`.

**1. Criação da Autoridade Certificadora (CA):**
Foi gerada a chave raiz e o certificado que assinará todos os outros dispositivos.
```bash
openssl req -new -x509 -days 3650 -keyout ca.key -out cacert.pem

```

**2. Geração do Certificado do Servidor (EMQX):**
Foi criada a chave privada do servidor e a requisição de assinatura (CSR), que posteriormente foi assinada pela CA gerada no passo anterior.

```bash
openssl genrsa -out emqx.key 2048
openssl req -new -key emqx.key -out emqx.csr
openssl x509 -req -in emqx.csr -CA cacert.pem -CAkey ca.key -CAcreateserial -out emqx.pem -days 3650

```

**3. Geração dos Certificados dos Clientes:**
O mesmo processo foi repetido para gerar o `client.key` e o `client.pem`. Esses arquivos foram embarcados no código C++ do NodeMCU e na pasta raiz do Django, garantindo que apenas dispositivos com essas chaves consigam publicar no tópico da fechadura.

---

## 🚀 Guia de Execução (Passo a Passo)

Para levantar o sistema completo a partir do zero, é necessário iniciar cada nó da arquitetura em terminais separados, seguindo a ordem de dependência abaixo.

### Passo 1: O Barramento de Mensagens (Docker)

O EMQX deve ser o primeiro a iniciar para receber as conexões.

1. Abra o terminal na raiz do projeto e navegue até a pasta do Docker:
```bash
cd docker/emqx

```


2. Inicie o container em segundo plano:
```bash
docker compose up -d

```



> **Nota:** O painel de controle do broker ficará acessível no navegador através de `http://localhost:18083`.

### Passo 2: O Motor de IA e Backend (Python/Django)

Responsável por gerenciar o banco de rostos e a câmera.

1. Em um **novo terminal**, navegue até a pasta do site:
```bash
cd site_camera

```


2. Inicie o servidor de desenvolvimento do Django:
```bash
python manage.py runserver

```



> **Nota:** A interface da câmera web ficará ativa em `http://localhost:8000`. Neste momento, o terminal exibirá a mensagem de sucesso da conexão MQTT com o EMQX.

### Passo 3: O Painel de Controle (App Flutter)

O aplicativo do administrador para visualização e controle.

1. Em um **terceiro terminal**, navegue até a pasta do aplicativo mobile:
```bash
cd smartlock_admin

```


2. Execute o aplicativo nativamente:
```bash
flutter run -d windows

```



[ IMAGEM: Inserir fotos do App Flutter (Tela de aprovações pendentes e Galeria de usuários) ]

### Passo 4: O Hardware (Fechadura Inteligente)

1. Conecte o **NodeMCU ESP8266** via cabo USB (ou certifique-se de que ele está ligado na fonte).
2. Abra a pasta do hardware no VS Code (ambiente configurado com **PlatformIO**).
3. Garanta que o arquivo `secrets.h` contém o IP IPv4 atual da sua máquina local.
4. Clique no botão de **Upload** na barra inferior do PlatformIO para compilar e enviar o firmware em C++.

[ IMAGEM: Inserir foto física do NodeMCU conectado ao circuito/fechadura ]

---

## 📱 Fluxo de Operação e Cadastro

A interação entre as pontas foi projetada para exigir intervenção humana apenas no momento do cadastro inicial:

1. **Solicitação:** Um visitante se posiciona em frente à câmera da aplicação web, digita seu nome e clica em "Cadastrar Novo Rosto".
2. **Espera:** O Django extrai o *frame* em base64, salva temporariamente e envia um pacote JSON via MQTT para o tópico `smartlock/pendentes`. A porta permanece travada.
3. **Notificação:** O App Flutter do administrador recebe a notificação em tempo real, exibindo a foto capturada e o nome.
4. **Autorização:** O administrador clica em **Aprovar**. O App publica a permissão no tópico de respostas.
5. **Efetivação:** O backend Python move a foto para o banco de dados oficial, criando o perfil definitivo do usuário.
6. **Acesso Futuro:** Nas próximas vezes que essa pessoa aparecer na câmera e o sistema tentar identificar, o *DeepFace* fará a validação instantânea, disparando o comando de "LIBERADO" direto para o NodeMCU abrir a porta automaticamente.

---

## 👨‍💻 Sobre o Autor

Desenvolvido por **João Henrique Corrêa de Araújo**, estudante do 6º período de Ciência da Computação na Faculdade Nova Roma. O projeto reflete a aplicação prática de conceitos de Engenharia de Software, Redes, Criptografia e Inteligência Artificial.

* **Conecte-se:**
* [GitHub](https://github.com/JoaoHenrique32/full_smartlock)

