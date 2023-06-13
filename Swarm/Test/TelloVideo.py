import socket
from threading import Thread
import time
import cv2
from typing import Optional, Union, Type, Dict
import numpy as np


LOCALIP = "192.168.8.100"
LOCALPORT = 11112

drones: Optional[dict] = {}

class PCServer(object):
    def __init__(self):
        self.piAddr = (LOCALIP, LOCALPORT)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((LOCALIP, LOCALPORT))   
        # self.cap: Optional[cv2.VideoCapture] = None
        self.background_frame_read: Optional['BackgroundFrameRead'] = None

    def get_frame_read(self) -> 'BackgroundFrameRead':
        """Get the BackgroundFrameRead object from the camera drone. Then, you just need to call
        backgroundFrameRead.frame to get the actual frame received by the drone.
        Returns:
            BackgroundFrameRead
        """
        if self.background_frame_read is None:
            address = self.piAddr
            self.background_frame_read = BackgroundFrameRead(self)  # also sets self.cap
            self.background_frame_read.start()
        return self.background_frame_read 
    
    def _receive_video_thread(self):
        """
        Listens for video streaming (raw h264) from the Tello.

        Runs as a thread, sets self.frame to the most recent frame Tello captured.

        """
        packet_data = b""
        while True:
            try:
                res_string, ip = self.socket.recvfrom(2048)
                packet_data += res_string
                # end of frame
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                        print(type(frame))
                    packet_data = ""

            except socket.error as exc:
                print ("Caught exception socket.error : %s" % exc)
    
    def _h264_decode(self, packet_data):
        """
        decode raw h264 format data from Tello
        
        :param packet_data: raw h264 data array
       
        :return: a list of decoded frame
        """
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                # print 'frame size %i bytes, w %i, h %i, linesize %i' % (len(frame), w, h, ls)

                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
                frame = (frame.reshape((h, ls / 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    # def receiveVideo(self):
    #     # packet_data = ""
    #     print("started")
    #     # address = 'udp://@0.0.0.0:11112'
    #     # videoCapture = cv2.VideoCapture(address)
    #     # if not videoCapture.isOpened():
    #     #     videoCapture.open(address)
    #     print("cv2 ready")
    #     while True:
    #         try:
    #             # print("waiting for video")
    #             # _, frame = videoCapture.read()
    #             # # img = self.get_frame_read().frame
    #             # print(_)
    #             # print(frame)
    #             # frame = cv2.resize(frame, (360,240))
    #             # cv2.imshow("TelloFootage", frame)
    #             # cv2.waitKey(1)
    #             # print("listening on " + LOCALIP)
    #             res_string = self.socket.recvfrom(2048)
    #             imgArr = np.frombuffer(res_string,np.uint8)
    #             img = cv2.imdecode(imgArr, cv2.IMREAD_COLOR)
    #             if type(img) is type(None):
    #                 print("img type is None")
    #                 pass
    #             else:
    #                 cv2.imshow("Video Stream", img)
    #                 cv2.waitKey(1)
    #             # print(f"{res_string} and {ip}")
    #             # packet_data += res_string
    #             # self.sendPCQ.put_nowait(res_string)
    #             # print()
    #             # # end of frame
    #             # if len(res_string) != 1460:
    #             #     # for frame in self._h264_decode(packet_data):
    #             #     #     self.frame = frame
    #             #     packet_data = ""

    #         except socket.error as exc:
    #             print ("Caught exception socket.error : %s" % exc)

class BackgroundFrameRead:
    """
    This class read frames from a VideoCapture in background. Use
    backgroundFrameRead.frame to get the current frame.
    """

    def __init__(self, tello):
        address = 'udp://@192.168.8.100:11112'
        tello.cap = cv2.VideoCapture(address)

        self.cap = tello.cap

        if not self.cap.isOpened():
            self.cap.open(address)

        # Try grabbing a frame multiple times
        # According to issue #90 the decoder might need some time
        # https://github.com/damiafuentes/DJITelloPy/issues/90#issuecomment-855458905
        start = time.time()
        while time.time() - start < 3:
            # Tello.LOGGER.debug('trying to grab a frame...')
            self.grabbed, self.frame = self.cap.read()
            if self.frame is not None:
                break
            time.sleep(0.05)

        if not self.grabbed or self.frame is None:
            raise Exception('Failed to grab first frame from video stream')

        self.stopped = False
        self.worker = Thread(target=self.update_frame, args=(), daemon=True)

    def start(self):
        """Start the frame update worker
        Internal method, you normally wouldn't call this yourself.
        """
        self.worker.start()
        print("Thread Began")

    def update_frame(self):
        """Thread worker function to retrieve frames from a VideoCapture
        Internal method, you normally wouldn't call this yourself.
        """
        while not self.stopped:
            if not self.grabbed or not self.cap.isOpened():
                self.stop()
            else:
                self.grabbed, self.frame = self.cap.read()
                print(self.grabbed)

    def stop(self):
        """Stop the frame update worker
        Internal method, you normally wouldn't call this yourself.
        """
        self.stopped = True
        self.worker.join()

if __name__ == '__main__':
    server = PCServer()
    print("starting")
    server._receive_video_thread()
