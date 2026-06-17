import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

void main() {
  runApp(const SmartLockApp());
}

class SmartLockApp extends StatelessWidget {
  const SmartLockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartLock Admin',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF121212),
        primaryColor: const Color(0xFF1E1E2C),
        appBarTheme: const AppBarTheme(backgroundColor: Color(0xFF1A1A2E), elevation: 0),
        cardColor: const Color(0xFF252538),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Color(0xFF1A1A2E),
          selectedItemColor: Colors.green,
          unselectedItemColor: Colors.grey,
        )
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _indiceAbaAtual = 0; // Controla qual tela está aparecendo
  
  List<Map<String, dynamic>> cadastrosPendentes = [];
  List<Map<String, dynamic>> usuariosCadastrados = [];
  
  MqttServerClient? client;
  bool isConnected = false;

  @override
  void initState() {
    super.initState();
    conectarMQTT();
  }

  Future<void> conectarMQTT() async {
    client = MqttServerClient('coloque o IP aqui', 'AppAdminFlutter');
    client!.port = 1883;
    client!.logging(on: false);
    client!.keepAlivePeriod = 20;

    final connMess = MqttConnectMessage()
        .withClientIdentifier('AppAdmin_${DateTime.now().millisecondsSinceEpoch}')
        .startClean();
    client!.connectionMessage = connMess;

    try {
      await client!.connect();
    } catch (e) {
      client!.disconnect();
    }

    if (client!.connectionStatus!.state == MqttConnectionState.connected) {
      setState(() => isConnected = true);

      // Inscreve nos dois canais
      client!.subscribe('smartlock/pendentes', MqttQos.atLeastOnce);
      client!.subscribe('smartlock/lista_usuarios', MqttQos.atLeastOnce);

      // Pede pro Python mandar a lista de usuários logo que conecta
      _solicitarListaUsuarios();

      client!.updates!.listen((List<MqttReceivedMessage<MqttMessage?>>? c) {
        final topic = c![0].topic;
        final recMess = c[0].payload as MqttPublishMessage;
        final payloadText = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);

        try {
          final data = jsonDecode(payloadText);
          
          setState(() {
            // Se chegou um pedido de cadastro novo
            if (topic == 'smartlock/pendentes') {
              cadastrosPendentes.insert(0, {
                "id": data["id"],
                "nome": data["nome"],
                "data": data["data"],
                "fotoBase64": data["foto"]
              });
            } 
            // Se chegou a lista completa de usuários do banco de dados
            else if (topic == 'smartlock/lista_usuarios') {
              usuariosCadastrados = List<Map<String, dynamic>>.from(data);
            }
          });
        } catch (e) {
          print("🚨 Erro JSON: $e");
        }
      });
    } else {
      setState(() => isConnected = false);
    }
  }

  // Manda uma mensagem pro Python: "Ei, me manda a lista de quem já tem acesso!"
  void _solicitarListaUsuarios() {
    if (client != null && isConnected) {
      final builder = MqttClientPayloadBuilder();
      builder.addString('{"comando": "listar"}');
      client!.publishMessage('smartlock/pedir_usuarios', MqttQos.atLeastOnce, builder.payload!);
    }
  }

  void responderCadastro(String id, bool aprovado, String nome) {
    if (client != null && isConnected) {
      final builder = MqttClientPayloadBuilder();
      final resposta = jsonEncode({"id": id, "nome": nome, "aprovado": aprovado});
      builder.addString(resposta);
      client!.publishMessage('smartlock/respostas', MqttQos.exactlyOnce, builder.payload!);

      setState(() {
        cadastrosPendentes.removeWhere((element) => element["id"] == id);
      });
    }
  }

  Widget _construirAvatar(String? base64String, double tamanho) {
    if (base64String == null || base64String.isEmpty) {
      return Icon(Icons.person, size: tamanho * 0.6, color: Colors.grey);
    }
    try {
      Uint8List bytesImagem = base64Decode(base64String);
      return ClipOval(
        child: Image.memory(bytesImagem, width: tamanho, height: tamanho, fit: BoxFit.cover),
      );
    } catch (e) {
      return Icon(Icons.broken_image, size: tamanho * 0.6, color: Colors.red);
    }
  }

  // TELA 1: Pendentes
  Widget _buildTelaPendentes() {
    if (cadastrosPendentes.isEmpty) {
      return const Center(child: Text("Nenhum cadastro pendente 😴", style: TextStyle(color: Colors.grey)));
    }
    return ListView.builder(
      itemCount: cadastrosPendentes.length,
      itemBuilder: (context, index) {
        final pessoa = cadastrosPendentes[index];
        return Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Row(
                  children: [
                    Container(
                      width: 60, height: 60,
                      decoration: BoxDecoration(color: Colors.grey[800], shape: BoxShape.circle),
                      child: _construirAvatar(pessoa["fotoBase64"], 60),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(pessoa["nome"], style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 4),
                          Text(pessoa["data"], style: const TextStyle(fontSize: 12, color: Colors.grey)),
                          const SizedBox(height: 4),
                          const Text("Solicitando Cadastro", style: TextStyle(fontSize: 12, color: Colors.orange)),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    OutlinedButton.icon(
                      onPressed: () => responderCadastro(pessoa["id"], false, pessoa["nome"]),
                      icon: const Icon(Icons.close, color: Colors.redAccent),
                      label: const Text("Negar", style: TextStyle(color: Colors.redAccent)),
                      style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.redAccent)),
                    ),
                    ElevatedButton.icon(
                      onPressed: () => responderCadastro(pessoa["id"], true, pessoa["nome"]),
                      icon: const Icon(Icons.check, color: Colors.white),
                      label: const Text("Aprovar"),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                    ),
                  ],
                )
              ],
            ),
          ),
        );
      },
    );
  }

  // TELA 2: Usuários Cadastrados (A Galeria)
  // TELA 2: Usuários Cadastrados (A Galeria)
  Widget _buildTelaUsuarios() {
    if (usuariosCadastrados.isEmpty) {
      return const Center(child: Text("Ninguém cadastrado no sistema ainda.", style: TextStyle(color: Colors.grey)));
    }
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2, 
        childAspectRatio: 0.75, // Ajustado levemente para caber o novo texto da data
        crossAxisSpacing: 10,
        mainAxisSpacing: 10,
      ),
      itemCount: usuariosCadastrados.length,
      itemBuilder: (context, index) {
        final usuario = usuariosCadastrados[index];
        // Pega a data que veio do Python, ou coloca um texto padrão se vier vazio
        final dataCadastro = usuario["data_cadastro"] ?? "Data desconhecida";

        return Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 70, height: 70,
                decoration: BoxDecoration(color: Colors.grey[800], shape: BoxShape.circle),
                child: _construirAvatar(usuario["foto"], 70),
              ),
              const SizedBox(height: 12),
              Text(
                usuario["nome"], 
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              const Text("Autorizado", style: TextStyle(color: Colors.green, fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              // Aqui entra a nova informação da data e hora!
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.access_time, size: 12, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    dataCadastro, 
                    style: const TextStyle(color: Colors.grey, fontSize: 10)
                  ),
                ],
              )
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_indiceAbaAtual == 0 ? 'Aprovações' : 'Banco de Rostos', style: const TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          Icon(Icons.cloud_done, color: isConnected ? Colors.green : Colors.red),
          const SizedBox(width: 16),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: _indiceAbaAtual == 0 ? _buildTelaPendentes() : _buildTelaUsuarios(),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceAbaAtual,
        onTap: (index) {
          setState(() => _indiceAbaAtual = index);
          if (index == 1) {
            _solicitarListaUsuarios(); // Atualiza a galeria ao clicar nela
          }
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.notifications_active), label: "Pendentes"),
          BottomNavigationBarItem(icon: Icon(Icons.people), label: "Usuários"),
        ],
      ),
    );
  }
}