import socket
import threading
import time


class GBNSender:
    N = 8
    timeout = 5
    HEADER_SIZE = 4

    def __init__(self, targetIP, targetPort, listenPort):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind(('', listenPort))
        except:
            raise ConnectionError
        self.target = (targetIP, targetPort)
        self.listenPort = listenPort

        self.base = 0
        self.nextSeqNum = 0
        self.sndPkt = [b'' for i in range(GBNSender.N)]

        self.recvThread = threading.Thread(target=self._rdt_recv)
        self.recvThread.start()
        self.recvThreadFlag = threading.Event()

    def send(self, data):
        if self.nextSeqNum < self.base + GBNSender.N:
            pkt = self._make_pkt(data, self.nextSeqNum)
            self.sndPkt[(self.nextSeqNum - self.base) % GBNSender.N] = pkt
            self.sock.sendto(pkt, self.target)
            if self.base == self.nextSeqNum:
                self._start_timer()
            self.nextSeqNum += 1
            return True
        else:
            return False

    def clear(self):
        self.recvThreadFlag.set()
        self.sock.close()
        self.sndPkt = []

    def _make_pkt(self, data, seq):
        header = bytearray(seq.to_bytes(4))
        pkt = header + data
        return pkt

    def _resend_all(self):
        nsn = (self.nextSeqNum - self.base) % GBNSender.N
        for i in range(nsn):
            data = self.sndPkt[i]
            self.sock.sendto(data, self.target)
        threading.Thread(target=self._restart_timer).start()

    def _restart_timer(self):
        time.sleep(0.1)
        self._start_timer()

    def _rdt_recv(self):
        while True:
            if self.recvThreadFlag.isSet():
                break

            data, _ = self.sock.recvfrom(1024)
            try:
                data = data.decode().split()
                if data[0] == 'ACK':
                    seq = data[1]
                    seq = int(seq) + 1
                    delta = seq - self.base
                    if delta > 0:
                        self.sndPkt = self.sndPkt[delta:] + [b'' for i in range(delta)]
                    self.base = seq
                    if self.base == self.nextSeqNum:
                        self._stop_timer()
                    else:
                        self._start_timer()
                else:
                    continue

            except:
                continue

    def _start_timer(self):
        self.timer = threading.Timer(GBNSender.timeout, self._resend_all)
        self.timer.start()

    def _stop_timer(self):
        self.timer.cancel()
