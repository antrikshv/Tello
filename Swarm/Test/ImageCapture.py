from djitellopy import tello
import cv2, imutils, socket
import numpy as np
import time
import base64
# import pickle as pkl
# import socket

BUFF_SIZE = 65536
PCIP = "192.168.50.40"
PORTPCTX = 10000
CLIENTADDR = (PCIP, PORTPCTX)
me = tello.Tello()
me.connect()
print(me.get_battery())
me.streamon()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
fps,st,frames_to_count,cnt = (0,0,20,0)

while True:
    print(me.get_acceleration_x())
    img = me.get_frame_read().frame
    img = cv2.resize(img, (360, 240))
    encoded,buffer = cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,80])
    message = base64.b64encode(buffer)
    sock.sendto(message,CLIENTADDR)
    frame = cv2.putText(img,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
    cv2.imshow('TRANSMITTING VIDEO',frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        sock.close()
        break
    if cnt == frames_to_count:
        try:
            fps = round(frames_to_count/(time.time()-st))
            st=time.time()
            cnt=0
        except:
            pass
    cnt+=1
    # sock.sendto(b'hi', (PCIP, PORTPCTX))
    # img = me.get_frame_read().frame
    # print(f"original: {type(img)}" )
    # test1 = pkl.dumps(img)
    # print(test1)
    # sock.sendto(test1, (PCIP, PORTPCTX))
    # # test2 = pkl.loads(test1)
    # # print(f"test2: {type(test2)}")
    # # image = cv2.resize(test2, (360,240))
    # # cv2.imshow("TelloFootage", test2)
    # # cv2.waitKey(1)