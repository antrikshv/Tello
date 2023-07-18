import tools.TelloTools as Tello
import time
import threading
import queue
import socket
import cv2
import numpy as np
import time
import base64
import imutils
import yaml
import argparse
import math
import asyncio
import tensorflow
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier

class TelloClient(object):
    def __init__(self, standalone, server):
        #Read the Configurations
        self.cfg = self.read_yaml("configuration/VideoStreamConfig.yml")
        self.buffSize = self.cfg["buffsize"]
        self.telloAddr = (self.cfg["serverip"], self.cfg["rcvTelloCmdPort"])
        self.serverAddr = (self.cfg["serverip"], self.cfg["sendTelloVidPort"] + self.cfg["index"])
        self.serverRespAddr = (self.cfg["serverip"], self.cfg["sendTelloRespPort"] + self.cfg["index"])
        self.SwarmTotal = self.cfg["SwarmTotal"]
        self.fpath = self.cfg["fpath"]
        self.commands = self._get_commands(self.fpath)
        self.countSwarmRCerr = 0

        #Establish Connection with the Tello Drones directly for standalone or server mode
        if (standalone):
            err = False
            i = 0
            self.drones = []
            self.dronesFlight = []
            print("here")
            while (i < self.SwarmTotal):
                self.drones.append(Tello.Tello(self.cfg["SwarmTelloAddr"][i], 1))
                self.dronesFlight.append(False)
                self.drones[i].send_command_with_return("command")
                time.sleep(2)
                try:
                    print("[SETUP] Drone " + str(i) + " Battery Level = " + str(self.drones[i].get_battery()))
                except Exception as e:
                    err = True
                    print(e)
                if (err == True):
                    print("[SETUP] Drone " + str(i) + " Battery Level = " + str(self.drones[i].get_battery()))
                    
                i+=1
            
            self.drones[0].send_command_with_return("streamon")
            print("[INFO] Starting Video Stream")
            
            #Start Mission Pad downward detection
            self.swarmMon()
            self.swarmMdirection(0)

        elif (server):
            self.me = Tello.Tello(self.cfg["SwarmTelloAddr"][0], 1)
            self.me.send_command_with_return("command")
            time.sleep(2)
            try:
                print("[SETUP] Drone 0 Battery Level = " + str(self.me.get_battery()))
            except Exception as e:
                err = True
                print(e)
            if (err == True):
                print("[SETUP] Drone 0 Battery Level = " + str(self.me.get_battery()))
            
            #Start the socket if talking to SwarmServer
            self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.telloCmdSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.telloCmdSocket.bind(self.telloAddr)
        
        #Set flags and Misc
        self.command_timeout = .3
        self.abort_flag = False
        self.imperial = False
        self.response = None  
        self.last_height = 0
        self.takeoffCount = 0
        
        self.isStandalone = standalone
        self.isServer = server
        
        #Set Parameters for AI
        self.autonomous = False
        self.prevmsg = "0 0 0 0"
        self.labels = ["Misc","Land","Formation"]
        self.offset = 20
        self.imgSize = 300
        self.index = 0
        self.autoLanding = 0
        self.face_cascade = cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')
        self.detector = HandDetector(maxHands=1)
        self.classifier = Classifier("HandSignalModel/keras_model.h5","HandSignalModel/labels.txt")     
        
    """[TOOL] Opens and Reads Commands from file"""
    def _get_commands(self, fpath):      
        with open(fpath, 'r') as f:
            return f.readlines()

    """[TOOL] Read Configuration File"""
    def read_yaml(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    
    """[Server/Standalone Mode] Main thread used to handle commands received from Unity Game Engine
        or from external Python server sending Joystick Data
    fac"""
    def main(self):
        self.takeoff = 0
        cam = 1
        if (self.isServer):
            #Start Video Forwarding Thread
            self.receiveVideoThread = threading.Thread(target=self.receiveVideo)
            self.receiveVideoThread.daemon = True
            self.receiveVideoThread.start()

            #Loop to listen for Commands
            while True:
                data,_ = self.telloCmdSocket.recvfrom(self.buffSize)
                if data != None: 
                    print(data)
                    data = data.decode('utf8')
                    data = data.split() 
                    if (len(data) == 1):
                        if (data[0] == "switchCam"):
                            print("switchCam")
                            self.me.send_command_without_return("downvision " + str(cam))
                            cam = 0 if cam == 1 else 1
                    elif (len(data) == 5):
                        if (data[4] == '1' and self.takeoff == 0): 
                            self.me.send_command_without_return("takeoff")
                            print("takeoff")
                            self.takeoff = 1
                        elif (data[4] == '-1' and self.takeoff == 1): 
                            self.me.send_command_without_return("land")
                            print("land")
                            self.takeoff = 0
                        elif (data[4] == '0'):
                            try:
                                self.me.send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                            except:
                                print("error")
                            print(data)
              
        elif (self.isStandalone):
            self.displayVideoThread = threading.Thread(target=self.displayVideo)
            self.displayVideoThread.daemon = True
            self.displayVideoThread.start()

            i = 0
            while True:
                val = input("[INPUT] Key Commands:")
                if val == "start":
                    i = 0
                    while i < self.SwarmTotal:
                        if (self.drones[i].get_mission_pad_id() != -1):
                            self.drones[i].send_command_without_return("land")
                        i+=1 
                    try:
                        for command in self.commands:
                            command = command.rstrip()
                            if '>' in command:
                                
                                self._handle_gte(command)
                            elif 'delay' in command:
                                self._handle_delay(command)
                    except Exception as e:
                        print(e)
                elif val == "AI":
                    self.autonomous = True
                elif (val == "0"):
                    self._handle_gte("0>land")
                elif (val == "1"):
                    self._handle_gte("1>land")
                elif (val == "2"):
                    self._handle_gte("2>land")
                elif (val == "3"):
                    self._handle_gte("3>land")
                elif (val == "4"):
                    self._handle_gte("4>land")

        elif (self.isServer and self.isStandalone):
            data,_ = self.telloCmdSocket.recvfrom(self.buffSize)
            if data != None: 
                print(data)
                data = data.decode('utf8')
                data = data.split() 
                if (len(data) == 1 or len(data) == 2):
                    if (data[0] == "switchCam"):
                        print("switchCam")
                        self.drones[0].send_command_without_return("downvision " + str(cam))
                        cam = 0 if cam == 1 else 1
                    if (data[0] == "Autonomous"):
                        print("autonomous")
                        self.autonomous = True
                    if (data[0] == "RC"):
                        print("rc")
                        self.autonomous = False
                elif (len(data) == 5):
                    if (data[4] == '1' and self.takeoff == 0):
                        # if (self.takeoffCount == 0):
                        #     self.takeOffRoutine()
                        #     self.takeoffCount+=1
                        # else: 
                        self.drones[0].send_command_without_return("takeoff")
                        self.dronesFlight[0] = True
                        self.swarmTakeoff()
                        print("takeoff")
                        self.takeoff = 1
                        self.autoLanding = 0
                    elif (data[4] == '-1' and self.takeoff == 1): 
                        self.drones[0].send_command_without_return("land")
                        self.dronesFlight[0] = False
                        self.swarmLand()
                        print("land")
                        self.takeoff = 0
                    elif (data[4] == '0'):
                        try:
                            self.drones[0].send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                            self.swarmRC(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                        except:
                            print("error")
                        print(data) 
                elif (len(data) == 6):
                    droneIndex = int(data[5])
                    if (data[4] == '1' and self.takeoff == 0): 
                        self.drones[droneIndex].send_command_without_return("takeoff")
                        self.dronesFlight[droneIndex] = True
                        print("takeoff")
                        self.takeoff = 1
                    elif (data[4] == '-1' and self.takeoff == 1): 
                        self.drones[droneIndex].send_command_without_return("land")
                        self.dronesFlight[droneIndex] = False
                        print("land")
                        self.takeoff = 0
                    elif (data[4] == '0'):
                        try:
                            self.drones[droneIndex].send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                        except:
                            print("error")
    
    """[TOOLS] Tools to broadcast specific messages to multiple Tello Drones"""
    def startKeepAlive(self):
        while True:
            print("Here Alive")
            i=0
            while (i < self.SwarmTotal):
                if (self.dronesFlight[i]):
                    self.drones[i].send_command_without_return("command")
                    print(i)
                    i+=1
                    time.sleep(5)       
    def swarmMon(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].enable_mission_pads()
            i+=1 
    def swarmMdirection(self, direction):
        i = 1
        while i < self.SwarmTotal:
            self.drones[i].set_mission_pad_detection_direction(direction)
            i+=1
    def swarmTakeoff(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return("takeoff")
            self.dronesFlight[i] = True
            i+=1
    def swarmLand(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return("land")
            self.dronesFlight[i] = False
            i+=1   
    def swarmDownvision(self, cam):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return("downvision " + str(cam))
            i+=1  
    def swarmRC(self, roll, pitch, throttle, yaw):
        i = 0
        while i < 3:
            try:
                self.drones[i].send_rc_control(roll, pitch, throttle, yaw)
            except:
                if (self.countSwarmRCerr == 0):
                    print("no swarm drones")
                    self.countSwarmRCerr+=1
                else:
                    pass
                
                # self.drones[i].send_command_with_return("land")
            i+=1
    def swarmForward(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def swarmBack(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def swarmUp(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def swarmDown(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def swarmRight(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def swarmLeft(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    def broadcast(self, message):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_without_return(message)
            self.dronesFlight[i] = True
            i+=1
    
    """[Server Mode] Receives Video Footage, reduces the scale, displays and forwards
        to the main Server (to be used on a PI connected to the drone)
        Will forward the video data, for the main computer to process the facetracking
    """          
    def receiveVideo(self):     
        fps,st,frames_to_count,cnt = (0,0,20,0)
        while True:
            try:
                img = self.me.get_frame_read().frame
                img = cv2.resize(img, (720, 480))
                encoded,buffer = cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,80])
                message = base64.b64encode(buffer)
                self.serverSock.sendto(message,self.serverAddr)
                # frame = cv2.
                # frame = cv2.putText(img,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                # cv2.imshow('TELLO VIDEO',img)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                if cnt == frames_to_count:
                    try:
                        fps = round(frames_to_count/(time.time()-st))
                        st=time.time()
                        cnt=0
                    except:
                        pass
                cnt+=1
            except:
                pass
    
    """[Standalone Mode] Receives and Displays Video Footage
        Also processes the facetracking here if needed.
    """
    def displayVideo(self):     
        while True:
            try:
                frame = self.drones[0].get_frame_read().frame
                if (self.autonomous):
                    hands, img = self.detector.findHands(frame)
                    if hands:
                        hand = hands[0]
                        xh,yh,wh,hh = hand['bbox']
                        imgCrop = img[yh-self.offset:yh+hh+self.offset, xh-self.offset:xh+wh+self.offset]
                        aspectRatio = h/w
                        imgWhite = np.ones((self.imgSize,self.imgSize,3),np.uint8)*255
                        if aspectRatio>1:
                            k = self.imgSize/h
                            wCal = math.ceil(k*w)
                            imgResize = cv2.resize(imgCrop, (wCal, self.imgSize))
                            wGap = math.ceil((self.imgSize-wCal)/2)
                            imgWhite[:,wGap:wCal+wGap] = imgResize
                            pred, self.index = self.classifier.getPrediction(imgWhite)
                        else:
                            k = self.imgSize/w
                            hCal = math.ceil(k*h)
                            imgResize = cv2.resize(imgCrop, (self.imgSize, hCal))
                            hGap = math.ceil((self.imgSize-hCal)/2)
                            imgWhite[hGap:hCal+hGap,:] = imgResize
                            pred, self.index = self.classifier.getPrediction(imgWhite)
                        
                        # asyncio.run(self.processImg(imgCrop, hh, wh))
                    cap = self.drones[0].get_video_capture()

                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    center_x = int(width/2)
                    center_y = int(height/3)

                    cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0))
                    
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)
                    
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
                    cv2.putText(img, self.labels[self.index], (10, 50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),2)
                    cv2.putText(frame, f'[{offset_x}, {offset_y}, {z_area}]', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2, cv2.LINE_AA)
                    self.adjust_tello_position(offset_x, offset_y, z_area)
                    
                cv2.imshow('TELLO VIDEO',frame)
                cv2.waitKey(1)
                
            except:
                pass
    
    """[TOOLS] Handles Hand Gesture Identification"""
    async def processImg(self, imgCrop, h, w):   
        aspectRatio = h/w
        imgWhite = np.ones((self.imgSize,self.imgSize,3),np.uint8)*255
        if aspectRatio>1:
            k = self.imgSize/h
            wCal = math.ceil(k*w)
            imgResize = cv2.resize(imgCrop, (wCal, self.imgSize))
            wGap = math.ceil((self.imgSize-wCal)/2)
            imgWhite[:,wGap:wCal+wGap] = imgResize
            pred, self.index = self.classifier.getPrediction(imgWhite)
        else:
            k = self.imgSize/w
            hCal = math.ceil(k*h)
            imgResize = cv2.resize(imgCrop, (self.imgSize, hCal))
            hGap = math.ceil((self.imgSize-hCal)/2)
            imgWhite[hGap:hCal+hGap,:] = imgResize
            pred, self.index = self.classifier.getPrediction(imgWhite)
        if (self.index == 1 and self.takeoff == 1):
            self.autoLanding = 1
            self.takeoff = 0
            self.drones[0].send_command_without_return("land")
            self.swarmLand()
        #cv2.imshow("ImageCrop", imgWhite)

    """[TOOLS] Adjusts the Tello Position for Face Tracking"""
    def adjust_tello_position(self, offset_x, offset_y, offset_z):
        if not -90 <= offset_x <= 90 and offset_x is not 0:
            offset_x = offset_x/8
        else:
            offset_x = 0
        if not -50 <= offset_y <= 50 and offset_y is not -30:
            offset_y = offset_y/7
        else:
            offset_y = 0
        if not 15000 <= offset_z <= 25000 and offset_z is not 0:
            offset_z = ((offset_z-20000)/900)
        else:
            offset_z = 0
        # if(self.autoLanding == 0):
        if (self.index == 1):
            print("landing")
            self.autoLanding = 1
            self.drones[1].send_command_without_return("land")
            self.drones[2].send_command_without_return("land")
            self.drones[0].send_command_with_return("land")
        elif (self.autoLanding == 0):
            self.drones[0].send_rc_control(0, -offset_z, -offset_y, offset_x)
            self.swarmRC(0, -offset_z, -offset_y, offset_x)
            # message = str(0) + " " + str(-offset_z) + " " + str(-offset_y) + " " + str(offset_x)
            # if (self.prevmsg != message):
            #     self.serverSock.sendto(message.encode('utf-8'), ("192.168.56.1", 8000))
            #     self.prevmsg = message

    """[TOOLS] Parses the movement commands in the txt file for showcase"""
    def _handle_gte(self, command):
        id_list = []
        id = command.partition('>')[0]
        action = str(command.partition('>')[2])
        details = action.split()
        if id == '*':
            print("here: " + action)
            self.broadcast(action)
            self.drones[0].send_command_with_return(action)
        else:
            self.drones[int(id)].send_command_without_return(action)
        print("[INFO] Command Sent: " + command)
        # time.sleep(4)

    """[TOOLS] Processes the delay for the delay commands in the txt file for showcase"""
    def _handle_delay(self, command):
        delay_time = float(command.partition('delay')[2])
        print (f'[DELAY] Start Delay for {delay_time} second')
        time.sleep(delay_time)  

    """[TOOLS] Handles Keyboard interrupt for showcase"""
    def _handle_keyboard_interrupt(self):
        print('[QUIT_ALL], KeyboardInterrupt. Sending land to all drones')
        # tello_ips = self.manager.tello_ip_list
        # for ip in tello_ips:
        #     self.manager.send_command('land', ip)

    """[TOOLS] Function to print Exceptions"""
    def _handle_exception(self, e):
        print(f'[EXCEPTION], {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--standalone", action="store_true")
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()
    print("here")
    if (args.standalone == True and args.server == True):
        print("[ERROR] Only use one mode [--standalone or --server]!")
    elif (args.standalone == False and args.server == False):
        print("[ERROR] Please define your mode [--standalone or --server]!")
    else:
        print("[INFO] Starting up!")
        server = TelloClient(args.standalone, args.server)
        server.main()