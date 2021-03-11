import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
from face_finder import find_faces, net, draw_face_box

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
        self.camera.StartGrabbingMax(1_000_000_000, pylon.GrabStrategy_LatestImages)
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
                        if len(self.faces) >= 1:
                            draw_face_box(img, self.faces)

                    else:
                        img = self.frame
                    cv2.imshow("Preview", img)
                    cv2.waitKey(1)

            if i % 10 == 0:
                img = cv2.cvtColor(self.frame, cv2.COLOR_YUV2BGR_YUY2)
                faces = set_auto_functions(self.camera, img)
                if len(faces) >= 1:
                    self.faces = faces

                self.avg_fps.emit(self.virt_cam._fps_counter.avg_fps)

            if len(self.faces) >= 1:
                center_face(self.camera, self.faces[0])

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

def set_auto_functions(camera, img):
    faces = find_faces(img, net)
    offX = camera.OffsetX.GetValue()
    offY = camera.OffsetY.GetValue()

    if len(faces) >= 1:
        (conf, startX, startY, endX, endY) = faces[0]

        face_width =  endX - startX
        face_height = endY - startY
        face_abs_start_x = offX + startX
        face_abs_start_y = offY + startY


        set_int_value(camera.AutoFunctionROIWidth, face_width)
        set_int_value(camera.AutoFunctionROIHeight, face_height)
        set_int_value(camera.AutoFunctionROIOffsetX, face_abs_start_x)
        set_int_value(camera.AutoFunctionROIOffsetY, face_abs_start_y)

    return faces

def center_face(camera, face):
    dead_zone = 200
    incX = camera.OffsetX.Inc
    incY = camera.OffsetX.Inc
    offX = camera.OffsetX.GetValue()
    offY = camera.OffsetY.GetValue()


    (conf, startX, startY, endX, endY) = face

    face_width =  endX - startX
    face_height = endY - startY

    face_center_x = startX + face_width // 2
    face_center_y = startY + face_height // 2

    height = camera.Height.Value
    width = camera.Width.Value

    if face_center_x > ((width/2)+dead_zone):
        new_off_x = offX + incX
    elif face_center_x < ((width/2)-dead_zone):
        new_off_x = offX - incX
    else:
        new_off_x = offX


    if face_center_y < ((height/2)- dead_zone):
        new_off_y = offY - incY
    elif face_center_y > ((height/2) + dead_zone):
        new_off_y = offY + incY
    else:
        new_off_y = offY

    set_int_value(camera.OffsetX, new_off_x)
    set_int_value(camera.OffsetY, new_off_y)


def set_int_value(feature, value):
    val_0_min = value - feature.Min
    val_corr_inc = (val_0_min // feature.Inc) * feature.Inc

    val = min(max(val_corr_inc + feature.Min, feature.Min), feature.Max)

    feature.Value = int(val)