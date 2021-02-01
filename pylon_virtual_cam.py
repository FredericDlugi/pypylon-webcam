import numpy as np
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from grab_thread import GrabThread
from config_gui import ConfigGui


if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon('pylon_webcam_icon_64.png'))
    grab_thread = GrabThread()
    gui = ConfigGui(grab_thread)

    sys.exit(app.exec_())
