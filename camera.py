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
            # try raspberry camera first
            try:
                self.vs = PiVideoStream(resolution=(320, 240)).start()
                print("started with custom resolution")
            except:
                self.vs = PiVideoStream().start()
                print("started with standard resolution")
            #resolution=(640, 480)
            #resolution=(320, 240)
        except:
            # start webcam for testing instead
            self.vs = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            #0 is the standard number of the connected camera in windows
        self.flip = flip
        time.sleep(1.0)

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

        # now returns a simple frame additionally
        return jpeg.tobytes(), frame

    def get_frame_resolution(self):
        object_methods = [method_name for method_name in dir(self.resolution)
                  if callable(getattr(self.resolution, method_name))]
        print(object_methods)
        print(f"previously set resolution: {self.vs.resolution}")
        try:
            self.vs.VideoCapture().resolution = (320, 240)
        print(f"previously set resolution: {self.vs.resolution}")
        try:
            frame = self.flip_if_needed(self.vs.read())
            ret, jpeg = cv2.imencode('.jpg', frame)
        except:
            ret, frame = self.vs.read()
            ret, jpeg = cv2.imencode('.jpg', frame)

        # set resolution back to last value
        try:
            self.vs.resolution = (320, 240)
        # 640, 480
        # 1280, 720
        #resolution=(320, 240)
        # now returns a simple frame additionally
        return jpeg.tobytes(), frame

    # def take_image(self):
    #     # stop cam before taking images
    #     # try:
    #     #     self.vs.stop()
    #     # except:
    #     #     self.vs.release()

    #     try:
    #         ret, frame = self.vs.read()
    #         # for printing path where image was saved
    #         # self.vs.stop()

    #         # self.vs = PiVideoStream().start()
    #     except:
    #         print("take_image did not work")

    #     ret, jpeg = cv2.imencode('.jpg', frame)
    #     return frame, jpeg
