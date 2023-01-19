from contextlib import redirect_stderr
import sys
import os, os.path
from PIL import Image
from PIL.Image import fromarray
from PyQt5 import *
from PyQt5.uic import loadUi

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

parentDirectory = os.path.dirname(__file__)
PathT = os.path.join(parentDirectory, 'Tesseract-OCR')
newPath = os.path.join(PathT, 'tesseract.exe')

import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = newPath

from UI_MainWin import Ui_MainWindow

videoPath = 0
directoryPath = ''
captureType = 0

config = ('-l fil — oem 1 — psm 3')
outputContainer = ''

class mainwindow:
    
    def __init__(self):

        self.buttonclicked = False
        self.outputChecker = None

        self.VideoOCR = VideoOCR()
        self.VideoIn = VideoIn()
        self.OCR = OCR()

        self.main_win = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_win)

        self.ui.btnCamera.clicked.connect(self.on_btnCamera_clicked)
        self.ui.btnStopCamera.clicked.connect(self.on_btnStopCamera_clicked)
        self.ui.btnFile.clicked.connect(self.on_btnFile_clicked)
        self.ui.btnDirectory.clicked.connect(self.on_btnDirectory_clicked)
        self.ui.btnExit.clicked.connect(self.on_btnExit_clicked)

    def show(self):
        self.main_win.show()

    def on_btnStopCamera_clicked(self):
        if self.buttonclicked == True:
            self.buttonclicked = False
            if self.outputChecker == True:
                self.Remove_Image()
                self.VideoIn.ImageUpdate.disconnect(self.ImageUpdateSlot)
                self.OCR.ImageUpdate.disconnect(self.ImageUpdateSlotOCR)
                self.OCR.stop()
                self.VideoIn.stop()
            elif self.outputChecker == False:
                self.Remove_Image()
                self.VideoOCR.ImageUpdate.disconnect(self.ImageUpdateSlot)
                self.VideoOCR.stop()
        self.ui.vidOut.setText('Video Turned Off')

    def on_btnCamera_clicked(self):
        if self.buttonclicked == False:
            self.buttonclicked = True
            self.outputChecker = True
            self.Remove_Image()
            self.Open_Webcam()
            self.VideoIn.start()
            self.OCR.start()
            self.VideoIn.ImageUpdate.connect(self.ImageUpdateSlot)
            self.OCR.ImageUpdate.connect(self.ImageUpdateSlotOCR)

    def on_btnFile_clicked(self):
        if self.buttonclicked == False:
            self.buttonclicked = True
            self.outputChecker = False
            self.Remove_Image()
            self.Open_File()
            self.VideoOCR.start()
            self.VideoOCR.ImageUpdate.connect(self.ImageUpdateSlot)

    def on_btnDirectory_clicked(self):
        self.Open_Folder()

    def ImageUpdateSlot(self, Image):
        self.ui.ocrOut_2.setPixmap(QPixmap.fromImage(Image))

    def ImageUpdateSlotOCR(self, Image):
        self.ui.vidOut.setPixmap(QPixmap.fromImage(Image))

    def Open_Webcam(self):
        global videoPath
        videoPath = int(0)

    def Open_File(self):
        fname = QFileDialog.getOpenFileName()
        global videoPath
        videoPath = str(fname[0])

    def Open_Folder(self):
        fname = QFileDialog.getOpenFileName()
        global directoryPath
        directoryPath = fname[0]
        try:
            file = open(directoryPath, "w")
            file.write(outputContainer)
            file.close()
        except:
            pass

    def Remove_Image(self):
        self.ui.vidOut.clear()
        self.ui.ocrOut_2.clear()
        
    def StopCam(self):
        self.WebcamOCR.stop()

    def on_btnExit_clicked(self):
        sys.exit(0)

Capture = cv2.VideoCapture(0)

class VideoIn(QThread):

    ImageUpdate = pyqtSignal(QImage)

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            ret, frame = Capture.read()
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ConvertToQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(640, 480)
                self.ImageUpdate.emit(Pic)

    def stop(self):
        self.ThreadActive = False
        Capture.release
        self.quit()

class OCR(QThread):

    ImageUpdate = pyqtSignal(QImage)

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            ret, frame = Capture.read()
            if ret:
                transparent = cv2.imread('transparent.png', -1)

                self.boxes = pytesseract.image_to_data(frame, config = config)
                self.imgchar=pytesseract.image_to_string(frame, config = config)

                for x, b in enumerate(self.boxes.splitlines()):
                    if x !=0:
                        b = b.split()
                        if len(b) == 12:
                            x, y, w, h = int(b[6]), int(b[7]), int(b[8]), int(b[9])
                            #cv2.rectangle(transparent, (640, 479), (0, 445), (0, 0, 0, 200), -1)
                            cv2.rectangle(transparent, (x, y), (w + x, h + y), (0, 0, 255, 255), 1)
                            #cv2.rectangle(transparent, (x,y), (w + x, h + y), (0, 0, 0, 128), -1)

                            cv2.putText(transparent, b[11], (x , y),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255, 255), 1)
                    
                Image = cv2.cvtColor(transparent, cv2.COLOR_BGRA2RGBA)
                ConvertToQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format_RGBA8888)
                Pic = ConvertToQtFormat.scaled(640, 480)
                self.ImageUpdate.emit(Pic)

            try:
                global outputContainer
                outputContainer = self.imgchar
            except:
                pass

    def stop(self):
        try:
            global outputContainer
            outputContainer = self.imgchar
        except:
            pass
        Capture.release
        self.ThreadActive = False
        self.quit()

class VideoOCR(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.VideoCapture = cv2.VideoCapture(videoPath)
        self.ThreadActive = True
        while self.ThreadActive:
            ret, frame = self.VideoCapture.read()
            if ret:
                imH, imW, _ = frame.shape
                self.imgchar = pytesseract.image_to_string(frame, config = config)
                self.imgbox = pytesseract.image_to_data(frame, config = config)

                for x, b in enumerate(self.imgbox.splitlines()):
                    if x != 0:
                        b = b.split()
                        if len(b) == 12:
                            x, y, w, h = int(b[6]), int(b[7]), int(b[8]), int(b[9])
                            cv2.rectangle(frame, (x, y), (w + x, h + y), (0, 0, 255), 1)
                            #cv2.rectangle(frame, (640, 479), (0, 445), (0, 0, 0, 200), -1)

                            cv2.putText(frame, b[11], (x, y),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ConvertToQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(1280, 960)
                self.ImageUpdate.emit(Pic)

            try:
                global outputContainer
                outputContainer = self.imgchar
            except:
                pass

    def stop(self):
        try:
            global outputContainer
            outputContainer = self.imgchar
        except:
            pass
        self.ThreadActive = False
        self.VideoCapture.release
        self.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = mainwindow()
    main_win.show()
    sys.exit(app.exec())