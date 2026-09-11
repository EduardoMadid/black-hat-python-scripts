import ipaddress
import struct

class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]

# voce instaciara a classe IP passando o buffer do pacote capturado
# mypacket = IP(buff)
# print(f'{mypacket.src_address} -> {mypacket.dst_address}')

class IP:
    def __init__(self, buff=None):
        header = struct.unpack('<BBHHHBBH4s4s', buff)

        self.ver = header[0] >> 4
        self.ihl = header[0] & 0xF

        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]

        # enderecos IP legiveis
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)

        # mapear constantes de protocolo com seus nomes
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}