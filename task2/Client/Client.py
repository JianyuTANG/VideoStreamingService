from tkinter import *
from tkinter import messagebox as tkMessageBox
from RtpClient import RtpClient
import socket


class Client:
    def __init__(self, master, serverIP, serverPort, rtpPort):
        self.master = master
        self.frame = Frame(self.master)
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()

        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (serverIP, serverPort)
        self.rtpPort = rtpPort
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect(self.serverAddr)
            self.recvVideoList()
        except:
            tkMessageBox.showwarning('Connecting Failed', 'Fail to connect server')

        self.player = None

    def createWidgets(self):
        self.label1 = Label(self.master)
        self.label1['text'] = '搜索'
        self.label1.grid(row=0, column=0, columnspan=2)
        
        self.searchInput = Entry(self.master)
        self.searchInput.grid(row=1, column=0, padx=10, pady=10)
        # self.searchInput.grid(row=1, column=0, columnspan=2)

        self.searchButton = Button(self.master, width=8, height=1, padx=3, pady=3)
        self.searchButton['text'] = '搜索'
        self.searchButton['command'] = self.search
        self.searchButton.grid(row=1, column=1)

        self.label2 = Label(self.master, pady=3)
        self.label2['text'] = '播放列表'
        self.label2.grid(row=2, column=0, columnspan=2)

        self.playList = Listbox(self.master, selectmode=SINGLE)
        self.playList.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.playButton = Button(self.master, width=10, padx=3, pady=3)
        self.playButton['text'] = '播放'
        self.playButton['command'] = self.play
        self.playButton.grid(row=5, column=0, sticky=W)

        self.clearButton = Button(self.master, width=10, padx=3, pady=3)
        self.clearButton['text'] = '清空搜索结果'
        self.clearButton['command'] = self.clearSearch
        self.clearButton.grid(row=5, column=1, sticky=W)

    def recvVideoList(self):
        try:
            data = self.rtspSocket.recv(4096).decode()
        except:
            raise IOError

        lines = data.split('\n')
        len = int(lines[0].split()[-1])
        self.videoList = []
        for i in range(len):
            videoname = lines[i + 1].split()[-1]
            self.videoList.append(videoname)
            self.playList.insert('end', videoname)

    def search(self):
        var = self.searchInput.get()
        self.playList.delete(0, END)
        for videoname in self.videoList:
            if videoname.find(var) != -1:
                self.playList.insert('end', videoname)

    def clearSearch(self):
        self.searchInput.delete(0, END)
        self.playList.delete(0, END)
        for videoname in self.videoList:
            self.playList.insert('end', videoname)

    def play(self):
        if self.player is not None and self.player.teardownAcked == 0:
            tkMessageBox.showwarning('Warning', '请先关闭当前正在播放的视频')
            return
        var = self.playList.get(ACTIVE)
        print(var)
        if var is None or len(var) == 0:
            tkMessageBox.showwarning('Warning', '请选择一个视频播放')
            return
        self.newWindow = Toplevel(self.master)
        self.player = RtpClient(self.newWindow, self.serverIP, self.serverPort, self.rtpPort, var, self.rtspSocket)

    def handler(self):
        if self.player is not None and self.player.teardownAcked == 0:
            if tkMessageBox.askokcancel("Quit?", "Movie is playing, are you sure you want to quit?"):
                self.player.exitClient()
                self.master.destroy()
                return
            else:  # When the user presses cancel, resume playing.
                return
        self.rtspSocket.close()
        self.master.destroy()


root = Tk()
c = Client(root, '127.0.0.1', 6666, 5555)
root.mainloop()
print('666')
