from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import time
from face_finder import draw_face_box
import settings


class PreviewThread(QObject):

    preview_toggle = pyqtSignal()
    window_name = "Preview"
    vga_resolution = (854, 480)

    def __init__(self):
        super().__init__()
        self.running = True
        self.preview_enabled = False
        self.face = None

    def stop(self):
        self.running = False

    def enable_preview(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self.preview_enabled = True
        resolution = settings.get_setting(
            "preview_resolution", self.vga_resolution)
        cv2.resizeWindow(self.window_name, resolution[0], resolution[1])

    def disable_preview(self):
        self.preview_enabled = False

    def send_frame(self, frame):
        self.frame = frame

    def send_face(self, face):
        self.face = face

    def run(self):
        while self.running:
            if self.preview_enabled:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.preview_toggle.emit()
                    self.preview_enabled = False
                else:
                    if not self.face is None:
                        draw_face_box(self.frame, self.face)
                    cv2.imshow(self.window_name, self.frame)
                    cv2.waitKey(30)
            else:
                cv2.destroyWindow(self.window_name)
                time.sleep(0.03)
