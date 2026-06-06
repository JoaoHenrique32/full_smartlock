#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- 1. PREENCHA COM OS DADOS DA SUA CASA/FACULDADE ---
const char* ssid = "LIVE TIM_3CF0_2G";      
const char* password = "f6axp43c73"; 

// --- 2. O IP DO SEU COMPUTADOR ---
// O ESP8266 NÃO entende "localhost". Ele precisa do IP real da sua máquina na rede (ex: 192.168.1.15)
const char* mqtt_server = "192.168.1.4";    
const char* mqtt_topic = "t/fechadura";

// --- 3. PINOS DE HARDWARE ---
const int pinoAcessoLiberado = D5;  // LED Verde ou Relé da Fechadura
const int pinoAcessoNegado = D7;    // LED Vermelho ou Buzzer

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando na rede Wi-Fi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado com sucesso!");
  Serial.print("IP do ESP8266: ");
  Serial.println(WiFi.localIP());
}

// --- A MÁGICA ACONTECE AQUI: Quando a mensagem do Django chega ---
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("\nMensagem recebida no tópico: ");
  Serial.println(topic);

  // 1. Converte os bytes recebidos para uma String (o JSON)
  String mensagem = "";
  for (int i = 0; i < length; i++) {
    mensagem += (char)payload[i];
  }
  Serial.println("Conteúdo: " + mensagem);

  // 2. Extrai as informações usando o ArduinoJson
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, mensagem);

  if (error) {
    Serial.print("Erro ao ler o JSON: ");
    Serial.println(error.c_str());
    return;
  }

  // Pega as variáveis que vieram do Python
  const char* status_acesso = doc["status"];
  const char* nome_aluno = doc["aluno"];

  // 3. TOMA A DECISÃO FÍSICA
  if (String(status_acesso) == "LIBERADO") {
    Serial.print("🔓 ABRINDO PORTA PARA: ");
    Serial.println(nome_aluno);
    
    digitalWrite(pinoAcessoLiberado, HIGH); // Liga o Verde
    digitalWrite(pinoAcessoNegado, LOW);    // Garante que o Vermelho tá desligado
    
    delay(4000); // Mantém a porta aberta por 4 segundos
    
    digitalWrite(pinoAcessoLiberado, LOW);  // Tranca a porta de novo
    Serial.println("🔒 Porta trancada novamente.");

  } else if (String(status_acesso) == "NEGADO") {
    Serial.println("🚫 ACESSO NEGADO! Estranho detectado.");
    
    // Pisca o LED vermelho rápido 3 vezes para alertar
    for(int i=0; i<3; i++){
      digitalWrite(pinoAcessoNegado, HIGH);
      delay(200);
      digitalWrite(pinoAcessoNegado, LOW);
      delay(200);
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao Broker MQTT no IP ");
    Serial.print(mqtt_server);
    Serial.print("...");
    
    String clientId = "NodeMCU-Fechadura-" + String(random(0xffff), HEX);
    
    // Conecta no EMQX (Sem usuário e senha, pois você liberou acesso público)
    if (client.connect(clientId.c_str())) {
      Serial.println(" Conectado!");
      client.subscribe(mqtt_topic); // Se inscreve no tópico para ouvir o Django
    } else {
      Serial.print(" Falhou, erro rc=");
      Serial.print(client.state());
      Serial.println(" Tentando de novo em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  // Configura os pinos como saída e garante que começam desligados
  pinMode(pinoAcessoLiberado, OUTPUT);
  pinMode(pinoAcessoNegado, OUTPUT);
  digitalWrite(pinoAcessoLiberado, LOW);
  digitalWrite(pinoAcessoNegado, LOW);
  
  Serial.begin(115200); // Para você ver os logs no Monitor Serial
  
  setup_wifi();
  
  client.setServer(mqtt_server, 1883); // Aponta para a porta do Docker
  client.setCallback(callback); // Avisa qual função roda quando chegar mensagem
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Mantém a conexão viva
}