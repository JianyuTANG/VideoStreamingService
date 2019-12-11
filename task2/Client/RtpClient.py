from tkinter import *
from tkinter import messagebox as tkMessageBox
from PIL import Image, ImageTk
from RtpPacket import RtpPacket
import socket
import time
import threading
import numpy as np
from cv2 import *
from SubtitleLoader import SubtitleLoader


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

    def __init__(self, master, serverIP, serverPort, rtpPort, videoname, rtspsock, **kw):
        super().__init__(master, **kw)
        self.state = RtpClient.INIT
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (serverIP, serverPort)
        self.rtpPort = rtpPort
        self.rtspSocket = rtspsock
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # try:
        #     self.rtspSocket.connect(self.serverAddr)
        #     threading.Thread(target=self.recvRtspReply).start()
        # except:
        #     raise IOError


        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.screen_width = master.winfo_screenwidth()
        print(self.screen_width)
        self.screen_height = master.winfo_screenheight()
        print(self.screen_height)

        self.rtspSeq = 0
        self.fileName = videoname
        self.sessionId = 0
        self.teardownAcked = 0
        self.currentSec = IntVar()
        self.currentSec.set(0)
        self.isFullScreen = False

        threading.Thread(target=self.recvRtspReply).start()
        self.setupMovie()

        self.master.bind('<space>', func=self.processBlank)

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        # self.setup = Button(self.master, width=20, padx=3, pady=3)
        # self.setup["text"] = "Setup"
        # self.setup["command"] = self.setupMovie
        # self.setup.grid(row=2, column=0, padx=2, pady=2)

        # Create Play button
        self.playimg = Image.open('res/play.png')
        self.playimg = self.playimg.resize((20, 20), Image.ANTIALIAS)
        self.playimg = ImageTk.PhotoImage(self.playimg)
        self.pauseimg = Image.open('res/pause.png')
        self.pauseimg = self.pauseimg.resize((20, 20), Image.ANTIALIAS)
        self.pauseimg = ImageTk.PhotoImage(self.pauseimg)
        self.start = Button(self.master, image=self.playimg)
        # self.start["text"] = "Play"
        # self.start.configure(img=self.playimg)
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=0, padx=2, pady=2)

        # Create Pause button
        self.fullimg = Image.open('res/full.png')
        self.fullimg = self.fullimg.resize((20, 20), Image.ANTIALIAS)
        self.fullimg = ImageTk.PhotoImage(self.fullimg)
        self.pause = Button(self.master, image=self.fullimg)
        self.pause["command"] = self.enter_full_screen
        self.pause.grid(row=2, column=1, padx=2, pady=2)

        # Create Teardown button
        # self.teardown = Button(self.master, width=20, padx=3, pady=3)
        # self.teardown["text"] = "Teardown"
        # self.teardown["command"] = self.exitClient
        # self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        # self.label = Label(self.master, height=19)
        # self.label.grid(row=0, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

        # create a scale
        # self.progress = Scale(self.master, from_=0, to=100, orient=HORIZONTAL)
        # self.progress.grid(row=1, column=0, columnspan=4, sticky=W + E + N + S, padx=5, pady=5)

        self.x1 = Button(self.master, width=7, padx=3, pady=3)
        self.x1["text"] = "x1"
        self.x1["command"] = self.setDuration1
        self.x1.grid(row=2, column=2, padx=2, pady=2)

        self.x15 = Button(self.master, width=7, padx=3, pady=3)
        self.x15["text"] = "x1.5"
        self.x15["command"] = self.setDuration15
        self.x15.grid(row=2, column=3, padx=2, pady=2)

        self.x05 = Button(self.master, width=7, padx=3, pady=3)
        self.x05["text"] = "x0.5"
        self.x05["command"] = self.setDuration05
        self.x05.grid(row=2, column=4, padx=2, pady=2)

    def setupMovie(self):
        self.state = RtpClient.INIT
        # clear
        movieName = self.fileName
        self.rtspSeq += 1
        # Write the RTSP request to be sent.
        request = 'SETUP ' + movieName + ' RTSP/1.0\nCSeq: ' + str(
            self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
        # print(request)
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
        # print(request)
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
        # print(request)
        threading.Thread(target=self.listenRtp).start()
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
        print(request)
        if self.state == RtpClient.PLAYING:
            # self.state = RtpClient.READY
            self.playEvent.set()
            print('暂停播放 reposition')
        return True

    def exitClient(self):
        """Teardown button handler."""
        if self.state == RtpClient.INIT:
            self.teardownAcked = 1
            self.master.destroy()  # Close the gui window
            return
        if self.state == RtpClient.PLAYING:
            self.playEvent.set()
            time.sleep(0.2)
        self.rtspSeq += 1
        request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
            self.sessionId)

        try:
            self.rtspSocket.sendall(request.encode())
        except:
            tkMessageBox.showwarning('Sending Failed', 'Fail to send rtsp message')
            return False

        # cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        # if os.path.isfile(cachename):
        #     os.remove(cachename)
        self.requestSent = RtpClient.TEARDOWN
        return True

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            if self.teardownAcked == 1:
                return
            try:
                reply = self.rtspSocket.recv(1024)
            except:
                print('connection broke')
                return

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

    def printscale(self, sec):
        print(sec)

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
                        try:
                            self.rtpSocket.bind(('', self.rtpPort))
                        except:
                            tkMessageBox.showwarning('Binding Failed', 'Fail to bind RTP socket')
                            return
                        length = int(float(lines[3].split()[1]))
                        fps = int(float(lines[4].split()[1]))
                        height = int(float(lines[5].split()[1]))
                        width = int(float(lines[6].split()[1]))
                        self.length = length
                        self.fps = fps
                        self.actualfps = fps
                        self.height = height
                        self.width = width
                        self.frameNum = int(float(lines[7].split()[1]))
                        framenum = self.frameNum
                        print('height ' + str(self.height))
                        print('width ' + str(self.width))
                        print('framenum: ' + str(framenum))
                        print('fps: ' + str(fps))
                        print('len: ' + str(length))
                        self.buffer = [None for i in range(framenum + 100)]
                        self.fullScreenBuffer = [None for i in range(framenum + 100)]
                        self.duration = 1 / fps
                        self.state = RtpClient.READY
                        self.frameSeq = 0
                        self.progress = Scale(self.master, from_=0, to=length, orient=HORIZONTAL,
                                              variable=self.currentSec,
                                              command=self.process_reposition)
                        self.progress.grid(row=1, column=0, columnspan=5,
                                           sticky=W + E + N + S, padx=5, pady=5)
                        self.canvas = Canvas(self.master, width=width, height=height)
                        self.canvas.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)
                        self.loadingimg = Image.open('res/loading.png')
                        self.loadingimg = ImageTk.PhotoImage(self.loadingimg)
                        self.image_on_canvas = self.canvas.create_image(0, 0,
                                                                        anchor=NW, image=self.loadingimg)
                        try:
                            srtname = self.fileName.split('.')[0]
                            srtname += '.srt'
                            srtname = os.path.join('srt/', srtname)
                            self.subtitleLoader = SubtitleLoader(srtName=srtname, length=length)
                            self.hasSub = True
                        except:
                            self.hasSub = False
                        if self.hasSub:
                            self.subtitle = Label(self.canvas)
                            # self.subtitle.place(x=width / 2, y=height - 15, anchor=CENTER)

                    elif self.requestSent == RtpClient.PLAY:
                        self.state = RtpClient.PLAYING
                        self.playEvent = threading.Event()
                        threading.Thread(target=self.updateFrames).start()
                        self.start['image'] = self.pauseimg
                        self.start['command'] = self.pauseMovie

                    elif self.requestSent == RtpClient.PAUSE:
                        self.state = RtpClient.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                        self.start['image'] = self.playimg
                        self.start['command'] = self.playMovie

                    elif self.requestSent == RtpClient.REPOSITION:
                        self.frameSeq = int(lines[3].split()[1])
                        print('receive reposition')
                        # print('after repositioning: ' + str(self.frameSeq))
                        if self.state == RtpClient.PLAYING:
                            time.sleep(0.2)
                            self.playEvent = threading.Event()
                            threading.Thread(target=self.updateFrames).start()

                    elif self.requestSent == RtpClient.TEARDOWN:
                        self.master.destroy()  # Close the gui window
                        self.state = RtpClient.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                        self.buffer = None
                        self.fullScreenBuffer = None
                        self.rtpSocket.shutdown(socket.SHUT_RDWR)
                        self.rtpSocket.close()

    def listenRtp(self):
        """Listen for RTP packets."""
        print('start listen')
        while True:
            try:
                data = self.rtpSocket.recvfrom(62040)[0]
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()

                    if self.buffer[currFrameNbr] is None:
                        # print(currFrameNbr)
                        data = rtpPacket.getPayload()
                        # img = Image.open(BytesIO(data))
                        # photo = ImageTk.PhotoImage(img)

                        img = np.fromstring(data, np.uint8)
                        img = imdecode(img, IMREAD_COLOR)
                        img = img[:, :, ::-1]
                        img = Image.fromarray(img)
                        # if self.isFullScreen:
                        #     img.resize((self.screen_height, self.screen_width), Image.ANTIALIAS)
                        photo = ImageTk.PhotoImage(img)
                        self.buffer[currFrameNbr] = photo
                        threading.Thread(target=self._process_frame, args=(img, currFrameNbr,)).start()
                    if currFrameNbr == self.frameNum:
                        return

            except:
                print('except')
                break
                # if self.teardownAcked == 1:
                #     break
                #
                # if self.playEvent.isSet():
                #     break

    def _process_frame(self, img, currFrameNbr):
        try:
            photo = img.resize((self.screen_width, self.screen_height), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(photo)
            self.fullScreenBuffer[currFrameNbr] = photo
        except:
            return

    def updateFrames(self):
        print('enter updateFrames')

        time.sleep(1)
        while True:
            if self.playEvent.isSet() or self.teardownAcked == 1:
                print('break')
                break
            if self.isFullScreen:
                # print('full screen')
                photo = self.fullScreenBuffer[self.frameSeq]
            else:
                photo = self.buffer[self.frameSeq]
            if photo is not None:
                # self.label.configure(image=photo, height=self.height)
                # self.label.image = photo
                self.canvas.itemconfig(self.image_on_canvas, image=photo)
                self.buffer[self.frameSeq - 1] = None
                self.fullScreenBuffer[self.frameSeq - 1] = None
                self.frameSeq += 1
            else:
                print('lack ' + str(self.frameSeq))
                self.frameSeq += 1
            if self.frameSeq % self.actualfps == 0:
                sec = self.currentSec.get() + 1
                self.currentSec.set(sec)
                if self.hasSub:
                    c = self.subtitleLoader.getsub(sec)
                    print(type(c))
                    if c is None:
                        self.subtitle['text'] = ''
                        self.subtitle.place_forget()
                    elif isinstance(c, str):
                        width = int(self.canvas['width'])
                        height = int(self.canvas['height'])
                        self.subtitle.place(x=width / 2, y=height - 15, anchor=CENTER)
                        self.subtitle['text'] = c
                        print(c)
                    else:
                        width = int(self.canvas['width'])
                        height = int(self.canvas['height'])
                        self.subtitle.place(x=width / 2, y=height - 15, anchor=CENTER)
            if self.frameSeq == self.frameNum:
                self.state = RtpClient.READY
                return
            time.sleep(self.duration)


    def handler(self):
        """Handler on explicitly closing the GUI window."""
        state = self.state
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            if state == RtpClient.PLAYING:
                self.playMovie()

    def process_reposition(self, sec):
        # print(self.currentSec.get())
        threading.Thread(target=self._process_reposition, args=(sec,)).start()

    def _process_reposition(self, sec):
        time.sleep(0.1)
        sec = int(sec)
        if sec != self.currentSec.get():
            return
        self.repositionMovie(sec)

    def setDuration1(self):
        self.setDuration(1)

    def setDuration15(self):
        self.setDuration(1.5)

    def setDuration05(self):
        self.setDuration(0.5)

    def setDuration(self, mul):
        newdur = 1 / (mul * self.fps)
        newfps = mul * self.fps
        if self.state == RtpClient.INIT:
            return
        elif self.actualfps == newfps:
            return
        elif self.state == RtpClient.READY:
            self.duration = newdur
            self.actualfps = newfps
        elif self.state == RtpClient.PLAYING:
            self.playEvent.set()
            time.sleep(0.4)
            self.duration = newdur
            self.actualfps = newfps
            self.playEvent = threading.Event()
            threading.Thread(target=self.updateFrames).start()

    def enter_full_screen(self):
        if self.state == RtpClient.INIT:
            return
        self.isFullScreen = True
        self.master.bind('<Escape>', func=self.processESC)
        self.hideWidgets()
        self.master.attributes("-fullscreen", True)
        self.canvas.config(width=self.screen_width, height=self.screen_height)

        try:
            if self.state == RtpClient.READY:
                if self.fullScreenBuffer[self.frameSeq] is not None:
                    photo = self.fullScreenBuffer[self.frameSeq]
                    self.canvas.itemconfig(self.image_on_canvas, image=photo)
        except:
            return

    def quit_full_screen(self):
        if not self.isFullScreen:
            return
        self.master.unbind('<Escape>')
        self.master.attributes("-fullscreen", False)
        self.showWidgets()
        self.isFullScreen = False
        self.canvas.config(width=self.width, height=self.height)

        try:
            if self.state == RtpClient.READY:
                if self.buffer[self.frameSeq] is not None:
                    photo = self.buffer[self.frameSeq]
                    self.canvas.itemconfig(self.image_on_canvas, image=photo)
        except:
            return

    def processBlank(self, ke):
        if self.state == RtpClient.INIT:
            return
        if self.state == RtpClient.PLAYING:
            self.pauseMovie()
        else:
            self.playMovie()

    def processESC(self, ke):
        if not self.isFullScreen:
            return
        self.quit_full_screen()

    def hideWidgets(self):
        self.start.grid_forget()
        self.pause.grid_forget()
        self.x1.grid_forget()
        self.x05.grid_forget()
        self.x15.grid_forget()
        self.progress.grid_forget()

    def showWidgets(self):
        self.start.grid(row=2, column=0, padx=2, pady=2)
        self.pause.grid(row=2, column=1, padx=2, pady=2)
        self.progress.grid(row=1, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)
        self.x1.grid(row=2, column=2, padx=2, pady=2)
        self.x15.grid(row=2, column=3, padx=2, pady=2)
        self.x05.grid(row=2, column=4, padx=2, pady=2)


# root = Tk()
# c = RtpClient(root, '127.0.0.1', 6666, 5555)
# c.mainloop()
