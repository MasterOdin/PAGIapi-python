"""
Python PAGIworld API
"""
__author__ = "Matthew Peveler"
__copyright__ = "Copyright 2015, RAIR Lab"
__credits__ = ["Matthew Peveler"]
__license__ = "MIT"

import math
import os
import socket
import time

ERROR_CHECK = True

VALID_COMMANDS = ["sensorRequest", "addForce", "loadTask", "print", "findObj", "setState",
                  "getActiveStates", "setReflex", "removeReflex", "getActiveReflexes"]

VALID_SENSORS = ["S", "BP", "LP", "RP", "A", "MDN", "MPN"]
for i in range(5):
    VALID_SENSORS.append("L%d" % i)
    VALID_SENSORS.append("R%d" % i)
for i in range(0, 31):
    for j in range(0, 21):
        VALID_SENSORS.append("V%d.%d" % (i, j))
for i in range(0, 16):
    for j in range(0, 11):
        VALID_SENSORS.append("P%d.%d" % (i, j))

VALID_FORCES = ["RHvec", "LHvec", "BMvec", "RHH", "LHH", "RHV", "LHV", "BMH", "BMV", "J", "BR",
                "RHG", "LHG", "RHR", "LHR"]

# pylint: disable=too-many-instance-attributes
class PAGIWorld(object):
    """
    :type pagi_socket: socket.socket
    :type __ip_address: str
    :type __port: int
    :type __timeout: float
    :type __message_fragment: str
    :type __task_file: str
    :type message_stack: list
    """
    def __init__(self, ip_address="", port=42209, timeout=3):
        """

        :param ip:
        :param port:
        :return:
        """
        self.pagi_socket = None
        self.__ip_address = ip_address
        self.__port = port
        self.__timeout = timeout
        self.__message_fragment = ""
        self.__task_file = ""
        self.message_stack = list()
        self.connect(ip_address, port, timeout)
        self.agent = PAGIAgent(self)

    def connect(self, ip_address="", port=42209, timeout=3):
        """
        Create a socket to the given

        :param ip:
        :param port:
        :return:
        :raises: ConnectionRefusedError
        """
        if ip_address == "":
            ip_address = socket.gethostbyname(socket.gethostname())
        self.__ip_address = ip_address
        self.__port = port
        self.__timeout = timeout
        self.__message_fragment = ""
        self.__task_file = ""
        self.message_stack = list()
        self.pagi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pagi_socket.connect((ip_address, port))
        self.pagi_socket.setblocking(False)
        self.pagi_socket.settimeout(timeout)

    def disconnect(self):
        """
        Close the socket to PAGIWorld and then reset internal variables (in case we just use
        connect directly without creating new PAGIWorld instance)

        :return:
        """
        self.pagi_socket.close()

    def __assert_open_socket(self):
        """
        Make sure that we have an existing socket connection. If we don't, exception will be raised.
        :return:
        :raises: RuntimeError
        """
        if self.pagi_socket is None:
            raise RuntimeError("No open socket. Use connect() to open a new socket connection")

    def send_message(self, message):
        """
        Send a message to the socket. We make sure that the message is a valid action type, as well
        verify that if the message is for a sensor or action, that it's a valid sensor or action
        to prevent bad calls.

        :param message:
        :type message: str
        :return:
        :raises: RuntimeError
        """
        self.__assert_open_socket()
        if ERROR_CHECK:
            command = message[:message.find(",")]
            if command == "" or command not in VALID_COMMANDS:
                raise RuntimeError("Invalid command found in the message '%s'" % message)

            end = message[len(command)+1:].find(",")
            if end == -1:
                secondary = message[len(command)+1:]
            else:
                secondary = message[len(command)+1:end + len(command) + 1]
            if command == "sensorRequest" and secondary not in VALID_SENSORS:
                raise RuntimeError("Invalid sensor '%s' in message '%s'" % (secondary, message))
            elif command == "addForce" and secondary not in VALID_FORCES:
                raise RuntimeError("Invalid force '%s' in message '%s'" % (secondary, message))

        # all messages must end with \n
        if message[-1] != "\n":
            message += "\n"
        self.pagi_socket.send(message.encode())

    def get_message(self, code="", block=False):
        """
        Gets messages from the socket. If code is blank, then we just return the first message
        from the socket, otherwise return the first matching message with that code, saving all
        other messages to a stack. If block is set to False, and there's no response from the
        socket, after self.__timeout seconds, function will raise socket.timeout exception. If
        block is set to true, no exception will be thrown, but program will stop in this function
        if socket doesn't return anything

        :param code:
        :type code: str
        :param block:
        :type block: bool
        :return:
        :raises: socket.timeout
        """
        if block:
            self.pagi_socket.setblocking(True)
        response = self.__get_message_from_stack(code)
        while True and response != "":
            while "\n" not in self.__message_fragment:
                self.__message_fragment += self.pagi_socket.recv(4096).decode()
            message_index = self.__message_fragment.find("\n")
            if message_index == -1:
                break
            else:
                response = self.__message_fragment[:message_index]
                self.__message_fragment = self.__message_fragment[message_index+1:]
                if code == "" or (response[:len(code)] == code and response[len(code)] == ","):
                    break
                else:
                    self.message_stack.append(response)
        if block:
            self.pagi_socket.setblocking(False)
            self.pagi_socket.settimeout(self.__timeout)
        return response

    def __get_message_from_stack(self, code):
        """
        Attempts to return a message from the stack if (1) the stack isn't empty and (2) either
        code is blank or it matches something on the message stack
        :param code:
        :return: str
        """
        if len(self.message_stack) > 0:
            if code != "":
                for index in range(len(self.message_stack)):
                    if self.message_stack[index][:len(code)] == code and \
                            self.message_stack[index][len(code)] == ",":
                        return self.message_stack.pop(0)
                return None
            else:
                return self.message_stack.pop(0)

    def load_task(self, task_file):
        """
        Loads a task in PAGIworld. We additionally save the task file name so we can reset things
        if necessary
        :param task_file:
        :type task_file: str
        :raises: FileNotFoundError
        """
        if not os.path.isfile(task_file):
            raise RuntimeError("Task file at '%s' was not found" % task_file)
        self.__task_file = task_file
        self.send_message("loadTask,%s" % task_file)

    def reset_task(self):
        """
        Resets the task to the one that was loaded in self.load_task. If one wasn't loaded, then
        a RuntimeError will be raised.
        :raises: RuntimeError
        """
        if self.__task_file == "" or self.__task_file is None:
            raise RuntimeError("Cannot reset task, no previous task file found")
        self.load_task(self.__task_file)

    def print_text(self, text):
        """
        Print text to the PAGIworld console window.
        :param text:
        :type text: str
        :return:
        """
        text = str(text)
        self.send_message("print,%s" % text)
        self.get_message(code="print")

    def set_state(self, name, length):
        """
        Set a state within PAGIworld.
        :param name:
        :type name: str
        :param length:
        :type length: int
        :return:
        """
        self.send_message("setState,%s,%d" % (name, length))
        self.get_message(code="setState")

    def remove_state(self, name):
        """
        "Removes" states from PAGIworld by just setting it's duration to zero (so that can't ever
        really be in a state)
        :param name:
        :return:
        """
        self.send_message("setState,%s,0" % name)
        self.get_message(code="setState")

    def get_all_states(self):
        """
        Returns a list of all states that are currently in PAGIworld.
        :return: list
        """
        self.send_message("getActiveStates")
        states = self.get_message(code="activeStates").split(",")
        return states[1:]

    def set_reflex(self, name, conditions, actions=None):
        """
        Sets a reflex in PAGIworld to be carried out on conditions.
        :param name:
        :param conditions:
        :param actions:
        :return:
        """
        if actions is not None:
            self.send_message("setReflex,%s,%s,%s" % (name, conditions, actions))
        else:
            self.send_message("setReflex,%s,%s" % (name, conditions))
        self.get_message(code="setReflex")

    def remove_reflex(self, name):
        """
        Removes a reflex completely from PAGIworld
        :param name:
        :return:
        """
        self.send_message("removeReflex,%s" % name)
        self.get_message(code="removeReflex")

    def get_all_reflexes(self):
        """
        Returns a list of all the active reflexes in PAGIworld
        :return: list
        """
        self.send_message("getActiveReflexes")
        reflexes = self.get_message(code="activeReflexes").split(",")
        return reflexes[1:]

    def drop_item(self, name, x_coord, y_coord, description=None):
        """
        Creates an item and drops into into PAGIworld. These items are the ones pre-built into
        PAGIworld.
        :param name:
        :param x:
        :param y:
        :param n:
        :return:
        """
        if description is None or description == "":
            self.send_message("dropItem,%s,%f,%f" % (name, x_coord, y_coord))
        else:
            self.send_message("dropItem,%s,%f,%f,%s" % (name, x_coord, y_coord, description))
        self.get_message(code="dropItem")

    # pylint: disable=too-many-arguments
    def create_item(self, name, image_file, x, y, m, ph, r, e, k, degrees=True):
        """
        Creates a new item in PAGIworld with the specified properties

        :param name:
        :param image_file:
        :param x:
        :param y:
        :param m:
        :param ph:
        :param r:
        :param e:
        :param k:
        :param degrees:
        :return:
        """
        if degrees:
            r = r * math.pi / 180.
        self.send_message("createItem,%s,%s,%f,%f,%f,%d,%f,%f,%d" % (name, image_file,
                                                                     x, y, m, ph, r, e, k))
        self.get_message(code="createItem")

