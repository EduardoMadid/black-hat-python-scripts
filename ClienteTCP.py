# Cliente TCP basico (Black Hat Python).
# Uso: ajuste target_host/target_port para apontar para um servidor TCP
# (ex.: ServidorTCP.py rodando na mesma maquina/rede) e execute:
#   python3 ClienteTCP.py
import socket

target_host = "0.0.0.0"
target_port = 9998

# AF_INET = IPv4, SOCK_STREAM = TCP (orientado a conexao, com garantia de entrega)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# three-way handshake do TCP acontece aqui
client.connect((target_host, target_port))

# envia bytes (por isso o prefixo b"..."); strings precisam ser codificadas antes
client.send(b"MEnsagem sendo enviada do cliente")

# recv(4096) le ate 4096 bytes do buffer do socket (pode vir menos que isso)
response = client.recv(4096)

# decode() converte bytes -> str (usa utf-8 por padrao)
print(response.decode())
# libera os recursos do socket; sempre feche para evitar conexoes penduradas
client.close()