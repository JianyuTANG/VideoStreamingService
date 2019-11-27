import os


class VideoLoader:
    def __init__(self, folder):
        if not os.path.isdir(folder):
            raise IOError
        self.frameSeq = 0

    def getFrame(self):
        header = self.video.read(5)
        if header:
            length = int(header)
            frame = self.video.read(length)
            self.frameSeq += 1
            return frame
        return None

    def getSeq(self):
        return self.frameSeq
