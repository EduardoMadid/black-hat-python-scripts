# Cliente SSH que executa UM comando remoto e imprime a saida, usando a
# biblioteca paramiko (requer: pip install paramiko).
# Uso: python3 ssh_cmd.py  (pede usuario/senha/IP/porta/comando interativamente,
# com valores padrao entre parenteses se voce so der <ENTER>)
import paramiko

def ssh_command(ip, port, user, passwd, cmd):
    client = paramiko.SSHClient()
    # ATENCAO: AutoAddPolicy aceita qualquer host key sem confirmar --
    # conveniente para labs/pentest, mas vulneravel a MITM em producao.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Ensure port is an integer
    client.connect(ip, port=int(port), username=user, password=passwd)

    # exec_command roda o comando em um canal separado e devolve
    # (stdin, stdout, stderr); aqui juntamos saida normal e de erro
    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()

    if output:
        print("--- Saida ---")
        for line in output:
            print(line.strip())

if __name__ == '__main__':
    import getpass
    user = input("Username: ")
    password = getpass.getpass()  # nao ecoa a senha no terminal

    ip = input("Insira o IP do servidor: ") or '192.168.1.203'
    port = input("Insira a porta ou <CR>: ") or 2222
    cmd = input("Insira o comando ou <CR>: ") or 'id'

    ssh_command(ip, port, user, password, cmd)