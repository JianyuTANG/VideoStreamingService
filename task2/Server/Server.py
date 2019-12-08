import socket
import threading
from RtpPacket import RtpPacket
from VideoLoader import VideoLoader
import random
import os
import glob
import argparse


class Server:
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'
    REPOSITION = 'REPOSITION'
    DESCRIPTION = 'DESCRIPTION'

    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self, rtspSocket):
        self.state = Server.INIT

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
                print(data)
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

        if rtspType == Server.SETUP and self.state == Server.INIT:
            # deal with the video
            videoName = lines[0][1]
            try:
                self.videoLoader = VideoLoader(videoName)
            except IOError:
                reply = 'RTSP/1.0 404 FAIL\nCSeq: ' + seqNum + '\nSession: ' + self.session
                self.rtspSocket.sendall(reply.encode())
                print('setup error')
                return

            self.frameSeq = 0
            self.state = self.READY
            session = random.randint(100000, 999999)
            self.session = str(session)
            self.clientRtpPort = int(lines[2][3])

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            print(reply)
            self.rtspSocket.sendall(reply.encode())

        elif rtspType == Server.DESCRIPTION and self.state == Server.READY:
            len = self.videoLoader.getLen()
            fps = self.videoLoader.getFps()
            height = self.videoLoader.getHeight()
            width = self.videoLoader.getWidth()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            reply += '\nLen: ' + str(len) + '\nFps: ' + str(fps)
            reply += '\nheight: ' + str(height) + '\nwidth ' + str(width)
            print(reply)
            self.rtspSocket.sendall(reply.encode())

        elif rtspType == Server.PLAY and self.state == Server.READY:
            self.state = self.PLAYING
            self.rtpFlag.clear()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())
            threading.Thread(target=self.sendRtpPacket).start()

        elif rtspType == Server.PAUSE and self.state == Server.PLAYING:
            self.state = self.READY
            self.rtpFlag.set()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())

        elif rtspType == Server.REPOSITION:
            if self.state == Server.READY or self.state == Server.PLAYING:
                print('start reposition')
                sec = int(lines[0][1])
                if self.state == Server.PLAYING:
                    self.rtpFlag.set()
                if self.videoLoader.reposition(sec):
                    print('reposition success')
                    frameSeq = self.videoLoader.getSeq()
                    reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
                    reply += '\nFrameseq: ' + str(frameSeq + 1)
                else:
                    print('reposition fail')
                    reply = 'RTSP/1.0 404 FAIL\nCSeq: ' + seqNum + '\nSession: ' + self.session
                self.rtspSocket.sendall(reply.encode())
                if self.state == Server.PLAYING:
                    self.rtpFlag = threading.Event()
                    threading.Thread(target=self.sendRtpPacket).start()


        elif rtspType == Server.TEARDOWN:
            self.rtpFlag.set()
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seqNum + '\nSession: ' + self.session
            self.rtspSocket.sendall(reply.encode())

            self.videoLoader = None
            self.state = Server.INIT
            self.rtpFlag = threading.Event()

        else:
            return

    def sendRtpPacket(self):
        print('start transmitting')
        while True:
            self.rtpFlag.wait(0.035)
            if self.rtpFlag.isSet():
                break

            # read images
            data = self.videoLoader.getFrame(10)
            if data is not None:
                frameNumber = self.videoLoader.getSeq()
                pack = self.makePacket(data, frameNumber)
                try:
                    # print((self.clientIp, self.clientRtpPort))
                    self.rtpSocket.sendto(pack, (self.clientIp, self.clientRtpPort))
                    # print('pack ' + str(self.frameSeq))
                    self.frameSeq += 1
                except:
                    print('error')
            else:
                break

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
