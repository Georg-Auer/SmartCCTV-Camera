#Modified by Georg Auer
#Desc: Camera import for Flask

import cv2
try:
    from imutils.video.pivideostream import PiVideoStream
except:
    print("No Raspberry/No Raspberry Cam found")
import imutils
import time
import numpy as np

class VideoCamera(object):
    def __init__(self, flip = False):
        try:
            self.vs = PiVideoStream().start()
        except:
            self.vs = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            #0 is the standard number of the connected camera in windows
        self.flip = flip
        time.sleep(2.0)

    def __del__(self):
        try:
            self.vs.stop()
        except:
            self.vs.release()

    def flip_if_needed(self, frame):
        if self.flip:
            return np.flip(frame, 0)
        return frame

    def get_frame(self):
        try:
            frame = self.flip_if_needed(self.vs.read())
            ret, jpeg = cv2.imencode('.jpg', frame)
        except:
            ret, frame = self.vs.read()
            ret, jpeg = cv2.imencode('.jpg', frame)

        #ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def take_image(self):
        try:
            ret, frame = self.vs.read()
            # for printing path where image was saved
            # self.vs.stop()

            # self.vs = PiVideoStream().start()
        except:
            print("take_image did not work")

        ret, jpeg = cv2.imencode('.jpg', frame)
        return frame, jpeg
