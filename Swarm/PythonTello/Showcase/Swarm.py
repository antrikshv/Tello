import sys
import time
from Tello import *
from TelloManager import *
from SwarmUtil import *
import queue
import traceback
import time
import os
import binascii
from contextlib import suppress
import threading

class Swarm(object):
    """
    Tello Edu swarm.
    """

    def __init__(self, fpath):
        """
        Ctor.

        :param fpath: Path to command text file.
        """
        self.fpath = fpath
        self.commands = self._get_commands(fpath)
        self.manager = TelloManager()
        self.tellos = []
        self.pools = []
        self.sn2ip = {
            '0TQZL3PED03A2X': '192.168.10.1',
            '0TQZL3PED03A1T': '10.168.100.226',
            '0TQZL3PED03AG8': '10.168.100.238',
            '0TQZL3PED03A29': '10.168.100.244',
            '0TQZL3FED039AU': '10.168.100.247',
            '0TQZL3PED039MU': '10.168.100.250'
        }
        self.id2sn = {
            0: '0TQZL3PED03A2X',
            1: '0TQZL3PED03A1T',
            2: '0TQZL3PED03AG8',
            3: '0TQZL3PED03A29',
            4: '0TQZL3FED039AU',
            5: '0TQZL3PED039MU'
        }
        self.ip2id = {
            '192.168.10.1': 0,
            '10.168.100.226': 1,
            '10.168.100.238': 2,
            '10.168.100.244': 3,
            '10.168.100.247': 4,
            '10.168.100.250': 5,
        }
        self.cfg = self.read_yaml("configuration/showcaseConfig.yml")
        self.telloIps = self.cfg["SwarmTelloAddr"]

    def start(self):
        """
        Main loop. Starts the swarm.

        :return: None.
        """
        def is_invalid_command(command):
            if command is None:
                return True
            c = command.strip()
            if len(c) == 0:
                return True
            if c == '':
                return True
            if c == '\n':
                return True
            return False
        
        self.checkInputThread = threading.Thread(target=self.check_input)
        self.checkInputThread.daemon = False
        self.checkInputThread.start()
        
        try:
            for command in self.commands:
                if is_invalid_command(command):
                    continue

                command = command.rstrip()

                if '//' in command:
                    self._handle_comments(command)
                elif 'scan' in command:
                    self._handle_scan(command)
                elif '>' in command:
                    self._handle_gte(command)
                elif 'battery_check' in command:
                    self._handle_battery_check(command)
                elif 'delay' in command:
                    self._handle_delay(command)
                elif 'correct_ip' in command:
                    self._handle_correct_ip(command)
                elif '=' in command:
                    self._handle_eq(command)
                elif 'sync' in command:
                    self._handle_sync(command)
            
            self._wait_for_all()
        except KeyboardInterrupt as ki:
            self._handle_keyboard_interrupt()
        except Exception as e:
            self._handle_exception(e)
            traceback.print_exc()
        finally:
            SwarmUtil.save_log(self.manager)

    def check_input(self):
        print("Checking Input")
        while True:
            val = input()
            if (val == 'AI'):
                self.manager.toggle_facetracking(True)
            elif (val == "NAI"):
                self.manager.toggle_facetracking(False)
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


    def _wait_for_all(self):
        """
        Waits for all queues to be empty and for all responses
        to be received.

        :return: None.
        """
        while not SwarmUtil.all_queue_empty(self.pools):
            time.sleep(0.5)
        
        time.sleep(1)

        while not SwarmUtil.all_got_response(self.manager):
            time.sleep(0.5)

    def _get_commands(self, fpath):
        """
        Gets the commands.

        :param fpath: Command file path.
        :return: List of commands.
        """
        with open(fpath, 'r') as f:
            return f.readlines()

    def _handle_comments(self, command):
        """
        Handles comments.

        :param command: Command.
        :return: None.
        """
        print(f'[COMMENT] {command}')

    def _handle_scan(self, command):
        """
        Handles scan.

        :param command: Command.
        :return: None.
        """
        n_tellos = int(command.partition('scan')[2])

        self.manager.connect_predetermined_tello(self.telloIps, n_tellos)
        # self.manager.find_avaliable_tello(n_tellos)
        time.sleep(20)
        self.tellos = self.manager.get_tello_list()
        self.pools = SwarmUtil.create_execution_pools(n_tellos)

        for x, (tello, pool) in enumerate(zip(self.tellos, self.pools)):
            self.ip2id[tello.tello_ip] = x

            t = Thread(target=SwarmUtil.drone_handler, args=(tello, pool))
            t.daemon = True
            t.start()

            print(f'[SCAN] IP = {tello.tello_ip}, ID = {x}')

    def _handle_gte(self, command):
        """
        Handles gte or >.

        :param command: Command.
        :return: None.
        """
        id_list = []
        id = command.partition('>')[0]

        if id == '*':
            id_list = [t for t in range(len(self.tellos))]
        else:
            id_list.append(int(id)) 
        
        action = str(command.partition('>')[2])
        print(action)

        for tello_id in id_list:
            sn = self.id2sn[tello_id]
            ip = self.sn2ip[sn]
            id = self.ip2id[ip]
            
            self.pools[id].put(action)
            print(f'[ACTION] SN = {sn}, IP = {ip}, ID = {id}, ACTION = {action}')

    def _handle_battery_check(self, command):
        """
        Handles battery check. Raises exception if any drone has
        battery life lower than specified threshold in the command.

        :param command: Command.
        :return: None.
        """
        threshold = int(command.partition('battery_check')[2])
        for queue in self.pools:
            queue.put('battery?')

        self._wait_for_all()

        is_low = False

        for log in self.manager.get_last_logs():
            battery = int(log.response)
            drone_ip = log.drone_ip

            print(f'[BATTERY] IP = {drone_ip}, LIFE = {battery}%')

            if battery < threshold:
                is_low = True
        
        if is_low:
            raise Exception('Battery check failed!')
        else:
            print('[BATTERY] Passed battery check')

    def _handle_delay(self, command):
        """
        Handles delay.

        :param command: Command.
        :return: None.
        """
        delay_time = float(command.partition('delay')[2])
        print (f'[DELAY] Start Delay for {delay_time} second')
        time.sleep(delay_time)  

    def _handle_correct_ip(self, command):
        """
        Handles correction of IPs.

        :param command: Command.
        :return: None.
        """
        for queue in self.pools:
            queue.put('sn?') 

        self._wait_for_all()
        
        for log in self.manager.get_last_logs():
            sn = str(log.response)
            tello_ip = str(log.drone_ip)
            self.sn2ip[sn] = tello_ip

            print(f'[CORRECT_IP] SN = {sn}, IP = {tello_ip}')

    def _handle_eq(self, command):
        """
        Handles assignments of IDs to serial numbers.

        :param command: Command.
        :return: None.
        """
        id = int(command.partition('=')[0])
        sn = command.partition('=')[2]
        ip = self.sn2ip[sn]

        self.id2sn[id-1] = sn
        
        print(f'[IP_SN_ID] IP = {ip}, SN = {sn}, ID = {id}')

    def _handle_sync(self, command):
        """
        Handles synchronization.

        :param command: Command.
        :return: None.
        """
        timeout = float(command.partition('sync')[2])
        print(f'[SYNC] Sync for {timeout} seconds')

        time.sleep(1)

        try:
            start = time.time()
            
            while not SwarmUtil.all_queue_empty(self.pools):
                now = time.time()
                if SwarmUtil.check_timeout(start, now, timeout):
                    raise RuntimeError('Sync failed since all queues were not empty!')

            print('[SYNC] All queues empty and all commands sent')
           
            while not SwarmUtil.all_got_response(self.manager):
                now = time.time()
                if SwarmUtil.check_timeout(start, now, timeout):
                    raise RuntimeError('Sync failed since all responses were not received!')
            
            print('[SYNC] All response received')
        except RuntimeError:
            print('[SYNC] Failed to sync; timeout exceeded')

    def _handle_keyboard_interrupt(self):
        """
        Handles keyboard interrupt.

        :param command: Command.
        :return: None.
        """
        print('[QUIT_ALL], KeyboardInterrupt. Sending land to all drones')
        tello_ips = self.manager.tello_ip_list
        for ip in tello_ips:
            self.manager.send_command('land', ip)

    def _handle_exception(self, e):
        """
        Handles exception (not really; just logging to console).

        :param command: Command.
        :return: None.
        """
        print(f'[EXCEPTION], {e}')

    """[TOOL] Read Configuration File"""
    def read_yaml(self, file_path):
        with open(file_path, "r") as f:
            return yaml.safe_load(f)