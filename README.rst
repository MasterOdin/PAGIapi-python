PAGIapi-python
==============

This repository contains code to help with interacting with `PAGI World <https://github.com/RespeckKnuckles/PAGIworld>`_.

Usage
-----
Basic Usage::

    from pagi_api.pagiworld import PagiWorld
    pw = PagiWorld(IP_ADDRESS, PORT)
    pw.send_message("command")
    message = pw.receive_message()
