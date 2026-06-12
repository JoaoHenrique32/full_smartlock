#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

// 1. --- CONFIGURAÇÕES DE REDE ---
const char* ssid = SECRET_SSID;         // ◄ Puxa do secrets.h
const char* password = SECRET_PASS;     // ◄ Puxa do secrets.h

// 2. --- CONFIGURAÇÕES DO MQTT (EMQX) ---
const char* mqtt_server = ""; // IP da sua máquina
const int mqtt_port = 8883;              // Porta TLS Segura

// 3. --- PINOS DE HARDWARE (LEDS) ---
const int ledVerde = D5;     // Indica Acesso Liberado
const int ledVermelho = D7;  // Indica Acesso Negado / Porta Travada

// 4. --- O SEU CERTIFICADO DE SEGURANÇA (Cole o texto do cacert.pem aqui) ---

// Instanciando os clientes seguros
X509List cert(SECRET_CACERT);
WiFiClientSecure espClient;
PubSubClient client(espClient);

// Função que escuta as mensagens do EMQX
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensagem recebida no tópico: ");
  Serial.println(topic);

  // Transformando os bytes em texto legível (JSON)
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print("Erro ao ler JSON: ");
    Serial.println(error.c_str());
    return;
  }

  // Lendo o status
  const char* status = doc["status"];
  Serial.print("Status recebido: ");
  Serial.println(status);

  if (String(status) == "LIBERADO") {
    Serial.println("Acesso Permitido! Acendendo LED Verde. 🟢");
    digitalWrite(ledVermelho, LOW);  // Apaga o vermelho
    digitalWrite(ledVerde, HIGH);    // Acende o verde
    delay(3000);                     // Mantém "aberto" por 3 segundos
    digitalWrite(ledVerde, LOW);     // Apaga o verde
    digitalWrite(ledVermelho, HIGH); // Acende o vermelho novamente
    Serial.println("Fechadura travada novamente. 🔴");
  } else {
    Serial.println("Acesso Negado! Piscando LED Vermelho. ❌");
    // Pisca o vermelho rapidamente para dar feedback de rejeição
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
    Serial.print("Tentando conectar ao MQTT Seguro...");
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println(" Conectado!");
      client.subscribe("t/fechadura");
    } else {
      Serial.print(" Falhou, rc=");
      Serial.print(client.state());
      Serial.println(" Tentando de novo em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(ledVerde, OUTPUT);
  pinMode(ledVermelho, OUTPUT);
  
  // Garante que o sistema inicie no estado "Travado"
  digitalWrite(ledVerde, LOW);
  digitalWrite(ledVermelho, HIGH);

  // Conectando ao Wi-Fi
  Serial.println();
  Serial.print("Conectando-se à rede: ");
  Serial.println(ssid);
  // --- FORÇANDO O IP FIXO PARA DRIBLAR O ROTEADOR TIM ---
  IPAddress local_IP(192, 168, 1, 50); // O IP obrigatório do NodeMCU
  IPAddress gateway(192, 168, 1, 1);   // A porta do seu roteador
  IPAddress subnet(255, 255, 255, 0);  // A máscara da rede

  WiFi.config(local_IP, gateway, subnet); // Aplica a configuração
  // ------------------------------------------------------
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado. IP: " + WiFi.localIP().toString());

  // Configurando a Segurança (TLS) no modo de laboratório (Insecure)
  espClient.setTrustAnchors(&cert);
  espClient.setInsecure(); 

  // Configurando o MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconectarMQTT();
  }
  client.loop();
}