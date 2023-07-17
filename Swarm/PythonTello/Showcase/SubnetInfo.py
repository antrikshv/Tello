from netaddr import IPNetwork
import itertools

class SubnetInfo(object):
    """
    Subnet information.
    """

    def __init__(self, ip, network, netmask):
        """
        Ctor.
        :param ip: IP.
        :param network: Network.
        :param netmask: Netmask.
        """
        self.ip = ip
        self.network = network
        self.netmask = netmask

    def __repr__(self):
        return f'{self.network} | {self.netmask} | {self.ip}'

    def get_ips(self):
        """
        Gets all the possible IP addresses in the subnet.
        :return: List of IPs.
        """
        def get_quad(ip):
            """
            Gets the third quad.
            :param ip: IP.
            :return: Third quad.
            """
            quads = str(ip).split('.')
            quad = quads[3]
            return quad
        
        def is_valid(ip):
            """
            Checks if IP is valid.
            :return: A boolean indicating if IP is valid.
            """
            quad = get_quad(ip)
            result = False if quad == '0' or quad == '255' else True

            if result:
                if str(ip) == self.ip:
                    result = False
            
            return result

        ip_network = IPNetwork(f'{self.network}/{self.netmask}')

        return [str(ip) for ip in ip_network if is_valid(ip)]

    @staticmethod
    def flatten(infos):
        return list(itertools.chain.from_iterable(infos))