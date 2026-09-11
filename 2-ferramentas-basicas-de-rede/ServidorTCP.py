# Servidor TCP multi-thread basico (Black Hat Python).
# Uso: python3 ServidorTCP.py
# Depois conecte com ClienteTCP.py (ajustando a porta para 9998) ou com
# netcat: nc 127.0.0.1 9998
import socket
import threading

IP = '0.0.0.0'  # escuta em todas as interfaces de rede da maquina
PORT = 9998

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen(5)  # tamanho da fila de conexoes pendentes (backlog)
    print(f"[*] Listening on {IP}:{PORT}")

    while True:
        # accept() bloqueia ate chegar uma conexao nova
        client, address = server.accept()
        print(f"[*] Accepted connection from {address[0]}:{address[1]}")
        # cada cliente e atendido em sua propria thread, permitindo
        # multiplas conexoes simultaneas sem travar o loop principal
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

def handle_client(client_socket):
    # "with" garante que o socket sera fechado (close()) mesmo se der erro
    with client_socket as sock:
        request = sock.recv(1024)
        print(f"[*] Received: {request.decode('utf-8')}")
        sock.send(b"Mensagem do Servidor")

if __name__ == "__main__":
    main()