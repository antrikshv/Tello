import subprocess
import ipaddress
from subprocess import Popen, PIPE

ip_net = ipaddress.ip_network(u'10.168.100.1/24', strict=False)


for ip in ip_net.hosts():
    ip = str(ip)
    
    # Ping
    toping = Popen(['ping', '-c', '1', '-W', '50', ip], stdout=PIPE)
    output = toping.communicate()[0]
    hostalive = toping.returncode
    
    if hostalive ==0:
        print(ip, "is online")
    else:
        print(ip, "is offline")