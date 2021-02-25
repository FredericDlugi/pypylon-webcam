import numpy as np
import time
import pyvirtualcam
from pypylon import pylon
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent=parent)


    def run(self):
        while True:

            a = np.zeros((1080, 1920,3), dtype=np.uint8)

            rawImage = QImage(a.data, a.shape[1], a.shape[0], QImage.Format_RGB888)

            self.changePixmap.emit(rawImage)
            time.sleep(1)

class App(QWidget):
    def __init__(self):
            super(App,self).__init__()
            self.title = 'PyQt4 Video'
            self.left = 100
            self.top = 100
            self.width = 640
            self.height = 480
            self.initUI()

    def initUI(self):
            self.setWindowTitle(self.title)
            self.setGeometry(self.left, self.top, self.width, self.height)
            self.resize(800, 600)
            # create a label
            self.label = QLabel(self)
            self.label.move(0, 0)
            self.label.resize(640, 480)
            th = Thread(self)
            th.changePixmap.connect(self.setPixMap)
            th.start()

    def setPixMap(self, p):
        p = QPixmap.fromImage(p)
        p = p.scaled(640, 480, Qt.KeepAspectRatio)
        self.label.setPixmap(p)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    print("Setup successfull")

    sys.exit(app.exec_())