import os
from cv2 import *


class VideoLoader:
    def __init__(self, videoName):
        videoName = os.path.join('videos/', videoName)
        if not os.path.isfile(videoName):
            raise IOError
        try:
            self.video = VideoCapture(videoName)
        except:
            raise IOError
        self.frameSeq = 0

    def getFrame(self, quality):
        ret, frame = self.video.read()
        if ret:
            q = ['CV_IMWRITE_WEBP_QUALITY', quality]
            ret, buffer = imencode('WEBP', frame, q)
            if ret:
                return buffer

        return None

    def getSeq(self):
        return self.frameSeq

    def __del__(self):
        self.video.release()
