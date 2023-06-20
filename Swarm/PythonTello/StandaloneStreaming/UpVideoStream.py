import TelloVideo
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
        self.telloCmdSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cfg = self.read_yaml("VideoStreamConfig.yml")
        self.buffSize = self.cfg["buffsize"]
        self.telloAddr = (self.cfg["serverip"], self.cfg["rcvTelloCmdPort"])
        self.serverAddr = (self.cfg["serverip"], self.cfg["sendTelloVidPort"] + self.cfg["index"])
        self.serverRespAddr = (self.cfg["serverip"], self.cfg["sendTelloRespPort"] + self.cfg["index"])
        self.telloCmdSocket.bind(self.telloAddr)
        
        self.me = TelloVideo.Tello(self.cfg["telloip"], 1)
        self.me.send_command_without_return("command")
        self.me.send_command_without_return("streamon")
        print("[INFO] Starting Video Stream")
        
        self.command_timeout = .3
        self.abort_flag = False
        self.imperial = False
        self.response = None  
        self.last_height = 0

        self.receiveVideoThread = threading.Thread(target=self.receiveVideo)
        self.receiveVideoThread.daemon = True
        self.receiveVideoThread.start()
        # self.processVideoThread = threading.Thread(target=self.processVideoThread)
        # self.processVideoThread.daemon = True
        # self.processVideoThread.start()

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
                        self.me.send_command_without_return("downvision " + str(cam))
                        cam = 0 if cam == 1 else 1
                if (len(data) == 5):
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
    
    def receiveVideo(self):     
        fps,st,frames_to_count,cnt = (0,0,20,0)
        while True:
            try:
                img = self.me.get_frame_read().frame
                cv2.imshow('TELLO VIDEO',img)
                key = cv2.waitKey(1) & 0xFF
            except:
                pass
    
    # def processVideo(self, img):
    #     cv2.imshow('TELLO VIDEO',img)

if __name__ == '__main__':
    server = RaspBerryServer()
    server.main()