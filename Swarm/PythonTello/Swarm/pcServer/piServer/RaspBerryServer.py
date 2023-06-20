from djitellopy import tello
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

class RaspBerryServer(object):
    def __init__(self):
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverRespSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.telloCmdSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cfg = self.read_yaml("piServerConfig.yml")
        self.buffSize = self.cfg["buffsize"]
        self.telloAddr = (self.cfg["telloip"], self.cfg["rcvTelloCmdPort"])
        self.serverAddr = (self.cfg["serverip"], self.cfg["sendTelloVidPort"] + self.cfg["index"])
        self.serverRespAddr = (self.cfg["serverip"], self.cfg["sendTelloRespPort"] + self.cfg["index"])
        print("Server Addr - " + str(self.serverAddr))
        print("Waiting for commands on " + str(self.telloAddr))
        self.telloCmdSocket.bind(self.telloAddr)
        
        self.me = tello.Tello()
        self.me.connect()
        print(self.me.get_battery())
        self.me.streamon()
        self.me.enable_mission_pads()
        self.me.set_mission_pad_detection_direction(0)
        
        
        print(self.serverAddr)
        self.TelloQ = queue.Queue()
        self.command_timeout = .3
        self.abort_flag = False
        self.imperial = False
        self.response = None  
        self.last_height = 0
        self.takeoff = 0

        self.receiveVideoThread = threading.Thread(target=self.receiveVideo)
        self.receiveVideoThread.daemon = True
        self.receiveVideoThread.start()
        self.checkSwarmDroneStateThread = threading.Thread(target=self.checkSwarmDroneState)
        self.checkSwarmDroneStateThread.daemon = True
        self.checkSwarmDroneStateThread.start()

        # self.sendCoordThread = threading.Thread(target=self.sendCoord)
        # self.sendCoordThread.daemon = True
        # self.sendCoordThread.start()

        # self.showcaseThread = threading.Thread(target=self.showcase)
        # self.showcaseThread.daemon = True
    
    def checkSwarmDroneState(self):
        MpadId = -1
        while True:
            if (self.takeoff == 1):
                MpadId = self.me.get_mission_pad_id()
                if (MpadId != -1):
                    print(MpadId)
                    print("we made it")
                    # self.drones[i].send_command_with_return("go 0 0 0 40 m" + str(MpadId))
                    self.serverRespSock.sendto((str(self.cfg["index"]) + " land").encode('utf-8'), self.serverRespAddr)
                    self.me.land()
                    self.takeoff = 0  
    
    def sendCoord(self):
        while True:
            pitch = self.me.get_pitch()
            roll = self.me.get_roll()
            yaw = self.me.get_yaw()
            throttle = self.me.get_height()
            print("Pitch: " + str(pitch) + "\n" + 
                "Roll: " + str(roll) + "\n" +
                "Yaw: " + str(yaw) + "\n" +
                "Throttle: " + str(throttle))

    def showcase(self):
        commands = self.getCommands(self, self.SwarmCmdFilePaths[0])
        for command in commands:
            if command != '' and command != '\n':
                command = command.rstrip()
            command = command.split()
            if (command[0] == "takeoff"): self.me.takeoff()
            elif (command[0] == "land"): self.me.land()
            elif (command[0] == "up"): self.me.move_up(int(command[1]))  
            elif (command[0] == "go"): self.me.go_xyz_speed_mid(int(command[1]), int(command[2]), int(command[3]), int(command[4]), int(command[5]))

    def getCommands(self, fpath):
        with open(fpath, 'r') as f:
            return f.readlines()

    def read_yaml(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def main(self):
        self.takeoff = 0
        land = 1
        cam = 1
        while True:
            data,_ = self.telloCmdSocket.recvfrom(self.buffSize)
            if data != None: 
                print(data)
                data = data.decode('utf8')
                data = data.split() 
                if (len(data) == 1):
                    if (data[0] == "switchCam"):
                        print("switchCam")
                        self.me.send_command_with_return("downvision " + str(cam))
                        cam = 0 if cam == 1 else 1
                if (len(data) == 5):
                    if (data[4] == '1' and self.takeoff == 0): 
                        self.me.takeoff()
                        print("takeoff")
                        self.takeoff = 1
                    elif (data[4] == '-1' and self.takeoff == 1): 
                        self.me.land()
                        print("land")
                        self.takeoff = 0
                    elif (data[4] == '0'):
                        try:
                            self.me.send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                        except:
                            print("error")
                        print(data) 
                
    def receiveVideo(self):     
        fps,st,frames_to_count,cnt = (0,0,20,0)
        while True:
            # print("acceleration_x = " + str(self.me.get_acceleration_x()))
            img = self.me.get_frame_read().frame
            img = cv2.resize(img, (360, 240))
            encoded,buffer = cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,80])
            message = base64.b64encode(buffer)
            self.serverSock.sendto(message,self.serverAddr)
            frame = cv2.putText(img,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            cv2.imshow('TRANSMITTING VIDEO',frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                self.serverSock.close()
                break
            if cnt == frames_to_count:
                try:
                    fps = round(frames_to_count/(time.time()-st))
                    st=time.time()
                    cnt=0
                except:
                    pass
            cnt+=1

if __name__ == '__main__':
    print("Server starting up...")
    server = RaspBerryServer()
    server.main()