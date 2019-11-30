import socket
import threading
from RtpPacket import RtpPacket
import random
import os
import glob


class Server:
    def __init__(self, rtspSocket):
        self.INIT = 0
        self.READY = 1
        self.PLAYING = 2
        self.state = self.INIT

        self.SETUP = 'SETUP'
        self.PLAY = 'PLAY'
        self.PAUSE = 'PAUSE'
        self.TEARDOWN = 'TEARDOWN'
        self.rtspSocket = rtspSocket[0]
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clientIp = rtspSocket[1][0]
        self.clientRtpPort = 0
        self.session = ''
        self.rtpFlag = threading.Event()
        self.frameSeq = 0
        threading.Thread(target=self.recvRtspRequest).start()

    def recvRtspRequest(self):
        '''
        receive RTSP request from client
        '''
        while True:
            data = self.rtspSocket.recv(1024).decode()
            if data:
                self.parseRtspRequest(data)

    def parseRtspRequest(self, data):
        '''
        parse and process RTSP requests from client
        '''
        lines = data.split('\n')
        for i, line in enumerate(lines):
            lines[i] = line.split(' ')
        rtspType = lines[0][0]
        print(rtspType)
        seqNum = lines[1][1]
        print(seqNum)

        if rtspType == self.SETUP and self.state == self.INIT:
            # deal with the video
            folderName = lines[0][1]
            if not os.path.isdir(folderName):
                return
            self.imgList = glob.glob(os.path.join(folderName, '*.jpg'))
            self.imgList.sort()
            self.frameSeq = 0
            self.state = self.READY
            session = random.randint(100000, 999999)
            self.session = str(session)
            self.clientRtpPort = int(lines[2][3])

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            print(reply)
            self.rtspSocket.sendall(reply.encode())

        elif rtspType == self.PLAY and self.state == self.READY:
            self.state = self.PLAYING
            self.rtpFlag.clear()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())
            threading.Thread(target=self.sendRtpPacket).start()

        elif rtspType == self.PAUSE and self.state == self.PLAYING:
            self.state = self.READY
            self.rtpFlag.set()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())

        elif rtspType == self.TEARDOWN:
            self.rtpFlag.set()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())
            self.rtpSocket.close()
            return

        else:
            return

    def sendRtpPacket(self):
        print('start transmitting')
        while True:
            self.rtpFlag.wait(0.05)
            if self.rtpFlag.isSet():
                break

            # read images
            try:
                data = open(self.imgList[self.frameSeq], 'rb')
                data = data.read()
            except:
                break
            if data:
                frameNumber = self.frameSeq
                pack = self.makePacket(data, frameNumber)
                try:
                    self.rtpSocket.sendto(pack, (self.clientIp, self.clientRtpPort))
                    print('pack' + str(self.frameSeq))
                    self.frameSeq += 1
                except:
                    print('error')

    def makePacket(self, payload, frameSeq):
        version = 2
        padding = 0
        extension = 0
        CC = 0
        marker = 0
        PT = 26
        seqNum = frameSeq
        SSRC = 0

        # Create and encode the RTP packet
        # ...
        rtpPacket = RtpPacket()
        rtpPacket.encode(version, padding, extension, CC, seqNum, marker, PT, SSRC, payload)

        # Return the RTP packet
        # ...
        return rtpPacket.getPacket()


def runService(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(1)
    while True:
        rtspSock = sock.accept()
        Server(rtspSocket=rtspSock)


runService(6666)
