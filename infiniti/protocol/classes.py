from ip_deck_pb2 import DeckSpawn

"""
Deck transfer?
"""

class Deck:

    def from_tx(tx_id):
        self.tx_id = tx_id
        self.tx_confirmations = 0

    def from_uuid(uuid):
        pass

    def is_valid(self):
        """
        Perform a full consensus check
        """
        # Did the TX pay the fee?
        # 

    def serialize(self):
        pass

    def deserialize(self):
        pass

