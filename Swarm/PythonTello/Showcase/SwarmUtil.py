import sys
import time
from Tello import *
from TelloManager import *
import queue
import traceback
import time
import os
import binascii
from contextlib import suppress
import time
class SwarmUtil(object):
    """
    Swarm utility class.
    """

    @staticmethod
    def create_execution_pools(num):
        """
        Creates execution pools.

        :param num: Number of execution pools to create.
        :return: List of Queues.
        """
        return [queue.Queue() for x in range(num)]


    @staticmethod
    def drone_handler(tello, queue):
        """
        Drone handler.

        :param tello: Tello.
        :param queue: Queue.
        :return: None.
        """
        while True:
            while queue.empty():
                pass
            command = queue.get()
            tello.send_command_with_return(command)
            


    @staticmethod
    def all_queue_empty(pools):
        """
        Checks if all queues are empty.

        :param pools: List of Queues.
        :return: Boolean indicating if all queues are empty.
        """
        for queue in pools:
            if not queue.empty():
                return False
        return True


    @staticmethod
    def all_got_response(manager):
        """
        Checks if all responses are received.

        :param manager: TelloManager.
        :return: A boolean indicating if all responses are received.
        """
        for log in manager.get_last_logs():
            if not log.got_response():
                return False
        return True


    @staticmethod
    def create_dir(dpath):
        """
        Creates a directory if it does not exists.

        :param dpath: Directory path.
        :return: None.
        """
        if not os.path.exists(dpath):
            with suppress(Exception):
                os.makedirs(dpath)

    @staticmethod
    def save_log(manager):
        """
        Saves the logs into a file in the ./log directory.

        :param manager: TelloManager.
        :return: None.
        """
        dpath = './log'
        SwarmUtil.create_dir(dpath)

        start_time = str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time())))
        fpath = f'{dpath}/{start_time}.txt'

        with open(fpath, 'w') as out:
            log = manager.get_log()
            for cnt, stats in enumerate(log.values()):
                out.write(f'------\nDrone: {cnt + 1}\n')

                s = [stat.get_stats_delimited() for stat in stats]
                s = '\n'.join(s)

                out.write(f'{s}\n')
        
        print(f'[LOG] Saved log files to {fpath}')


    @staticmethod
    def check_timeout(start_time, end_time, timeout):
        """
        Checks if the duration between the end and start times
        is larger than the specified timeout.

        :param start_time: Start time.
        :param end_time: End time.
        :param timeout: Timeout threshold.
        :return: A boolean indicating if the duration is larger than the specified timeout threshold.
        """
        diff = end_time - start_time
        time.sleep(0.1)
        return diff > timeout