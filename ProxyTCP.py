# Proxy TCP de interceptacao (Black Hat Python) - fica entre um cliente e um
# servidor remoto, mostrando um hexdump de tudo que trafega e permitindo
# alterar requisicoes/respostas em request_handler()/response_handler().
# Util para analisar protocolos desconhecidos ou testar apps proprias.
#
# Uso: ./ProxyTCP.py [localhost] [localport] [remotehost] [remoteport] [receive_first]
# Exemplo: ./ProxyTCP.py 127.0.0.1 9000 10.12.132.1 9000 True
#   - receive_first=True quando o servidor remoto fala primeiro (ex.: banners
#     de FTP/SSH); False quando o cliente inicia a conversa (ex.: HTTP).
import sys
import socket
import threading


# tabela de traducao: mantem caracteres ASCII imprimiveis e troca o resto
# por "." -- usada pelo hexdump() para montar a coluna de texto
HEX_FILTER = ''.join(
    [(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)]
)


# Funcao do hexdump
def hexdump(src, length=16, show=True):
    '''
    Recebe algum input como bytes ou uma string e imprime um hexdump no console.
    Ou seja, ele retorna os detalhes do pacote com seus valores hexadecimais e caracteres
    ASCII imprimiveis.
    É uma função simples e util para entender protocolos desconhecidos,
    encontrar creds de usuarios em plain text, etc.
    '''

    # Certificamos de ter uma string, decodificando os bytes caso uma string de bytes tenha
    # sido passada
    if isinstance(src, bytes):
        src = src.decode()
    
    results = list()
    for i in range(0, len(src), length):
        word = str(src[i:i+length]) # Pegamos um pedaco da string para despejar e a colocamos na variavel word


        printable = word.translate(HEX_FILTER) # Utilizamos a funcao nativa translate para substituir a representacao da string de cada caractere pelo caractere correspondente na string bruta (imprimivel)
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexwidth = length*3
        results.append(f'{i:04x}  {hexa:<{hexwidth}} {printable}') # Substituimos a representacao hexadecimal do valor inteiro de cada caractere na string bruta (hexa). Por fim, criamos um novo array para armazenar as strings, result, que contem o valor hexadecimal da palavra e a sua representacao imprimivel
    if show:
        for line in results:
            print(line)
    else:
        return results


def receive_from(connection):
    '''
    Para receber dados tanto local quanto remotamente, passamos o objeto socket a ser utilizado. Criamos uma string de bytes vazia, buffer, que acumulura as respostas do socket. Por padrao configuramos um tempo limite de 5 segundos, oq pode ser agressivo se estviermos roteando o trafego para outros paises ou por redes com perda, entao fique a vontade para aumentar o tempo limite.
    '''
    buffer = b""
    connection.settimeout(5) # tempo limite de 5 segundos
    try:
        while True:
            data = connection.recv(4096) # loop para ler os dados de resposta do buffer
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer


def request_handler(buffer):
    # Realizar modificacoes no pacote
    # Verifica se o cliente está usando o curl
    if b"User-Agent: curl" in buffer:
        print("\n[*] Identidade exposta detectada! Mascarando para Firefox...")
        # Substitui o "curl" por uma string que simula um navegador real
        buffer = buffer.replace(b"User-Agent: curl", b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64)")
    
    return buffer


def response_handler(buffer):
    # Realizar modificacoes no pacote
    # Verifica se a palavra NeverSSL está no pacote
    if b"NeverSSL" in buffer:
        print("[*] Alvo detectado! Injetando HTML modificado...")
        # Substitui "NeverSSL" (8 letras) por "Eduardo!" (8 letras)
        buffer = buffer.replace(b"NeverSSL", b"Eduardo!")
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)
    
        remote_buffer = response_handler(remote_buffer)
        if len(remote_buffer):
            print("[<==] Enviando %d bytes para o localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)

    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            line = "[==>] Recebido %d bytes do localhost." % len(local_buffer)
            print(line)
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Enviado para o servidor remoto.")
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Recebido %d bytes do servidor remoto." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Enviado para o localhost.")
        
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] Nao ha mais dados. Fechando as conexoes!")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print('Problema ao conectar: %r' % e)
        print("[!!] Falha ao ouvir em %s:%d" % (local_host, local_port))
        print("[!!] Verifique outros sockets de escuta ou corrija as permissões.")
        sys.exit(0)
    
    print("[*] Ouvindo em %s:%d" % (local_host, local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # imprimir as informacoes da conexao local
        line = '> Conexao de entrada recebida de %s:%d' % (addr[0], addr[1])
        print(line)
        # iniciar  uma thread para se comunicar com o host remoto
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )
        proxy_thread.start()


def main():
    if len(sys.argv[1:]) != 5:
        print("Uso: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Exemplo: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    
    try:
        server_loop(local_host, local_port, remote_host, remote_port, receive_first)
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C detectado. Encerrando o proxy. Falou, Eduardo!")
        sys.exit(0)

if __name__ == '__main__':
    main()
