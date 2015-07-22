import pagi_api

pw = pagi_api.PAGIWorld()
a = pw.agent.get_detailed_vision()
pw.disconnect()
