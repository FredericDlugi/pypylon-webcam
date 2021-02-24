import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ConfigGui(QWidget):

    def __init__(self, grab_thread):
        super().__init__()

        vbox = QVBoxLayout()
        self.camera = None

        self.camera_list = QComboBox()
        self.discover_button = QPushButton("Discover")
        self.discover_button.clicked.connect(self.discover_cameras)
        self.connect_button = QPushButton("Open")
        self.connect_button.clicked.connect(self.connect_camera)
        self.discover_cameras()

        discover_box = QHBoxLayout()
        discover_box.addWidget(self.camera_list)
        discover_box.addWidget(self.discover_button)
        discover_box.addWidget(self.connect_button)

        vbox.addLayout(discover_box)

        self.camera_feature_box = QVBoxLayout()
        vbox.addLayout(self.camera_feature_box)
        vbox.addStretch()
        self.avg_fps_label = QLabel("FPS:  0.00")
        vbox.addWidget(self.avg_fps_label)
        self.setLayout(vbox)
        self.setGeometry(50,50,320,200)
        self.setWindowTitle("Pylon Webcam")

        self.setup_minimize_to_tray()

        self.grab_thread = grab_thread
        self.grab_thread.finished.connect(self.grab_thread_finished)
        self.grab_thread.avg_fps.connect(self.update_avg_fps)
        self.thread = QThread()
        self.grab_thread.moveToThread(self.thread)
        self.thread.started.connect(self.grab_thread.run)

        self.show()

    def setup_minimize_to_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('pylon_webcam_icon_64.png'))

        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, event):
        if event == QSystemTrayIcon.DoubleClick:
            self.show()


    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Pylon Webcam",
                    "Application was minimized to Tray",
                    1000
                )

    def show(self):
        super().show()
        self.setWindowState(Qt.WindowNoState)


    def grab_thread_finished(self):
        self.connect_button.setDisabled(False)
        self.discover_cameras()

    def update_avg_fps(self, value):
        self.avg_fps_label.setText("FPS: {:2.2f}".format(value))

    def discover_cameras(self):
        self.full_name_list = []
        self.camera_list.clear()
        devices = pylon.TlFactory.GetInstance().EnumerateDevices()
        self.camera_list.setDisabled(len(devices) == 0)
        self.connect_button.setDisabled(len(devices) == 0)
        for cam in devices:
            self.camera_list.addItem(cam.GetFriendlyName())
            self.full_name_list.append(cam.GetFullName())

    def connect_camera(self):
        if self.camera is None:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(self.full_name_list[self.camera_list.currentIndex()]))
            self.camera.Open()
            self.grab_thread.set_camera(self.camera)
            print("start GrabThread")
            self.thread.start()
            # update gui
            self.connect_button.setText("Close")
            self.setup_camera_features()

        else:
            self.grab_thread.stop()
            self.connect_button.setDisabled(True)
            self.connect_button.setText("Open")
            self.camera = None

    def setup_camera_features(self):
        clearLayout(self.camera_feature_box)

        if hasattr(self.camera, "AutoTargetBrightness"):
            self.brightness_slider = SliderFeature(self.camera.AutoTargetBrightness, "Brightness")
            self.camera_feature_box.addLayout(self.brightness_slider.get_layout())

        if hasattr(self.camera, "BslContrast"):
            self.contrast_slider = SliderFeature(self.camera.BslContrast, "Contrast")
            self.camera_feature_box.addLayout(self.contrast_slider.get_layout())

        if hasattr(self.camera, "BslSaturation"):
            self.saturation_slider = SliderFeature(self.camera.BslSaturation, "Saturation")
            self.camera_feature_box.addLayout(self.saturation_slider.get_layout())

        if hasattr(self.camera, "BslHue"):
            self.hue_slider = SliderFeature(self.camera.BslHue, "Hue")
            self.camera_feature_box.addLayout(self.hue_slider.get_layout())

        if hasattr(self.camera, "Gamma"):
            self.gamma_slider = SliderFeature(self.camera.Gamma, "Gamma")
            self.camera_feature_box.addLayout(self.gamma_slider.get_layout())

        if hasattr(self.camera, "BslSharpnessEnhancement"):
            self.sharpness_slider = SliderFeature(self.camera.BslSharpnessEnhancement, "Sharpness")
            self.camera_feature_box.addLayout(self.sharpness_slider.get_layout())

        if hasattr(self.camera, "BslNoiseReduction"):
            self.noise_slider = SliderFeature(self.camera.BslNoiseReduction, "NoiseReduction")
            self.camera_feature_box.addLayout(self.noise_slider.get_layout())

        if hasattr(self.camera, "BslLightSourcePreset"):
            self.light_source_enum = EnumFeature(self.camera.BslLightSourcePreset, "LightSource")
            self.camera_feature_box.addLayout(self.light_source_enum.get_layout())

def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    if child.widget():
      child.widget().deleteLater()

class SliderFeature:

    def __init__(self, feature, name):
        self.SLIDER_MAX = 100
        self.SLIDER_MIN = 0
        self.feature = feature
        self.label = QLabel(name)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.SLIDER_MIN, self.SLIDER_MAX)
        self.slider.setValue((self.feature.Value - self.feature.Min) / (self.feature.Max - self.feature.Min) * self.SLIDER_MAX)
        self.slider.setFixedWidth(200)
        self.slider.valueChanged[int].connect(self.value_changed)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.slider)


    def get_layout(self):
        return self.layout

    def value_changed(self, value):
        self.feature.Value =  (value / self.SLIDER_MAX) * (self.feature.Max - self.feature.Min) + self.feature.Min


class EnumFeature:

    def __init__(self, feature, name):
        self.feature = feature
        self.label = QLabel(name)
        self.combobox = QComboBox()
        self.enumText = [e.GetSymbolic() for e in self.feature.GetEntries()]
        self.combobox.addItems(self.enumText)
        self.combobox.setCurrentText(self.feature.GetCurrentEntry().GetSymbolic())
        self.combobox.currentIndexChanged.connect(self.index_changed)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addStretch()
        self.layout.addWidget(self.combobox)


    def get_layout(self):
        return self.layout

    def index_changed(self, index):
        self.feature.Value = self.combobox.currentText()

