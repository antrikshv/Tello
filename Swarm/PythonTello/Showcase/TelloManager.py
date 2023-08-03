import threading
from threading import Thread
import socket
import time
import netifaces
import netaddr
from netaddr import IPNetwork
from collections import defaultdict
import binascii
from datetime import datetime
import itertools
from Stats import *
from SubnetInfo import *
from Tello import *
import yaml
import tools.TelloTools as TelloClient
import cv2
import numpy as np
import math
import asyncio
# import tensorflow
# from cvzone.HandTrackingModule import HandDetector
# from cvzone.ClassificationModule import Classifier

class TelloManager(object):
    """
    Tello Manager.
    """

    def __init__(self):
        """
        Ctor.
        """
        self.local_ip = ''
        self.local_port = 8889
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.local_ip, self.local_port))

        # thread for receiving cmd ack
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.tello_ip_list = []
        self.tello_list = []
        self.log = defaultdict(list)

        self.COMMAND_TIME_OUT = 20.0

        self.last_response_index = {}
        self.str_cmd_index = {}
        self.isFaceTracking = False
        self.offset = 20
        self.imgSize = 300
        self.index = 0
        self.labels = ["Misc","Land","Formation"]

        

    def read_yaml(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    
    def toggle_facetracking(self, bool):
        self.isFaceTracking = bool
        print("[INFO] FaceTracking Status is set to: " + str(self.isFaceTracking))
        
    def find_avaliable_tello(self, num):
        """
        Find Tellos.
        :param num: Number of Tellos to search.
        :return: None
        """
        possible_ips = self.get_possible_ips()

        print(f'[SEARCHING], Searching for {num} from {len(possible_ips)} possible IP addresses')

        iters = 0

        while len(self.tello_ip_list) < num:
            print(f'[SEARCHING], Trying to find Tellos, number of tries = {iters + 1}')

            # delete already found Tello
            for tello_ip in self.tello_ip_list:
                if tello_ip in possible_ips:
                    possible_ips.remove(tello_ip)

            # skip server itself
            for ip in possible_ips:
                cmd_id = len(self.log[ip])
                self.log[ip].append(Stats('command', cmd_id))

                # print(f'{iters}: sending command to {ip}:8889')

                try:
                    self.socket.sendto(b'command', (ip, 8889))
                except:
                    print(f'{iters}: ERROR: {ip}:8889')
                    pass

            iters = iters + 1
            time.sleep(5)

        # filter out non-tello addresses in log
        temp = defaultdict(list)
        for ip in self.tello_ip_list:
            temp[ip] = self.log[ip]
        self.log = temp
    
    def connect_predetermined_tello(self, telloIps, n_tellos):
        i = 0
        err = False
        while (i < n_tellos):
            self.tello_list.append(TelloClient.Tello(telloIps[i], 1))
            self.tello_list[i].send_command_with_return("command")
            time.sleep(2)
            try:
                print("DRONE BATTERY = " + str(self.tello_list[i].get_battery()))
            except Exception as e:
                err = True
                print(e)
            if (err == True):
                print("DRONE BATTERY = " + str(self.tello_list[i].get_battery()))
                
            i+=1
        
        # self.me = Tello.Tello(self.cfg["telloip"], 1)
        # self.me.send_command_with_return("command")
        # self.tello_list[0].send_command_with_return("streamon")

        # self.displayVideoThread = threading.Thread(target=self.displayVideo)
        # self.displayVideoThread.daemon = False
        # self.displayVideoThread.start()
    
    def displayVideo(self):
        print("[INFO] Starting Video Stream")
        face_cascade = cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')
        # self.detector = HandDetector(maxHands=1)
        # self.classifier = Classifier("HandSignalModel/keras_model.h5","HandSignalModel/labels.txt")
        while True:
            try:
                frame = self.tello_list[0].get_frame_read().frame
                if (self.isFaceTracking):
                    # hands, img = self.detector.findHands(frame)
                    # if hands:
                    #     hand = hands[0]
                    #     xh,yh,wh,hh = hand['bbox']
                    #     imgCrop = img[yh-self.offset:yh+hh+self.offset, xh-self.offset:xh+wh+self.offset]
                    #     asyncio.run(self.processImg(imgCrop, hh, wh))
                    cap = self.tello_list[0].get_video_capture()

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
                    cv2.putText(img, self.labels[self.index], (10, 50),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,255),2)
                    cv2.putText(frame, f'[{offset_x}, {offset_y}, {z_area}]', (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2, cv2.LINE_AA)
                    self.adjust_tello_position(offset_x, offset_y, z_area)
                    
                cv2.imshow('TELLO VIDEO',frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                
            except:
                pass
    
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
        self.tello_list[0].send_rc_control(0, -offset_z, -offset_y, offset_x)

    # async def processImg(self, imgCrop, h, w):   
    #     print("processing hand")
    #     aspectRatio = h/w
    #     imgWhite = np.ones((self.imgSize,self.imgSize,3),np.uint8)*255
    #     if aspectRatio>1:
    #         k = self.imgSize/h
    #         wCal = math.ceil(k*w)
    #         imgResize = cv2.resize(imgCrop, (wCal, self.imgSize))
    #         wGap = math.ceil((self.imgSize-wCal)/2)
    #         imgWhite[:,wGap:wCal+wGap] = imgResize
    #         pred, self.index = self.classifier.getPrediction(imgWhite)
    #     else:
    #         k = self.imgSize/w
    #         hCal = math.ceil(k*h)
    #         imgResize = cv2.resize(imgCrop, (self.imgSize, hCal))
    #         hGap = math.ceil((self.imgSize-hCal)/2)
    #         imgWhite[hGap:hCal+hGap,:] = imgResize
    #         pred, self.index = self.classifier.getPrediction(imgWhite)
    #     # if (self.index == 1 and self.takeoff == 1):
    #     #     self.autoLanding = 1
    #     #     self.takeoff = 0
    #         # self.drones[0].send_command_without_return("land")
    #         # self.swarmLand()
    #     # cv2.imshow("ImageCrop", imgWhite)
        
    def get_possible_ips(self):
        """
        Gets all the possible IP addresses for subnets that the computer is a part of.
        :return: List of IP addresses.
        """
        infos = self.get_subnets()
        ips = SubnetInfo.flatten([info.get_ips() for info in infos])
        ips = list(filter(lambda ip: ip.startswith('10.168.100.'), ips))
        return ips

    def get_subnets(self):
        """
        Gets all subnet information.

        :return: List of subnet information.
        """
        infos = []

        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)

            if socket.AF_INET not in addrs:
                continue

            # Get ipv4 stuff
            ipinfo = addrs[socket.AF_INET][0]
            address, netmask = ipinfo['addr'], ipinfo['netmask']

            # limit range of search. This will work for router subnets
            if netmask != '255.255.255.0':
                continue

            # Create ip object and get
            cidr = netaddr.IPNetwork(f'{address}/{netmask}')
            network = cidr.network

            info = SubnetInfo(address, network, netmask)
            infos.append(info)

        return infos

    def get_tello_list(self):
        return self.tello_list

    def send_command(self, command, ip):
        """
        Sends a command to the IP address. Will be blocked until the last command receives an 'OK'.
        If the command fails (either b/c time out or error),  will try to resend the command.

        :param command: Command.
        :param ip: Tello IP.
        :return: Response.
        """
        #global cmd
        command_sof_1 = ord(command[0])
        command_sof_2 = ord(command[1])

        if command_sof_1 == 0x52 and command_sof_2 == 0x65:
            multi_cmd_send_flag = True
        else :
            multi_cmd_send_flag = False

        if multi_cmd_send_flag == True:      
            self.str_cmd_index[ip] = self.str_cmd_index[ip] + 1
            for num in range(1,5):                
                str_cmd_index_h = self.str_cmd_index[ip] / 128 + 1
                str_cmd_index_l = self.str_cmd_index[ip] % 128
                if str_cmd_index_l == 0:
                    str_cmd_index_l = str_cmd_index_l + 2
                cmd_sof = [0x52, 0x65, str_cmd_index_h, str_cmd_index_l, 0x01, num + 1, 0x20]
                cmd_sof_str = str(bytearray(cmd_sof))
                cmd = cmd_sof_str + command[3:]
                self.socket.sendto(cmd.encode('utf-8'), (ip, 8889))

            print(f'[MULTI_COMMAND], IP={ip}, COMMAND={command[3:]}')
            real_command = command[3:]
        else:
            time.sleep(0.5)
            self.socket.sendto(command.encode('utf-8'), (ip, 8889))
            print(f'[SINGLE_COMMAND] IP={ip}, COMMAND={command}')
            real_command = command
        
        self.log[ip].append(Stats(real_command, len(self.log[ip])))
        start = time.time()

        while not self.log[ip][-1].got_response():
            now = time.time()
            diff = now - start
            if diff > self.COMMAND_TIME_OUT:
                print(f'[NO_RESPONSE] Max timeout exceeded for command: {real_command}')
                return    

    def _receive_thread(self):
        """
        Listen to responses from the Tello.
        Runs as a thread, sets self.response to whatever the Tello last returned.

        :return: None.
        """
        while True:
            try:
                response, ip = self.socket.recvfrom(1024)
                response = response.decode('utf-8')
                self.response = response
                
                ip = ''.join(str(ip[0]))                
                
                if self.response.upper() == 'OK' and ip not in self.tello_ip_list:
                    self.tello_ip_list.append(ip)
                    self.last_response_index[ip] = 100
                    self.tello_list.append(Tello(ip, self))
                    self.str_cmd_index[ip] = 1
                
                response_sof_part1 = ord(self.response[0])               
                response_sof_part2 = ord(self.response[1])

                if response_sof_part1 == 0x52 and response_sof_part2 == 0x65:
                    response_index = ord(self.response[3])
                    
                    if response_index != self.last_response_index[ip]:
                        print(f'[MULTI_RESPONSE], IP={ip}, RESPONSE={self.response[7:]}')
                        self.log[ip][-1].add_response(self.response[7:], ip)
                    self.last_response_index[ip] = response_index
                else:
                    # print(f'[SINGLE_RESPONSE], IP={ip}, RESPONSE={self.response}')
                    self.log[ip][-1].add_response(self.response, ip)
                         
            except socket.error as exc:
                # swallow exception
                # print "[Exception_Error]Caught exception socket.error : %s\n" % exc
                pass

    def get_log(self):
        """
        Get all logs.
        :return: Dictionary of logs.
        """
        return self.log

    def get_last_logs(self):
        """
        Gets the last logs.
        :return: List of last logs.
        """
        return [log[-1] for log in self.log.values()]