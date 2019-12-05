from cv2 import *
import os
import shutil
import numpy as np


default_folder = 'videos/'
img_suffix = '.jpg'
quality = 30


def processMovie(videoName):
    if not os.path.isfile(videoName):
        raise IOError

    try:
        video = VideoCapture(videoName)
        frameNum = video.get(CAP_PROP_FRAME_COUNT)
        print('total frames: ' + str(frameNum))
    except:
        raise IOError
    foldername = videoName.split('/')[-1].split('.')[0]
    foldername = os.path.join(default_folder, foldername)
    if os.path.isdir(foldername):
        shutil.rmtree(foldername)
    os.mkdir(foldername)
    seq = 0
    ret, frame = video.read()
    while ret:
        img_name = str(seq) + img_suffix
        img_name = os.path.join(foldername, img_name)
        frame = np.array(frame)
        # frame = frame[:, :, ::-1]
        q = [IMWRITE_JPEG_QUALITY, quality]
        imwrite(img_name, frame, q)
        ret, frame = video.read()
        seq += 1
        if seq % 10 == 0:
            print(seq)
    print('finished frames: ' + str(seq))


processMovie('videos/1.mp4')
