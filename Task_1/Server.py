import socket
import threading
from RtpPacket import RtpPacket
import random
from VideoLoader import VideoLoader


class Server:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'

    def __init__(self, rtspPort):
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.bind(('', rtspPort))
        self.clientIp = ''
        self.clientRtpPort = 0
        self.session = ''
        self.rtpThread = None
        self.videoLoader = None
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
        for line in lines:
            line = line.split(' ')
        rtspType = lines[0][0]

        seqNum = lines[1][1]

        if rtspType == self.SETUP and self.state == self.INIT:

            # TODO: deal with the video
            videoName = lines[0][1]
            try:
                self.videoLoader = VideoLoader(videoName)
            except:
                return
            self.state = self.READY
            session = random.randint(100000, 999999)
            self.session = str(session)
            self.clientRtpPort = int(lines[2][3])

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session

        elif rtspType == self.PLAY and self.state == self.READY:
            self.state = self.PLAYING
            # TODO: deal with playing

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session

        elif rtspType == self.PAUSE and self.state == self.PLAYING:
            self.state = self.READY
            # TODO: pause the rtp thread
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session

        elif rtspType == self.TEARDOWN:
            # TODO: stop the rtp thread
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())
            self.rtspSocket.close()
            return

        else:
            return

        self.rtspSocket.sendall(reply.encode())

    def sendRtp(self):
        pass

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
