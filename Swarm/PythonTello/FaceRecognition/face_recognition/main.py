import numpy as np
import cv2 as cv
import tello_drone as tello

host = ''
port = 9000
local_address = (host, port)

# Pass the is_dummy flag to run the face detection on a local camera
drone = tello.Tello(host, port, is_dummy=False)
drone.send_command("takeoff")
def adjust_tello_position(offset_x, offset_y, offset_z):
    """
    Adjusts the position of the tello drone based on the offset values given from the frame

    :param offset_x: Offset between center and face x coordinates
    :param offset_y: Offset between center and face y coordinates
    :param offset_z: Area of the face detection rectangle on the frame
    """
    if not -90 <= offset_x <= 90 and offset_x is not 0:
        offset_x = offset_x/8
    else:
        offset_x = 0
    if not -50 <= offset_y <= 50 and offset_y is not -30:
        offset_y = offset_y/7
    else:
        offset_y = 0
    if not 22000 <= offset_z <= 32000 and offset_z is not 0:
        offset_z = ((offset_z-27000)/900)
    else:
        offset_z = 0

    drone.send_rc_control(0, -offset_z, -offset_y ,offset_x)
    # drone.send_rc_control(0, -offset_z, 0, 0)



face_cascade = cv.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')
frame_read = drone.get_frame_read()
while True:
    frame = frame_read.frame

    cap = drone.get_video_capture()

    height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    width = cap.get(cv.CAP_PROP_FRAME_WIDTH)

    center_x = int(width/2)
    center_y = int(height/3)

    cv.circle(frame, (center_x, center_y), 10, (0, 255, 0))
    
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)

    face_center_x = center_x
    face_center_y = center_y
    z_area = 0
    for face in faces:
        (x, y, w, h) = face
        cv.rectangle(frame,(x, y),(x + w, y + h),(255, 255, 0), 2)

        face_center_x = x + int(h/2)
        face_center_y = y + int(w/2)
        z_area = w * h

        cv.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255))

    offset_x = face_center_x - center_x
    offset_y = face_center_y - center_y - 30

    cv.putText(frame, f'[{offset_x}, {offset_y}, {z_area}]', (10, 50), cv.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2, cv.LINE_AA)
    adjust_tello_position(offset_x, offset_y, z_area)
    
    cv.imshow('Tello detection...', frame)
    if cv.waitKey(1) == ord('q'):
        break

drone.end()
cv.destroyAllWindows()