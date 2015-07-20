import socket

from pagi_api.pagiagent import PagiAgent

class PagiWorld(object):
    """
    :type pagi_socket: socket.socket
    :type __message_fragment: str
    """
    def __init__(self, ip_address, port=44209):
        """

        :param ip:
        :param port:
        :return:
        """
        self.pagi_socket = None
        self.__message_fragment = ""
        self.connect(ip_address, port)
        self.agent = PagiAgent(self)

    def connect(self, ip_address, port=44209):
        """
        Create a socket to the given

        :param ip:
        :param port:
        :return:
        """
        self.pagi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pagi_socket.connect((ip_address, port))
        self.pagi_socket.setblocking(False)

    def disconnect(self):
        self.pagi_socket.close()
        self.pagi_socket = None
        self.__message_fragment = ""

    def __assert_open_socket(self):
        """
        Make sure we are operating on an existing socket connection
        :return:
        """
        if self.pagi_socket is None:
            raise RuntimeError("No open socket. Use connect() to open a new socket connection")

    def send_message(self, message):
        """
        Send a message to the socket

        :param message:
        :return:
        """
        self.__assert_open_socket()
        # all messages must end with \n
        if message[-1] != "\n":
            message += "\n"

        self.pagi_socket.send(message)

    def get_message(self, block=True):
        """
        Returns the first available message from the socket. By default will block till we get a
        whole response from the socket

        :param block:
        :return:
        """
        if block:
            while "\n" not in self.__message_fragment:
                self.__message_fragment += self.pagi_socket.recv(4096)
        else:
            self.__message_fragment += self.pagi_socket.recv(4096)
        message_index = self.__message_fragment.find("\n")
        if message_index == -1:
            return ""
        else:
            response = self.__message_fragment[:message_index]
            self.__message_fragment = self.__message_fragment[message_index+1:]
            return response

