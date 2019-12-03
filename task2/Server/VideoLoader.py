from cv2 import *
import os


class VideoLoader:
    def __init__(self, videoName):
        videoName = os.path.join('videos/', videoName)
        print(videoName)
        if not os.path.isfile(videoName):
            raise IOError
        try:
            self.video = VideoCapture(videoName)
            self.fps = self.video.get(cv2.CAP_PROP_FPS)
            self.frameNum = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        except:
            raise IOError
        self.frameSeq = 0

    def getFrame(self, quality=100):
        ret, frame = self.video.read()
        if ret:
            q = [int(IMWRITE_WEBP_QUALITY), quality]
            ret, buffer = imencode('.webp', frame, q)
            if ret:
                print(type(buffer))
                print(buffer)
                return buffer
        return None

    def reposition(self, sec):
        milisec = sec * 1000
        try:
            self.video.set(CAP_PROP_POS_MSEC, milisec)
        except:
            return False
        return True

    def getSeq(self):
        return self.frameSeq

    def getLen(self):
        return self.frameNum / self.fps

    def getFps(self):
        return self.fps

    def __del__(self):
        try:
            self.video.release()
        except:
            pass
