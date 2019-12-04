from cv2 import *
import os
import numpy as np
from PIL import Image, ImageTk
from tkinter import Tk


class VideoLoader:
    def __init__(self, videoName):
        videoName = os.path.join('videos/', videoName)
        print(videoName)
        if not os.path.isfile(videoName):
            raise IOError
        try:
            self.video = VideoCapture(videoName)
            self.fps = self.video.get(CAP_PROP_FPS)
            self.frameNum = self.video.get(CAP_PROP_FRAME_COUNT)
            self.height = self.video.get(CAP_PROP_FRAME_HEIGHT)
        except:
            raise IOError
        self.frameSeq = -1

    def getFrame(self, quality=100):
        ret, frame = self.video.read()
        if ret:
            frame = np.array(frame)
            q = [int(IMWRITE_JPEG_QUALITY), quality]
            ret, buffer = imencode('.jpg', frame, q)
            buffer = np.array(buffer)
            buffer = buffer.tostring()
            if ret:
                self.frameSeq += 1
                return buffer
        return None

    def reposition(self, sec):
        milisec = sec * 1000
        try:
            self.video.set(CAP_PROP_POS_MSEC, milisec)
            self.frameSeq = int(self.video.get(cv2.CAP_PROP_POS_FRAMES) - 1)
        except:
            return False

        return True

    def getSeq(self):
        return self.frameSeq

    def getLen(self):
        return self.frameNum / self.fps

    def getFps(self):
        return self.fps

    def getHeight(self):
        return self.height

    def __del__(self):
        try:
            self.video.release()
        except:
            pass
