import cv2
import djitellopy as Tello
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import queue
import threading
import asyncio
import math
import time

async def processImg(imgCrop, h, w, saveimg, folder):   
    aspectRatio = h/w
    if aspectRatio>1:
        k = imgSize/h
        wCal = math.ceil(k*w)
        imgResize = cv2.resize(imgCrop, (wCal, imgSize))
        #imgResizeShape = imgResize.shape
        wGap = math.ceil((imgSize-wCal)/2)
        imgWhite[:,wGap:wCal+wGap] = imgResize
    else:
        k = imgSize/w
        hCal = math.ceil(k*h)
        imgResize = cv2.resize(imgCrop, (imgSize, hCal))
        #imgResizeShape = imgResize.shape
        hGap = math.ceil((imgSize-hCal)/2)
        imgWhite[hGap:hCal+hGap,:] = imgResize

    #cv2.imshow("ImageCrop", imgWhite)
    if (saveimg):
        
        cv2.imwrite(f'{folder}/Image_{time.time()}.jpg',imgWhite)
    

offset = 20
imgSize = 300
folder = "ASL/Formation"
counter = 0
saveimg = False
me = Tello.Tello("192.168.10.1", 1)
me.connect()
me.send_command_with_return("streamon")
#cap = me.get_video_capture()

detector = HandDetector(maxHands=1)
while True:
    img = me.get_frame_read().frame
    hands, img = detector.findHands(img)
    if hands:
        hand = hands[0]
        x,y,w,h = hand['bbox']
        
        imgWhite = np.ones((imgSize,imgSize,3),np.uint8)*255
        imgCrop = img[y-offset:y+h+offset, x-offset:x+w+offset]
        aspectRatio = h/w
        asyncio.run(processImg(imgCrop, h, w, saveimg, folder))
        
    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord("s"):
        counter+=1
        print(counter)
        saveimg=True
    else:
        saveimg=False

    