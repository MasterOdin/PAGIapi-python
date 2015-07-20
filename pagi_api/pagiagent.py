from pagi_api.pagihand import PagiHand
from pagi_api.pagiworld import PagiWorld

class PagiAgent(object):
    def __init__(self, pagi_world):
        if not isinstance(pagi_world, PagiWorld):
            raise ValueError("You must pass in a valid PagiWorld variable to PagiAgent")
        self.pagi_world = pagi_world
        self.left_hand = PagiHand('l', pagi_world)
        self.right_hand = PagiHand('r', pagi_world)

    def move_hand(self, hand):
        raise NotImplementedError

    def jump(self):
        raise NotImplementedError

    def reset_agent(self):
        raise NotImplementedError

    def reset_rotation(self):
        raise NotImplementedError

    def rotate(self, val, degrees=True, absolute=True):
        raise NotImplementedError

    def move(self, paces, direction):
        raise NotImplementedError

    def send_force(self, x=0, y=0):
        raise NotImplementedError

    def get_coordinates(self):
        raise NotImplementedError

    def get_periphal_vision(self):
        raise NotImplementedError

    def get_detailed_vision(self):
        raise NotImplementedError

    def center_hands(self):
        raise NotImplementedError
