# from djitellopy import tello
import UdpComms as U
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
import Tello
from ImageReceive import ImageReceive

class Server(object):
    def __init__(self, isVideo, isRouter, isDemo):
        #Read configuration file
        self.serverCfg = self.read_yaml("pcServerConfig.yml")
        self.dataEncoding = self.serverCfg["dataEncoding"]
        self.buffSize = self.serverCfg["buffsize"]
        self.telloTotal = self.serverCfg["telloTotal"]
        self.baseTelloVidPort = self.serverCfg["rcvTelloVidPort"]
        self.serverIP = self.serverCfg["localip"]
        self.sendCmdPort = self.serverCfg["sendTelloCmdPort"]
        self.SwarmTotal = self.serverCfg["SwarmTotal"]
        self.SwarmCmdFilePaths = self.serverCfg["SwarmCmdFiles"]
        self.baseRaspRespPort = self.serverCfg["rcvTelloRespPort"]
        self.printRaspAddr()

        #Set up all the ports and misc
        self.pcSock = U.UdpComms(udpIP=self.serverIP, pcIP=self.serverIP, 
                                 portTX=self.serverCfg["sendUnity"], portRX=self.serverCfg["rcvUnity"], 
                                 enableRX=True, suppressWarnings=True)
        self.piSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # print(self.serverIP)
        # self.sock.bind((self.serverIP, self.serverCfg["rcvUnity"]))
        self.TelloQ = queue.Queue()
        self.command_timeout = .3
        self.abort_flag = False
        self.imperial = False
        self.response = None  
        self.last_height = 0
        self.msgReceived = False
        self.responseQ = queue.Queue()
        self.isShowcase = False
        self.drones = []
        self.takeoff = 0
        self.raspRespQ = queue.Queue()

        #Start threads
        if (isRouter):
            i = 0
            while (i < self.SwarmTotal):
                self.drones.append(Tello.Tello(self.serverCfg["SwarmTelloAddr"][i], 1))
                # print(self.drones[i].address)
                # self.drones[i].connect()
                # print("DRONE BATTERY = " + str(self.drones[i].get_battery()))
                i+=1
            self.checkSwarmDroneStateThread = threading.Thread(target=self.checkSwarmDroneState)
            self.checkSwarmDroneStateThread.daemon = True
            self.checkSwarmDroneStateThread.start()
            # print("routerthread began")
        elif (isVideo):
            self.receiveVideoThread = threading.Thread(target=self.receiveVideoFromRasp)
            self.receiveVideoThread.daemon = True
            self.receiveVideoThread.start()
            self.raspDroneResponseThread = threading.Thread(target=self.raspDroneResponse)
            self.raspDroneResponseThread.daemon = True
            self.raspDroneResponseThread.start()

    """[ROUTER-MODE] Main Thread for Comms with Router"""
    def routerMain(self):
        # self.swarmMon()
        # self.swarmMdirection(0)
        # print("hello")
        while True:
            print("here")
            # data = self.pcSock.ReceiveData()
            data = self.sock.recv(self.buffSize)
            print(data)
            if data != None:
                self.pcSock.SendData("received")
                # data = data.decode('utf8')
                data = data.split() 
                if (len(data) == 1):
                    if (data[0] == "showcase"):
                        self.showcaseThread.start()
                if (len(data) == 5):
                    if (data[4] == '1' and self.takeoff == 0): 
                        self.swarmTakeoff()
                        print("takeoff")
                        self.takeoff = 1
                    elif (data[4] == '-1' and self.takeoff == 1): 
                        self.swarmLand()
                        print("land")
                        self.takeoff = 0
                    elif (data[4] == '0'):
                        self.swarmRC(data)
                        print(data) 
                if (len(data) == 6):
                    if (data[4] == '1' and self.takeoff == 0): 
                        self.drones[int(data[5])].send_command_with_return("takeoff")
                        print("takeoff")
                        self.takeoff = 1
                    elif (data[4] == '-1' and self.takeoff == 1): 
                        self.drones[int(data[5])].send_command_with_return("land")
                        print("land")
                        self.takeoff = 0
                    elif (data[4] == '0'):
                        try:
                            self.drones[int(data[5])].send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
                        except:
                            print("error")
                        print(data) 
    
    """[ROUTER-MODE] Thread to check Land when mission pad detected
    
    Will constantly check for Mission Pad, returns -1 if no Mission pad
    is detected, returns the Mission pad number otherwise
    """
    def checkSwarmDroneState(self):
        while True:
            i = 0
            if (self.takeoff == 1):
                while i < self.SwarmTotal:
                    MpadId = self.drones[i].get_mission_pad_id()
                    if (MpadId != -1):
                        print("we made it")
                        print(MpadId)
                        # self.drones[i].send_command_with_return("go 0 0 0 40 m" + str(MpadId))
                        self.pcSock.SendData(str(i) + " land")
                        self.drones[i].send_command_with_return("land") 
                        self.takeoff = 0  
                    i+=1

    """[ROUTER-MODE] Swarm Command Functions"""
    def swarmMon(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].enable_mission_pads()
            i+=1 
    def swarmMdirection(self, direction):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].set_mission_pad_detection_direction(direction)
            i+=1
    def swarmTakeoff(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_with_return("takeoff")
            i+=1
    def swarmLand(self):
        i = 0
        while i < self.SwarmTotal:
            self.drones[i].send_command_with_return("land")
            i+=1   
    def swarmRC(self, data):
        i = 0
        while i < self.SwarmTotal:
            try:
                self.drones[i].send_rc_control(int(data[0]), int(data[1]), int(data[2]), int(data[3]))
            except:
                print("error")
                # self.drones[i].send_command_with_return("land")
            i+=1

    """[RASP-MODE] Main Thread for Comms with Raspberry Servers"""               
    def raspMain(self):
        while True:
            data = self.pcSock.ReadReceivedData()
            if data != None:
                arrData = data.split()
                if (len(arrData) == 5 or len(arrData) == 1):
                    print(data)
                    self.broadcast(data)
                elif (len(arrData) == 6):
                    droneIndex = int(arrData[5])
                    data = arrData[0] + " " + arrData[1] + " " + arrData[2] + " " + arrData[3] + " " + arrData[4]
                    self.piSock.sendto(data.encode(self.dataEncoding), 
                                       ((self.serverCfg["telloAddr"][droneIndex]), self.sendCmdPort))

    """[RASP-MODE] Thread to get Video Stream from thhe different Rasp Servers
    
    Creates an array of threads which will handle the streaming of 
    Video from all the different Drones in the Swarm
    """
    def receiveVideoFromRasp(self):     
        i = 0
        transmission = [None]*self.telloTotal
        imgClass = [None]*self.telloTotal
        while (i < self.telloTotal):
            rcvTelloVidPort = self.baseTelloVidPort + i
            imgClass[i] = ImageReceive(i, self.serverIP, rcvTelloVidPort, self.buffSize)
            transmission[i] = threading.Thread(target=imgClass[i].main)
            transmission[i].daemon = True
            transmission[i].start()
            print("Waiting for VideoFeed on [Drone:" + str(i) + " - " 
                  + str(self.serverIP) + ", " + str(rcvTelloVidPort) + "]")
            i+=1

    """[RASP-MODE] Thread to check for Response from Rasp Servers
    
    Mainly used as a forwarding thread when the drone detects a mission pad and lands
    so the simulation knows that the mission pad has been detected
    """
    def raspDroneResponse(self):
        i = 0
        transmission = [None]*self.telloTotal
        raspResp = [None]*self.telloTotal
        while (i < self.telloTotal):
            rcvRaspRespPort = self.baseRaspRespPort + i
            raspResp[i] = raspResponse(i, self.serverIP, rcvRaspRespPort, self.buffSize, self.raspRespQ)
            transmission[i] = threading.Thread(target=raspResp[i].main)
            transmission[i].daemon = True
            transmission[i].start()
            i+=1
        while True:
            if (self.raspRespQ.empty() == False):
                response = self.raspRespQ.get_nowait()
                print(response)
                # response = response.split()
                self.pcSock.SendData(response.decode('utf-8'))
                # if (response[1] == "land"):
                #     self.pcSock.SendData(response[0] + " land")

    """[RASP-MODE] Broadcast messages to all Raspberry Pi servers"""
    def broadcast(self, data):
        i = 0
        while i < self.telloTotal:
            self.piSock.sendto(data.encode(self.dataEncoding), 
                               ((self.serverCfg["telloAddr"][i]), self.sendCmdPort))
            i+=1

    """[TOOL] Opens and Reads Commands from file"""
    @staticmethod
    def getCommands(self, fpath):
        with open(fpath, 'r') as f:
            return f.readlines()   
        
    """[TOOL] Read Configuration File"""
    def read_yaml(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    
    """[TOOL] Print All the Raspberru Pi Server Address"""
    def printRaspAddr(self):
        print("Drones Online")
        i = 0
        while (i < self.telloTotal):
            print("[INFO] Drone:" + str(i) + " - " + self.serverCfg["telloAddr"][i] +  ", " + str(self.sendCmdPort))
            i+=1

    """[TOOL] Parses and Executes Command from file
    
    Each Command is in its own seperate line, this function
    Strips and forwards the command to the Tello Drones

    Only for single drones
    """
    @staticmethod
    def executeCmdFile(self, commands, index):
        for command in commands:
            if command != '' and command != '\n':
                command = command.rstrip()
            print("[SENDING] " + command)
            self.showcaseSock.sendto(command.encode(self.dataEncoding),
                                (self.serverCfg["SwarmTelloAddr"][index], self.serverCfg["SwarmPort"]))
            self.waitDroneResponse(self, index)

class raspResponse(object):
    def __init__(self, index, addr, port, buffsize, q):
        self.buffSize = buffsize
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,self.buffSize)
        self.recvPort = port
        self.bindAddr = (addr, self.recvPort)
        self.client_socket.bind(self.bindAddr)
        self.index = str(index)
        self.landQ = q
    
    def main(self):
        while True:
            data, ip = self.client_socket.recvfrom(self.buffSize)
            print(data)
            if data != None:
                self.landQ.put_nowait(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--router", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if (args.video == True and args.router == True):
        print("[ERROR] Cannot use Video in router mode!")
    else:
        print("Server starting up...")
        server = Server(args.video, args.router, args.demo)
        if (args.video == True):
            server.raspMain()
        else:
            server.routerMain()