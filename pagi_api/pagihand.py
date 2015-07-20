class PagiHand(object):
    def __init__(self, hand, pagi_world):
        PagiHand.check_hand(hand)
        self.hand = hand.upper()
        self.pagi_world = pagi_world

    def get_position(self):
        raise NotImplementedError

    def get_coordinates(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    def grab(self):
        raise NotImplementedError

    def send_force(self, x, y):
        raise NotImplementedError

    @staticmethod
    def check_hand(hand):
        """
        Check if given hand value is left or right, and if neither, raise ValueError

        :param hand:
        :return:
        """
        if not hand.upper() == 'R' and not hand.upper == 'L':
            raise ValueError("You can only use a L or R value for hands")