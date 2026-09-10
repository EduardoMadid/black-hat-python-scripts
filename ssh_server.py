# Servidor SSH minimo usando paramiko, para uso com ssh_rcmd.py deste repo
# (nao e um sshd de producao). Ele so aceita usuario/senha fixos abaixo --
# troque antes de expor em qualquer rede que nao seja seu lab isolado.
#
# Requer uma chave de host RSA em test_rsa.key (nao versionada no git).
# Para gerar uma nova antes do primeiro uso:
#   ssh-keygen -t rsa -b 2048 -m PEM -f test_rsa.key -N ""
#
# Uso: 1) gere a chave acima; 2) ajuste "server"/ssh_port se necessario;
#      3) python3 ssh_server.py; 4) conecte com ssh_rcmd.py apontando para
#      esse IP/porta usando usuario 'tim' e senha 'sekret'.
import os
import paramiko
import socket
import sys
import threading

CWD = os.path.dirname(os.path.realpath(__file__))

HOSTKEY = paramiko.RSAKey(filename=os.path.join(CWD, 'test_rsa.key'))

class Server (paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        # so permite canais do tipo "session" (execucao de shell/comando)
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # credenciais fixas apenas para fins didaticos/lab -- NUNCA use
        # usuario/senha hardcoded fora de um ambiente de teste controlado
        if (username == 'tim') and (password == 'sekret'):
            return paramiko.AUTH_SUCCESSFUL

if __name__ == '__main__':
    server = '192.168.1.207'  # troque para o IP da interface onde vai escutar
    ssh_port = 2222
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
        sock.bind((server, ssh_port))
        sock.listen(100)
        print('[+] Ouvindo conexões ...')
        client, addr = sock.accept()
    except Exception as e:
        print('[-] Falha na escuta: ' + str(e))
        sys.exit(1)
    else:
        print('[+] Conexão estabelecida!', client, addr)

    bhSession = paramiko.Transport(client)
    bhSession.add_server_key(HOSTKEY)
    server = Server()
    bhSession.start_server(server=server)

    chan = bhSession.accept(20)
    if chan is None:
        print('*** Sem canal')
        sys.exit(1)

    print('[+] Autenticado!')
    print(chan.recv(1024))
    chan.send('BEM VINDO AO BH_SSH')
    try:
        while True:
            command = input("Insira o comando: ")
            if command != 'exit':
                chan.send(command)
                r = chan.recv(8192)
                print(r.decode())
            else:
                chan.send('exit')
                print('exiting')
                bhSession.close()
                break
    except KeyboardInterrupt:
        bhSession.close()