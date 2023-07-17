import socket
import threading
recvDroneRespSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recvDroneRespSock.bind(("", 8889))
# receiveDroneRespThread = threading.Thread(target=receiveDroneResponse)
# receiveDroneRespThread.daemon = True
# receiveDroneRespThread.start()
while True:
    resp = recvDroneRespSock.recvfrom(1024)
    print("[DRONE RESP]" + str(resp))