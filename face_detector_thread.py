import numpy as np
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import time
from face_finder import find_faces, net

class FaceDetectorThread(QObject):

    found_face = pyqtSignal(np.ndarray)

    fps = 2
    def __init__(self):
        super().__init__()
        self.running = True
        self.frame = None


    def stop(self):
        self.running = False

    def send_frame(self, frame):
        self.frame = frame
        self.new_frame = True

    def run(self):
        while self.running:
            if not self.frame is None and self.new_frame:
                self.new_frame = False
                start_time = time.process_time()
                self.faces = find_faces(self.frame, net)
                if len(self.faces) > 0:
                    face = np.array(self.faces[0][1:5])
                    self.found_face.emit(face)

                end_time = time.process_time()
                elapsed_time = end_time - start_time
            else:
                elapsed_time = 0
            # sleep the rest of the time
            time.sleep(max(1/self.fps - elapsed_time, 0))


