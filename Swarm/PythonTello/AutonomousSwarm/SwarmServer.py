# from djitellopy import tello
import tools.UdpComms as U
import threading
import queue
import socket
import numpy as np
import yaml

class SwarmServer(object):
    def __init__(self):
        #Read configuration file
        self.serverCfg = self.read_yaml("configuration/pcServerConfig.yml")
        self.dataEncoding = self.serverCfg["dataEncoding"]
        self.buffSize = self.serverCfg["buffsize"]
        self.telloTotal = self.serverCfg["telloTotal"]
        self.baseTelloVidPort = self.serverCfg["rcvTelloVidPort"]
        self.serverIP = self.serverCfg["localip"]
        self.sendCmdPort = self.serverCfg["sendTelloCmdPort"]
        self.SwarmTotal = self.serverCfg["SwarmTotal"]
        self.SwarmCmdFilePaths = self.serverCfg["SwarmCmdFiles"]
        self.baseRaspRespPort = self.serverCfg["rcvTelloRespPort"]
        self.baseAutoRespPort = self.serverCfg["rcvTelloAutoRespPort"]

        #Set up all the ports and misc
        self.pcSock = U.UdpComms(udpIP=self.serverIP, pcIP=self.serverIP, 
                                 portTX=self.serverCfg["sendUnity"], portRX=self.serverCfg["rcvUnity"], 
                                 enableRX=True, suppressWarnings=True)
        self.piSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.unityServer = (self.serverIP, self.serverCfg["sendUnity"])
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
        self.autoRespQ = queue.Queue()
        
        self.raspDroneResponseThread = threading.Thread(target=self.raspDroneResponse)
        self.raspDroneResponseThread.daemon = True
        self.raspDroneResponseThread.start()

    """[RASP-MODE] Main Thread for Comms with Raspberry Servers"""               
    def raspMain(self):
        while True:
            data = self.pcSock.ReadReceivedData()
            if data != None:
                print(data)
                arrData = data.split()
                # if (len(arrData) == 5 or len(arrData) == 1):
                self.broadcast(data)
                # elif (len(arrData) == 6 or len(arrData) == 2):
                #     if (len(arrData) == 6): 
                #         droneIndex = int(arrData[5])
                #         data = arrData[0] + " " + arrData[1] + " " + arrData[2] + " " + arrData[3] + " " + arrData[4]
                #     if (len(arrData) == 2): 
                #         droneIndex = int(arrData[1])
                #         data = arrData[0]
                #     self.piSock.sendto(data.encode(self.dataEncoding), 
                #                        ((self.serverCfg["telloAddr"][droneIndex]), self.sendCmdPort))

    """[RASP-MODE] Thread to check for Response from Rasp Servers
    
    Used to collate the responses from the drones and forward it to the Unity
    """
    def raspDroneResponse(self):
        i = 0
        
        transmission = [None]*self.telloTotal
        raspResp = [None]*self.telloTotal
        while (i < self.telloTotal):
            rcvRaspRespPort = self.baseRaspRespPort + i
            rcvAutoRespPort = self.baseAutoRespPort + i
            raspResp[i] = raspResponse(i, self.serverIP, rcvRaspRespPort, rcvAutoRespPort, 
                                       self.buffSize, self.raspRespQ, self.autoRespQ, self.unityServer)
            transmission[i] = threading.Thread(target=raspResp[i].main)
            transmission[i].daemon = True
            transmission[i].start()
            i+=1
        
        while True:
            if (self.raspRespQ.empty() == False):
                print("here")
                response = self.raspRespQ.get_nowait()
                print(response)
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
    def __init__(self, index, addr, vidport, autoport, buffsize, q, q2, unityServer):
        self.buffSize = buffsize
        self.pcSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,self.buffSize)
        self.auto_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.auto_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,self.buffSize)
        self.vidRecvPort = vidport
        self.autoRecvPort = autoport
        self.vidbindAddr = (addr, self.vidRecvPort)
        self.autobindAddr = (addr, self.autoRecvPort)
        self.client_socket.bind(self.vidbindAddr)
        self.auto_socket.bind(self.autobindAddr)
        print(self.vidbindAddr)
        self.index = str(index)
        self.landQ = q
        self.unityServer = unityServer

    def main(self):
        while True:
            data, ip = self.client_socket.recvfrom(self.buffSize)
            if data != None:
                self.pcSock.sendto(data, self.unityServer)
                print(data)
                # self.landQ.put_nowait(data.decode('utf-8'))

if __name__ == '__main__':
    server = SwarmServer()
    server.raspMain()