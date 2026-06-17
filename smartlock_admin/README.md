# 📱 Painel Administrativo Mobile (smartlock_admin)

Este diretório contém o front-end do ecossistema SmartLock, desenvolvido nativamente em **Flutter (Dart)**. O aplicativo atua como o painel mestre do gestor de segurança, comunicando-se em tempo real com o hardware e a inteligência artificial através de um barramento MQTT criptografado.

---

## ⚙️ O que este módulo faz?

* **Gestão de Acessos Pendentes:** Inscreve-se nos tópicos MQTT para receber alertas imediatos quando a IA detecta um rosto desconhecido. O gestor visualiza a foto capturada e pode **Aprovar** ou **Negar** o cadastro remotamente.
* **Galeria de Usuários (Banco de Rostos):** Sincroniza e exibe a lista de usuários que possuem autorização ativa no banco de dados SQLite do backend.
* **Comunicação Assíncrona:** Utiliza um cliente MQTT integrado ao Flutter para enviar comandos JSON de liberação e atualizações de banco de dados sem depender de requisições HTTP tradicionais.
* **UI/UX Moderna:** Interface desenhada sob medida, com temática *dark*, focada em uma experiência de usuário (UX) fluida e alertas visuais claros.

---

## 🛠️ Instalação e Execução Local

Certifique-se de ter o [Flutter SDK](https://docs.flutter.dev/get-started/install) instalado na sua máquina. O aplicativo está configurado atualmente para rodar como uma aplicação Windows Desktop, mas pode ser compilado para Android/iOS.

### 1. Atualizar as Credenciais de Rede
Antes de rodar o aplicativo, é **crucial** apontar o aplicativo para o servidor correto.
1. Abra o arquivo principal do aplicativo (geralmente `lib/main.dart` ou o arquivo de configuração MQTT).
2. Localize a função de conexão (ex: `MqttServerClient`) e atualize o endereço IP para o **IP atual do seu computador** ou do Roteador Wi-Fi (Hotspot) que está hospedando o broker EMQX.

### 2. Instalar Dependências
Navegue até a pasta do aplicativo e baixe os pacotes necessários definidos no `pubspec.yaml`:
```bash
flutter pub get

```

### 3. Rodar o Aplicativo

Inicie o aplicativo no modo de depuração para Windows:

```bash
flutter run -d windows

```

> *Dica:* Pressione `r` no terminal enquanto o app estiver rodando para aplicar o *Hot Reload* nas atualizações de interface.

---

## 📁 Estrutura Principal

* `/lib/` -> Contém todo o código-fonte em Dart (Telas, Lógica MQTT, Componentes de UI).
* `/windows/` -> Arquivos de configuração nativos para a compilação desktop.
* `pubspec.yaml` -> Gerenciador de pacotes e declaração de assets (imagens/fontes).
