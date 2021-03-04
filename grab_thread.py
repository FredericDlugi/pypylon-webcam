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
        avail_pix_for = self.camera.PixelFormat.GetSymbolics()
        self.is_color = "YCbCr422_8" in avail_pix_for
        if self.is_color:
            self.camera.PixelFormat = "YCbCr422_8"
        else:
            self.camera.PixelFormat = "Mono8"


        if self.virt_cam is None:
            if self.is_color:
                self.virt_cam = pyvirtualcam.Camera(width=self.camera.Width.Value,
                                                    height=self.camera.Height.Value,
                                                    fps=self.camera.BslResultingAcquisitionFrameRate.Value,
                                                    pixel_format=pyvirtualcam.PixelFormat.YUYV422,
                                                    delay=0, print_fps=False)
                self.frame = np.full((self.camera.Height.Value, self.camera.Width.Value, 2), 255, np.uint8)  # Ycbcr422
            else:
                self.virt_cam = pyvirtualcam.Camera(width=self.camera.Width.Value,
                                                    height=self.camera.Height.Value,
                                                    fps=self.camera.BslResultingAcquisitionFrameRate.Value,
                                                    pixel_format=pyvirtualcam.PixelFormat.GRAY8,
                                                    delay=0, print_fps=False)
                self.frame = np.full((self.camera.Height.Value, self.camera.Width.Value, 1), 255, np.uint8)  # Mono8

    def enable_preview(self):
        cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Preview", 854, 480)
        self.preview_enabled = True

    def disable_preview(self):
        cv2.destroyWindow("Preview")
        self.preview_enabled = False

    def run(self):
        print("started GrabThread")
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
                    if self.is_color:
                        img = cv2.cvtColor(self.frame, cv2.COLOR_YUV2BGR_YUY2)
                    else:
                        img = self.frame
                    cv2.imshow("Preview", img)
                    cv2.waitKey(1)

            if i % 10 == 0:
                self.avg_fps.emit(self.virt_cam._fps_counter.avg_fps)

            self.virt_cam.sleep_until_next_frame()
            i += 1

        if self.preview_enabled:
            self.preview_toggle.emit()

        self.virt_cam.close()
        self.camera.Close()
        self.virt_cam = None
        self.camera = None
        self.running = True
        print("finished GrabThread")
        self.finished.emit()
        self.avg_fps.emit(0)