class PAGIAgent(object):
    """
    PAGIAgent

    :type pagi_world: PAGIWorld
    :type left_hand: PAGIAgentHand
    :type right_hand: PAGIAgentHand
    """
    def __init__(self, pagi_world):
        if not isinstance(pagi_world, PAGIWorld):
            raise ValueError("You must pass in a valid PagiWorld variable to PagiAgent")
        self.pagi_world = pagi_world
        self.left_hand = PAGIAgentHand('l', pagi_world)
        self.right_hand = PAGIAgentHand('r', pagi_world)

    def jump(self):
        """
        Causes the agent to try and jump. He will only be able to if his bottom edge is touching
        something solid, otherwise he'll do nothing.

        :return: bool True if agent has jumped (his bottom is touching something solid) otherwise
                        False
        """
        self.pagi_world.send_message("addForce,J,1000")
        response = self.pagi_world.get_message(code="J").split(",")
        return int(response[1]) == 1

    def reset_agent(self):
        """
        Resets agent state back to a starting position (looking upward with hands in starting
        position)
        :return:
        """
        self.reset_rotation()

    def reset_rotation(self):
        """
        Resets the agent's rotation back to 0 degrees (looking upward)
        :return:
        """
        self.rotate(0, absolute=True)

    def rotate(self, val, degrees=True, absolute=False):
        """
        Rotate the agent some number of degrees/radians. If absolute is True, then we rotate to
        position specified from 0 (looking up), otherwise rotate him relative to where he's looking.

        Therefore, if he's looking down at 180 degrees, and we tell him to rotate 90 degrees, if
        absolute is True, he'll be looking to the left at 90 degrees and if absolute is False,
        he'll be looking to the right at 270 degrees

              0
        90  agent  270
             180
        :param val:
        :type val: float
        :param degrees:
        :type degrees: bool
        :param absolute:
        :type absolute: bool
        :return:
        """
        if not degrees:
            val = val * 180. / math.pi
        if absolute:
            val %= 360.
            val -= self.get_rotation()
        self.pagi_world.send_message("addForce,BR,%f" % val)
        self.pagi_world.get_message(code="BR")

    def get_rotation(self, degrees=True):
        """
        Returns rotation in either degrees (0 - 359) or radians (0 - 2*pi) of agent (0 is looking
        upward)

        :param degrees:
        :type degrees: bool
        :return:
        """
        self.pagi_world.send_message("sensorRequest,A")
        response = self.pagi_world.get_message(code="A").split(",")
        rotation = float(response[-1])
        rotation %= 360
        if degrees:
            rotation = rotation * 180 / math.pi
        return rotation

    def move_paces(self, paces, direction='L'):
        """
        Attempts to move the agent some number of paces (defined as one width of his body) to
        either the left or right.

        :param paces:
        :type paces: int
        :param direction:
        :type direction: str
        :return:
        """
        assert_left_or_right(direction)
        val = 1 if direction[0].upper() == "R" else -1
        cnt = 0
        while cnt < paces:
            self.send_force(x=(val * 1000), absolute=True)
            time.sleep(2)
            cnt += 1

    def send_force(self, x=0, y=0, absolute=False):
        """
        Sends a vector force to the agent to move his body. If absolute is False, then vectors are
        relative to the direction agent is looking, thus +y is always in direction of top of agent,
        -y is bottom, +x is towards his right side, -x is his left side. If absolute is true, then
        vector +y is world up, -y is world bottom, +x is world right and -x is world left.

        :param x:
        :type x: float
        :param y:
        :type y: float
        :param absolute:
        :type absolute: bool
        :return:
        """
        x = float(x)
        y = float(y)
        if not absolute or (x == 0 and y == 0):
            self.pagi_world.send_message("addForce,BMvec,%f,%f" % (x, y))
        else:
            rotation = self.get_rotation()
            if x != 0 and y != 0:
                ax = math.fabs(x)
                ay = math.fabs(y)
                hyp = math.sqrt(ax ** 2 + ay ** 2)
                angle = math.acos(ay / hyp)
                z = math.sin(angle) * ay
            else:
                if x != 0:
                    z = math.fabs(x)
                else:
                    z = math.fabs(y)
            nx, ny = PAGIAgent.__get_relative_vector(x, y, z, rotation)
            print(nx, ny)
            self.pagi_world.send_message("addForce,BMvec,%f,%f" % (nx, ny))

        self.pagi_world.get_message(code="BMvec")

    @staticmethod
    def __get_relative_vector(x, y, z, rotation):
        """
        TODO: Finish and simplify

        :param x:
        :param y:
        :param z:
        :param rotation:
        :return:
        """
        if x == 0:
            if y < 0:
                angle = 180
            else:
                angle = 0
        elif y == 0:
            if x > 0:
                angle = 270
            else:
                angle = 90
        elif x < 0:
            if y > 0:
                angle = math.acos(z / y) * 180 / math.pi
            else:
                angle = math.acos(z / x) * 180 / math.pi + 90
        else:
            if y < 0:
                angle = math.acos(z / y) * 180 / math.pi + 180
            else:
                angle = math.acos(z / x) * 180 / math.pi + 270

        adjusted = rotation - angle
        radjusted = adjusted * math.pi / 180
        if adjusted == 0:
            return 0, z
        elif adjusted == 180 or adjusted == -180:
            return 0, (-1 * z)
        elif adjusted == 90 or adjusted == -270:
            return z, 0
        elif adjusted == 270 or adjusted == -90:
            return (-1 * z), 0
        else:
            if adjusted > 0:
                if adjusted < 90:
                    ny = math.cos(radjusted) * z
                    nx = math.sqrt(math.pow(z, 2) - math.pow(ny, 2))
                elif adjusted < 180:
                    nx = math.cos(radjusted - 90) * z
                    ny = math.sqrt(math.pow(z, 2) - math.pow(nx, 2)) * -1
                elif adjusted < 270:
                    ny = math.cos(radjusted - 180) * z * -1
                    nx = math.sqrt(math.pow(z, 2) - math.pow(ny, 2)) * -1
                else:
                    nx = math.cos(radjusted - 270) * z * -1
                    ny = math.sqrt(math.pow(z, 2) - math.pow(nx, 2))
            else:
                if adjusted < -90:
                    ny = math.cos(radjusted * -1) * z
                    nx = math.sqrt(math.pow(z, 2) - math.pow(ny, 2)) * -1
                elif adjusted < -180:
                    nx = math.cos(radjusted * -1 - 90) * z * -1
                    ny = math.sqrt(math.pow(z, 2) - math.pow(nx, 2)) * -1
                elif adjusted < -270:
                    ny = math.cos(radjusted * -1 - 180) * z * -1
                    nx = math.sqrt(math.pow(z, 2) - math.pow(ny, 2))
                else:
                    nx = math.cos(radjusted * -1 - 270) * z
                    ny = math.sqrt(math.pow(z, 2) - math.pow(nx, 2))
            return nx, ny

    def get_position(self):
        """
        Gets x/y coordinates of the agent in the world
        :return: tuple(float, float) of coordinates of agent
        """
        self.pagi_world.send_message("sensorRequest,BP")
        response = self.pagi_world.get_message(code="BP").split(",")
        return float(response[1]), float(response[2])

    def get_periphal_vision(self):
        """
        Returns a list of 11 (rows) x 16 (columns) points which contains all of his periphal vision.
        vision[0][0] represents lower left of the vision field with vision[10][15] representing
        upper right
        :return: list of size 11 x 16
        """
        self.pagi_world.send_message("sensorRequest,MPN")
        response = self.pagi_world.get_message(code="MPN").split(",")
        return self.__process_vision(response, 16)

    def get_detailed_vision(self):
        """
        Returns a list of ?x? points which contains all of his detailed vision
        :return:
        """
        self.pagi_world.send_message("sensorRequest,MDN")
        response = self.pagi_world.get_message(code="MDN").split(",")
        return self.__process_vision(response, 21)

    @staticmethod
    def __process_vision(response, column_length):
        """
        Internal method to process returned vision repsonse. Splits the response into a list of
        lists where each inner list is the length of specified column_length.
        :param response:
        :param column_length:
        :return:
        """
        vision = list()
        current = list()
        for j in range(1, len(response)):
            if (j - 1) % column_length == 0:
                if len(current) > 0:
                    vision.append(current)
                current = list()
            current.append(response[j])
        vision.append(current)
        return vision

    def center_hands(self):
        """
        Moves both of the agent's hands to the center of his body
        :return:
        """
        raise NotImplementedError

