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

    def __init__(self, preview_thread_send_frame):
        super().__init__()
        self.running = True
        self.camera = None
        self.virt_cam = None
        self.preview_enabled = False
        self.preview_thread_send_frame = preview_thread_send_frame


    def stop(self):
        self.running = False
        print("stopping GrabThread")

    def set_camera(self, camera):
        self.camera = camera
        self.camera.PixelFormat = "RGB8"
        if self.virt_cam is None:
            self.virt_cam = pyvirtualcam.Camera(width=self.camera.Width.Value,
                                                height=self.camera.Height.Value,
                                                fps=self.camera.BslResultingAcquisitionFrameRate.Value,
                                                delay=0, print_fps=False)
            self.frame = np.full((self.camera.Height.Value, self.camera.Width.Value, 3), 255, np.uint8)  # Ycbcr422

    def enable_preview(self):
        self.preview_enabled = True

    def disable_preview(self):
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

            self.preview_thread_send_frame(self.frame)

            if i % 10 == 0:
                faces = set_auto_functions(self.camera, self.frame)
                if len(faces) >= 1:
                    self.faces = faces

                self.avg_fps.emit(self.virt_cam._fps_counter.avg_fps)

            if len(self.faces) >= 1:
                center_face(self.camera, self.faces[0])

            self.virt_cam.sleep_until_next_frame()
            i += 1


        self.virt_cam.close()
        self.camera.Close()
        self.virt_cam = None
        self.camera = None
        self.running = True
        self.preview_enabled = False
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

        camera.BalanceWhiteAuto.Value = "Once"
        camera.ExposureAuto.Value = "Once"
        camera.GainAuto.Value = "Once"

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