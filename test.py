import pagi_api
import socket
pw = pagi_api.PAGIWorld()
try:
    pw.get_message(block=False)
except socket.timeout:
    pw.get_message(block=True)
pw.disconnect()
