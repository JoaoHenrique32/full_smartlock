#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"
#include <ArduinoOTA.h>

// 2. --- CONFIGURAÇÕES DO MQTT (EMQX) ---
// CORREÇÃO 1: Usar IPAddress em vez de String/Char para burlar a validação de Hostname
IPAddress mqtt_server(192, 168, 1, 100); // Substitua pelo IP do seu broker MQTT
const int mqtt_port = 8883;              

// 3. --- PINOS DE HARDWARE (LEDS) ---
const int ledVerde = D5;     
const int ledVermelho = D7;  

// Instanciando os clientes seguros
WiFiClientSecure espClient;
PubSubClient client(espClient);
BearSSL::X509List cert(ca_cert);
BearSSL::X509List client_crt(client_cert);      // O crachá do NodeMCU
BearSSL::PrivateKey client_privkey(client_key); // A assinatura do NodeMCU 

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no tópico: ");
  Serial.println(topic);

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print("Erro ao ler JSON: ");
    Serial.println(error.c_str());
    return;
  }

  const char* status = doc["status"];
  Serial.print("Status recebido: ");
  Serial.println(status);

  if (String(status) == "LIBERADO") {
    Serial.println("Acesso Permitido! Acendendo LED Verde. 🟢");
    digitalWrite(ledVermelho, LOW);  
    digitalWrite(ledVerde, HIGH);    
    delay(3000);                     
    digitalWrite(ledVerde, LOW);     
    digitalWrite(ledVermelho, HIGH); 
    Serial.println("Fechadura travada novamente. 🔴");
  } else {
    Serial.println("Acesso Negado! Piscando LED Vermelho. ❌");
    digitalWrite(ledVermelho, LOW);
    delay(150);
    digitalWrite(ledVermelho, HIGH);
    delay(150);
    digitalWrite(ledVermelho, LOW);
    delay(150);
    digitalWrite(ledVermelho, HIGH);
  }
}

void reconectarMQTT() {
  while (!client.connected()) {
    Serial.print("🔐 Tentando conexão MQTT Segura (TLS)... ");
    
    const char* device_id = "device-201";

    if (client.connect(device_id, device_id, "")) {
      Serial.println(" Conectado com SUCESSO ao EMQX!");
      client.subscribe("t/fechadura");
    } else {
      Serial.print(" Falhou, rc=");
      Serial.print(client.state());
      
      // CORREÇÃO 2: Exibe o erro real escondido dentro da camada TLS (BearSSL)
      char error_buf[100];
      espClient.getLastSSLError(error_buf, sizeof(error_buf));
      Serial.print(" | Erro TLS Real: ");
      Serial.println(error_buf);
      
      Serial.println("Tentando de novo em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(ledVerde, OUTPUT);
  pinMode(ledVermelho, OUTPUT);
  
  digitalWrite(ledVerde, LOW);
  digitalWrite(ledVermelho, HIGH);

  Serial.println();
  Serial.print("Conectando-se à rede: ");
  Serial.println(ssid);
   
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado. IP: " + WiFi.localIP().toString());

  configTime(-3 * 3600, 0, "a.st1.ntp.br", "b.st1.ntp.br");
  Serial.print("⏱️ Sincronizando relógio via NTP para validação TLS...");
  time_t now = time(nullptr);
  while (now < 100000) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\n✅ Relógio sincronizado com a internet!");

  // CORREÇÃO 3: Otimização de buffers para não estourar a memória RAM do NodeMCU
  espClient.setBufferSizes(2048, 512);

  // Alimenta o cliente com o certificado CA do secrets.h
  espClient.setTrustAnchors(&cert);

  // Diz ao ESP quem é o servidor confiável
  espClient.setTrustAnchors(&cert);

  // 🔴 ATIVAÇÃO DO mTLS: Entrega o crachá e a chave para o servidor validar!
  espClient.setClientRSACert(&client_crt, &client_privkey);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // --- CONFIGURAÇÃO DO ARDUINO OTA ---
  ArduinoOTA.setPort(8266); // Porta padrão do ESP8266
  ArduinoOTA.setHostname("device-201"); // Nome do dispositivo que aparecerá na rede
  ArduinoOTA.setPassword("fechadura123"); // 🔒 Senha de segurança para autorizar o upload sem fios

  ArduinoOTA.onStart([]() {
    Serial.println("🔄 Início da atualização remota (OTA)...");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\n✅ Atualização concluída com sucesso! A reiniciar...");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("⏳ Progresso: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("🚨 Erro [%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Falha na autenticação (Senha errada)");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Falha ao iniciar gravação");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Falha de ligação");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Falha na receção de dados");
    else if (error == OTA_END_ERROR) Serial.println("Falha na finalização");
  });

  ArduinoOTA.begin();
  Serial.println("📶 Serviço OTA iniciado e pronto na rede local!");
}

void loop() {
  if (!client.connected()) {
    reconectarMQTT();
  }
  client.loop();

  // 🔴 Executa o serviço OTA em cada ciclo para escutar atualizações na rede
  ArduinoOTA.handle();
}