class PAGIAgentHand(object):
    """
    :type pagi_world: PAGIWorld
    """
    def __init__(self, hand, pagi_world):
        assert_left_or_right(hand)
        self.hand = hand[0].upper()
        self.pagi_world = pagi_world

    def get_position(self):
        """
        Gets the position of the hand relative to the agent
        :return: tupe(float, float) of the x, y coordinates of the hand
        """
        self.pagi_world.send_message("sensorRequest,%sP" % self.hand)
        response = self.pagi_world.get_message(code=("%sP" % self.hand)).split(",")
        return float(response[1]), float(response[2])

    def release(self):
        """
        Opens the hand, releasing anything it could be holding
        :return:
        """
        self.pagi_world.send_message("%sHR" % self.hand)
        self.pagi_world.get_message(code="%sHR" % self.hand)

    def grab(self):
        """
        Closes the hand, grabbing anything it is touching
        :return:
        """
        self.pagi_world.send_message("%sHG" % self.hand)
        self.pagi_world.get_message(code="%sHG" % self.hand)

    def send_force(self, x, y, absolute=False):
        """
        Sends a vector of force to the hand moving it
        :param x:
        :type x: float
        :param y:
        :type y: float
        :param absolute:
        :type absolute: bool
        :return:
        """
        if not absolute:
            self.pagi_world.send_message("%sHvec,%f,%f" % (self.hand, x, y))
        else:
            pass
        self.pagi_world.get_message(code="%sHvec" % self.hand)

def assert_left_or_right(direction):
    """
    Checks that the given direction is either left or right, and if it isn't, raise exception

    :param direction:
    :return:
    """
    if not direction.upper() == 'R' and not direction.upper() == 'L' \
            and not direction.upper() == 'RIGHT' and not direction.upper() == 'LEFT':
        raise ValueError("You can only use a L or R value for hands")
