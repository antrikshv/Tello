import tools.TelloTools as TelloClient
import time
import threading
import cv2

drone = TelloClient.Tello('192.168.10.1', 1)
drone.send_command_with_return("command")
time.sleep(2)
drone.send_command_with_return("streamon")

face_cascade = cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')     
while True:
    try:
        frame = drone.get_frame_read().frame
        cap = drone.get_video_capture()

        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        center_x = int(width/2)
        center_y = int(height/3)

        cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0))
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)
        
        face_center_x = center_x
        face_center_y = center_y
        z_area = 0
        for face in faces:
            (x, y, w, h) = face
            cv2.rectangle(frame,(x, y),(x + w, y + h),(255, 255, 0), 2)

            face_center_x = x + int(h/2)
            face_center_y = y + int(w/2)
            z_area = w * h

            cv2.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255))

        offset_x = face_center_x - center_x
        offset_y = face_center_y - center_y - 30
        cv2.putText(frame, f'[{offset_x}, {offset_y}, {z_area}]', (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2, cv2.LINE_AA)
        # self.adjust_tello_position(offset_x, offset_y, z_area)
            
        cv2.imshow('TELLO VIDEO',frame)
        cv2.waitKey(1)
        
    except:
        pass

