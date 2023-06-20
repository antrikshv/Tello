import cv2, imutils, socket
import numpy as np
import time
import base64
import sys

class ImageReceive(object):
	def __init__(self, index, addr, port, buffsize):
		self.buffSize = buffsize
		self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,self.buffSize)
		self.recvPort = port
		self.bindAddr = (addr, self.recvPort)
		self.client_socket.bind(self.bindAddr)
		self.index = str(index)

	def main(self):
		fps,st,frames_to_count,cnt = (0,0,20,0)
		while True:
			packet,_ = self.client_socket.recvfrom(self.buffSize)
			data = base64.b64decode(packet,' /')
			npdata = np.frombuffer(data,dtype=np.uint8)
			frame = cv2.imdecode(npdata,1)
			# frame = cv2.putText(frame,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
			cv2.imshow(self.index,frame)
			key = cv2.waitKey(1) & 0xFF
			if key == ord('q'):
				self.client_socket.close()
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
    index = int(sys.argv[1])
    server = ImageReceive(index)
    server.main()