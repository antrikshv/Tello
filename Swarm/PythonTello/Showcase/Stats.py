from datetime import datetime

class Stats(object):
    """
    Statistics
    """

    def __init__(self, command, id):
        """
        Ctor.
        :param command: Command.
        :param id: ID.
        """
        self.command = command
        self.response = None
        self.id = id

        self.start_time = datetime.now()
        self.end_time = None
        self.duration = None
        self.drone_ip = None

    def add_response(self, response, ip):
        """
        Adds a response.
        :param response: Response.
        :param ip: IP address.
        :return: None.
        """
        if self.response == None:
            self.response = response
            self.end_time = datetime.now()
            self.duration = self.get_duration()
            self.drone_ip = ip

    def get_duration(self):
        """
        Gets the duration.
        :return: Duration (seconds).
        """
        diff = self.end_time - self.start_time
        return diff.total_seconds()

    def print_stats(self):
        """
        Prints statistics.
        :return: None.
        """
        print(self.get_stats())

    def got_response(self):
        """
        Checks if response was received.
        :return: A boolean indicating if response was received.
        """
        return False if self.response is None else True

    def get_stats(self):
        """
        Gets the statistics.
        :return: Statistics.
        """
        return {
            'id': self.id,
            'command': self.command,
            'response': self.response,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration
        }

    def get_stats_delimited(self):
        stats = self.get_stats()
        keys = ['id', 'command', 'response', 'start_time', 'end_time', 'duration']
        vals = [f'{k}={stats[k]}' for k in keys]
        vals = ', '.join(vals)
        return vals

    def __repr__(self):
        return self.get_stats_delimited()