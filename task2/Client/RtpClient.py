from tkinter import *
from tkinter import messagebox as tkMessageBox
from PIL import Image, ImageTk
from RtpPacket import RtpPacket
import socket
import time
import threading
import os


CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class RtpClient(Frame):
    INIT = 0
    READY = 1
    PLAYING = 2

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIPTION = 4
    REPOSITION = 5

    def __init__(self, master, serverIP, serverPort, rtpPort, **kw):
        super().__init__(master, **kw)
        self.state = RtpClient.INIT
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (serverIP, serverPort)
        self.rtpPort = rtpPort
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.rtspSocket.connect(self.serverAddr)
            threading.Thread(target=self.recvRtspReply).start()
        except:
            raise IOError

        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()

        self.rtspSeq = 0
        self.fileName = '1.mp4'
        self.sessionId = 0

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

    def setupMovie(self):
        self.state = RtpClient.INIT
        # clear
        movieName = self.fileName
        self.rtspSeq += 1
        # Write the RTSP request to be sent.
        request = 'SETUP ' + movieName + ' RTSP/1.0\nCSeq: ' + str(
            self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
        print(request)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        # Keep track of the sent request.
        self.requestSent = self.SETUP
        return True

    def decribeMovie(self):
        if self.state != RtpClient.INIT:
            return False

        self.rtspSeq += 1
        request = 'DESCRIPTION ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)
        print(request)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        self.requestSent = RtpClient.DESCRIPTION
        return True

    def playMovie(self):
        if self.state != RtpClient.READY:
            return False

        self.rtspSeq += 1
        request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)
        print(request)
        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        self.requestSent = RtpClient.PLAY
        return True

    def pauseMovie(self):
        if self.state != RtpClient.PLAYING:
            return False

        self.rtspSeq += 1
        request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        self.requestSent = RtpClient.PAUSE
        return True

    def repositionMovie(self, sec):
        if self.state == RtpClient.INIT:
            return False

        self.rtspSeq += 1
        request = 'REPOSITION ' + str(sec) + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        self.requestSent = RtpClient.REPOSITION
        return True

    def exitClient(self):
        """Teardown button handler."""
        self.rtspSeq += 1
        request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False
        self.master.destroy()  # Close the gui window
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        if os.path.isfile(cachename):
            os.remove(cachename)
        self.requestSent = RtpClient.REPOSITION
        return True

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

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
                    if self.requestSent == RtpClient.SETUP:
                        # Update RTSP state.
                        self.frameSeq = 1
                        # Open RTP port.
                        self.decribeMovie()

                    elif self.requestSent == RtpClient.DESCRIPTION:
                        self.state = RtpClient.READY
                        length = int(float(lines[3].split()[1]))
                        fps = int(float(lines[4].split()[1]))
                        self.length = length
                        self.fps = fps
                        framenum = int(length * fps)
                        self.buffer = [None for i in range(framenum + 100)]
                        self.duration = 1 / fps

                    elif self.requestSent == RtpClient.PLAY:
                        self.state = RtpClient.PLAYING
                        self.playEvent = threading.Event()
                        threading.Thread(target=self.listenRtp).start()

                    elif self.requestSent == RtpClient.PAUSE:
                        self.state = RtpClient.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()

                    elif self.requestSent == RtpClient.REPOSITION:
                        self.frameSeq = int(lines[3][1])

                    elif self.requestSent == RtpClient.TEARDOWN:
                        self.state = RtpClient.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

    def listenRtp(self):
        """Listen for RTP packets."""
        print('start listen')
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    if self.buffer[currFrameNbr] is not None:
                        self.buffer[currFrameNbr] = rtpPacket.getPayload()

                    # if currFrameNbr > self.frameNbr:  # Discard the late packet
                    #    self.frameNbr = currFrameNbr
                    #    self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def updateFrames(self):
        while True:
            if self.playEvent.isSet() or self.teardownAcked == 1:
                break

            if self.buffer[self.frameSeq]:
                time.sleep(self.duration)
                cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
                file = open(cachename, "wb")
                file.write(self.buffer[self.frameSeq])
                file.close()
                photo = ImageTk.PhotoImage(Image.open(cachename))
                self.label.configure(image=photo, height=288)
                self.label.image = photo
                self.frameSeq += 1

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()


root = Tk()
c = RtpClient(root, '127.0.0.1', 6666, 5555)
print(666)
c.mainloop()
