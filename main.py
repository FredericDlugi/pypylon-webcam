import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from grab_thread import GrabThread
from preview_thread import PreviewThread
from face_detector_thread import FaceDetectorThread
from config_gui import ConfigGui


if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon('pylon_webcam_icon_64.png'))
    grab_thread = GrabThread()
    preview_thread = PreviewThread()
    face_detector_thread = FaceDetectorThread()
    grab_thread.frame_grabbed.connect(preview_thread.send_frame)
    grab_thread.frame_grabbed.connect(face_detector_thread.send_frame)
    face_detector_thread.found_face.connect(grab_thread.send_face)
    face_detector_thread.found_face.connect(preview_thread.send_face)
    gui = ConfigGui(grab_thread, preview_thread, face_detector_thread)

    sys.exit(app.exec_())
