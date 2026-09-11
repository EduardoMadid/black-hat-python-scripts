# Cliente UDP basico (Black Hat Python).
# Diferenca chave para o TCP: UDP nao tem handshake nem garantia de entrega,
# por isso nao existe connect() de fato (so associa o destino) e usamos
# sendto()/recvfrom() em vez de send()/recv().
# Uso: python3 ClienteUDP.py (aponte target_host/target_port para um servidor UDP)
import socket

target_host = "127.0.0.1"
target_port = 9997

# SOCK_DGRAM = UDP (sem conexao, sem garantia de entrega/ordem)
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# sendto precisa do endereco de destino a cada envio (nao ha "conexao" fixa)
client.sendto(b"Hello UDP Server", (target_host, target_port))

# recvfrom retorna os dados E o endereco de quem respondeu
data, addr = client.recvfrom(4096)

# imprime a resposta e fecha a conexao do cliente
print(data.decode())
client.close()

