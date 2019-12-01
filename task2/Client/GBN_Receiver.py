import socket


class GBN_Receiver:
    HEADER_SIZE = 4

    def __init__(self, listenPort):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind(('', listenPort))
        except:
            raise ConnectionError
        self.listenPort = listenPort

        self.expectSeq = 0

    def recv(self):
        while True:
            data, addr = self.sock.recvfrom(40960)
            if data:
                self._extract_pkt(data)
                seq = int(self.header)
                if seq == self.expectSeq:
                    ack = 'ACK ' + str(seq)
                    self.sock.sendto(ack.encode(), addr)
                    self.expectSeq += 1
                    return self.payload
                else:
                    ack = 'ACK ' + str(self.expectSeq - 1)
                    self.sock.sendto(ack.encode(), addr)

    def _extract_pkt(self, pkt):
        self.header = bytearray(pkt[:GBN_Receiver.HEADER_SIZE])
        self.payload = pkt[GBN_Receiver.HEADER_SIZE:]
