class VideoLoader:
    def __init__(self, filename):
        try:
            self.video = open(filename, 'rb')
        except:
            raise IOError
        self.frameSeq = 0

    def loadFrame(self):
        header = self.video.read(5)
        if header:
            length = int(header)
            frame = self.video.read(length)
            self.frameSeq += 1
            return frame
