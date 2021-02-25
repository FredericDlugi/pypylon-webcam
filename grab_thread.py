import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2

class GrabThread(QObject):

    avg_fps = pyqtSignal(float)
    finished = pyqtSignal()
    preview_toggle = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.camera = None
        self.virt_cam = None
        self.preview_enabled = False


    def stop(self):
        self.running = False
        print("stopping GrabThread")

    def set_camera(self, camera):
        self.camera = camera
        if self.virt_cam is None:
            self.virt_cam = pyvirtualcam.Camera(width=self.camera.Width.Value, height=self.camera.Height.Value, fps=self.camera.BslResultingAcquisitionFrameRate.Value, print_fps=False, pixForm=pyvirtualcam.PixelFormat.AV_PIX_FMT_YUYV422)
            self.frame = np.full((self.camera.Height.Value, self.camera.Width.Value, 2), 255, np.uint8)  # Ycbcr422

    def enable_preview(self):
        cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Preview", 854, 480)
        self.preview_enabled = True

    def disable_preview(self):
        cv2.destroyWindow("Preview")
        self.preview_enabled = False

    def run(self):
        self.camera.MaxNumBuffer = 20
        self.camera.StartGrabbingMax(100000000, pylon.GrabStrategy_LatestImages)
        i = 0
        while self.running:


            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_Return)
            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                self.frame = grabResult.Array
            else:
                print("grab Failed")
            grabResult.Release()
            self.virt_cam.send(self.frame)

            if self.preview_enabled:
                if cv2.getWindowProperty('Preview',cv2.WND_PROP_VISIBLE) < 1:
                    self.preview_toggle.emit()
                else:
                    cv2.imshow("Preview", cv2.cvtColor(self.frame, cv2.COLOR_YUV2BGR_YUY2))
                    cv2.waitKey(1)

            if i % 10 == 0:
                self.avg_fps.emit(self.virt_cam._fps_counter.avg_fps)

            self.virt_cam.sleep_until_next_frame()
            i += 1

        self.virt_cam.close()
        self.camera.Close()
        print("finished GrabThread")
        self.finished.emit()
        self.avg_fps.emit(0)
