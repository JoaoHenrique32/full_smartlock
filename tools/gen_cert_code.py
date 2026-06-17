import sys
import os

def pem_to_c_string(file_path, var_name):
    # O encoding='utf-8' previne erros de leitura no Windows
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adiciona a declaração PROGMEM essencial para o ESP8266
    content = content.replace("\\", "\\\\").replace("\n", "\\n\"\n\"")
    return f'const char {var_name}[] PROGMEM =\n"{content}\\n";\n\n'

def main():
    if len(sys.argv) != 4:
        print("Uso: python gen_cert_code.py <ca_cert> <client_crt> <client_key>")
        sys.exit(1)

    ca_file = sys.argv[1]
    crt_file = sys.argv[2]
    key_file = sys.argv[3]

    print("#ifndef SECRETS_H")
    print("#define SECRETS_H\n")
    print("const char* ssid = \"coloque seu SSID aqui\";")
    print("const char* password = \"coloque sua senha aqui\";\n")

    print(pem_to_c_string(ca_file, "ca_cert"))
    print(pem_to_c_string(crt_file, "client_cert"))
    print(pem_to_c_string(key_file, "client_key"))
    
    print("#endif")

if __name__ == "__main__":
    main()