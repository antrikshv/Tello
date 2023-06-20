import cv2
import djitellopy as Tello
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import numpy as np
import queue
import threading
import asyncio
import math
import time
import tensorflow

async def processImg(imgCrop, h, w, index):   
    aspectRatio = h/w
    if aspectRatio>1:
        k = imgSize/h
        wCal = math.ceil(k*w)
        imgResize = cv2.resize(imgCrop, (wCal, imgSize))
        #imgResizeShape = imgResize.shape
        wGap = math.ceil((imgSize-wCal)/2)
        imgWhite[:,wGap:wCal+wGap] = imgResize
        pred, index = classifier.getPrediction(imgWhite)
        print(pred,index)
    else:
        k = imgSize/w
        hCal = math.ceil(k*h)
        imgResize = cv2.resize(imgCrop, (imgSize, hCal))
        #imgResizeShape = imgResize.shape
        hGap = math.ceil((imgSize-hCal)/2)
        imgWhite[hGap:hCal+hGap,:] = imgResize
        pred, index = classifier.getPrediction(imgWhite)
        print(pred,index)

    cv2.imshow("ImageCrop", imgWhite)
    
labels = ["Misc","Land","Formation"]
offset = 20
imgSize = 300
index = 0
pred = labels[index]
me = Tello.Tello("192.168.10.1", 1)
me.connect()
me.send_command_with_return("streamon")

detector = HandDetector(maxHands=1)
classifier = Classifier("HandSignalModel/keras_model.h5","HandSignalModel/labels.txt")
while True:
    img = me.get_frame_read().frame
    
    hands, img = detector.findHands(img)
    if hands:
        hand = hands[0]
        x,y,w,h = hand['bbox']
        
        imgWhite = np.ones((imgSize,imgSize,3),np.uint8)*255
        imgCrop = img[y-offset:y+h+offset, x-offset:x+w+offset]
        aspectRatio = h/w
        asyncio.run(processImg(imgCrop, h, w, index))
    #cv2.putText(img, labels[index], (x,y-20),cv2.FONT_HERSHEY_COMPLEX,2,(255,0,255),3)
    cv2.imshow("Image", img)
    cv2.waitKey(1)
