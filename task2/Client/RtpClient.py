from RtpPacket import RtpPacket
import socket


class RtpClient:
    INIT = 0
    READY = 1
    PLAYING = 2

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIBE = 4
    REPOSITION = 5

    def __init__(self, serverIP, serverPort, rtpPort):
        self.state = RtpClient.INIT
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (serverIP, serverPort)
        self.rtpPort = rtpPort
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.rtspSocket.connect(self.serverAddr)
        except:
            raise IOError

        self.rtspSeq = 0
        self.requestSent = []

    def setupMovie(self, movieName):
        self.state = RtpClient.INIT
        # clear
        # Write the RTSP request to be sent.
        request = 'SETUP ' + movieName + ' RTSP/1.0\nCSeq: ' + str(
            self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            return False

        # Keep track of the sent request.
        self.fileName = movieName
        self.requestSent[self.rtspSeq] = self.SETUP
        self.rtspSeq += 1
        return True

    def decribeMovie(self):
        if self.state != RtpClient.INIT:
            return False

        request = 'DESCRIPTION ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            return False

        self.requestSent[self.rtspSeq] = self.DESCRIPTION
        self.rtspSeq += 1
        return True

    def playMovie(self):
        if self.state != RtpClient.READY:
            return False

        request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            return False

        self.requestSent[self.rtspSeq] = self.PLAY
        self.rtspSeq += 1
        return True

    def pauseMovie(self):
        if self.state != RtpClient.PLAYING:
            return False

        request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            return False

        self.requestSent[self.rtspSeq] = self.PAUSE
        self.rtspSeq += 1
        return True

    def repositionMovie(self, sec):
        if self.state == RtpClient.INIT:
            return False

        request = 'REPOSITION ' + str(sec) + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            return False

        self.requestSent[self.rtspSeq] = self.REPOSITION
        self.rtspSeq += 1
        return True

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # Update RTSP state.
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
