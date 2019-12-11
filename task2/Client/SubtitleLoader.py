def t2s(t):
    h, m, s = t.strip().split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


class SubtitleLoader:
    def __init__(self, srtName, length):
        try:
            self.file = open(srtName, 'r')
        except:
            raise IOError

        self.length = length
        self.content = [None for i in range(length)]
        self.load_subtitle()
        print(self.content)

    def load_subtitle(self):
        self.seq = 1
        lines = self.file.readlines()
        l = len(lines)
        i = 0
        while i < l:
            if lines[i][:-1] == str(self.seq):
                i += 1
                line = lines[i][:-1].split()
                starttime = line[0].split(',')[0]
                starttime = t2s(starttime)
                endtime = line[-1].split(',')[0]
                endtime = t2s(endtime)
                i += 1
                content = lines[i].strip()
                try:
                    self.content[starttime] = content
                    for j in range(starttime + 1, endtime + 1):
                        self.content[j] = True
                except:
                    return
                self.seq += 1
            else:
                i += 1

    def getsub(self, sec):
        try:
            c = self.content[sec]
            return c
        except:
            return None

