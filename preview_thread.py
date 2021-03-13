import numpy as np
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import time

class PreviewThread(QObject):

    preview_toggle = pyqtSignal()
    window_name = "Preview"
    vga_resolution = (854, 480)
    def __init__(self):
        super().__init__()
        self.running = True
        self.preview_enabled = False


    def stop(self):
        self.running = False

    def enable_preview(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.vga_resolution[0], self.vga_resolution[1])

        self.preview_enabled = True

    def disable_preview(self):
        cv2.destroyWindow(self.window_name)
        self.preview_enabled = False

    def send_rgb_img(self, frame):
        self.rgb_img = frame

    def run(self):
        while self.running:
            if self.preview_enabled:
                if cv2.getWindowProperty(self.window_name,cv2.WND_PROP_VISIBLE) < 1:
                    self.preview_toggle.emit()
                    self.preview_enabled = False
                else:
                    rgb_resized = cv2.resize(self.rgb_img, self.vga_resolution)
                    bgr_img = cv2.cvtColor(rgb_resized, cv2.COLOR_RGB2BGR)
                    cv2.imshow(self.window_name, bgr_img)
                    cv2.waitKey(30)
            else:
                time.sleep(0.02)
