import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2
import settings

class GrabThread(QObject):

    avg_fps = pyqtSignal(float)
    frame_grabbed = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    vga_resolution = (854, 480)

    def __init__(self):
        super().__init__()
        self.running = True
        self.camera = None
        self.virt_cam = None
        self.preview_enabled = False
        self.face = None
        self.face_id = 0



    def stop(self):
        self.running = False

    def set_camera(self, camera):
        self.camera = camera
        self.camera.PixelFormat = "BGR8"
        self.input_res = settings.get_setting("input_resolution", [self.camera.Width.Value, self.camera.Height.Value])
        self.output_res = settings.get_setting("output_resolution", [self.camera.Width.Value, self.camera.Height.Value])
        self.fps = settings.get_setting("fps", 30)
        self.camera.Width  = self.input_res[0]
        self.camera.Height = self.input_res[1]
        self.camera.AcquisitionFrameRate = self.fps
        self.camera.AcquisitionFrameRateEnable = True
        self.camera.AutoExposureTimeUpperLimit = settings.get_setting("max_exposure_time", 15000)
        self.virt_cam = pyvirtualcam.Camera(width=self.output_res[0],
                                            height=self.output_res[1],
                                            fps=self.fps,
                                            delay=0, print_fps=False, fmt=pyvirtualcam.PixelFormat.BGR)
        self.frame = np.full((self.camera.Height.Value, self.camera.Width.Value, 3), 255, np.uint8)

    def enable_preview(self):
        self.preview_enabled = True

    def disable_preview(self):
        self.preview_enabled = False

    def send_face(self, face):
        self.face_id += 1
        self.face = face

    def run(self):
        self.camera.MaxNumBuffer = 20
        self.camera.StartGrabbingMax(1_000_000_000, pylon.GrabStrategy_LatestImages)
        i = 0
        num_frames_no_face = 0
        last_id = 0
        while self.running:


            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_Return)
            # Image grabbed successfully?
            if grabResult.GrabSucceeded():
                self.frame = grabResult.Array
            grabResult.Release()

            if self.output_res != self.input_res:
                self.virt_cam.send(cv2.resize(self.frame, tuple(self.output_res)))
            else:
                self.virt_cam.send(self.frame)

            self.frame_grabbed.emit(self.frame)

            if i % 10 == 0:
                self.avg_fps.emit(self.virt_cam._fps_counter.avg_fps)


            if not self.face is None:
                center_face(self.camera, self.face)

                if self.face_id != last_id:
                    last_id = self.face_id
                    set_auto_functions(self.camera, self.face)
                    num_frames_no_face = 0
                else:
                    if num_frames_no_face > self.virt_cam.fps * 11:
                        self.face = None
                    num_frames_no_face += 1

            else:
                set_auto_functions(self.camera, np.array([0, 0, self.camera.Width.Value, self.camera.Height.Value]))
            self.virt_cam.sleep_until_next_frame()
            i += 1


        self.virt_cam.close()
        self.camera.Close()
        self.virt_cam = None
        self.camera = None
        self.running = True
        self.face = None
        self.preview_enabled = False
        self.finished.emit()
        self.avg_fps.emit(0)

def set_auto_functions(camera, face):
    offX = camera.OffsetX.GetValue()
    offY = camera.OffsetY.GetValue()

    startX = face[0]
    startY = face[1]
    endX   = face[2]
    endY   = face[3]

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


def center_face(camera, face):
    dead_zone = 100
    incX = camera.OffsetX.Inc
    incY = camera.OffsetX.Inc
    offX = camera.OffsetX.GetValue()
    offY = camera.OffsetY.GetValue()

    startX = face[0]
    startY = face[1]
    endX   = face[2]
    endY   = face[3]

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