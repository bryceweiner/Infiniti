from ip_deck_pb2 import DeckSpawn
from utils.db import *
from utils.helpers import *
from infiniti.params import *
import uuid
from Crypto.Random import get_random_bytes
"""
Deck transfer?
"""
class Dealer:
    def __init__(self):
        self._uuid = uuid.uuid4()

    def from_uuid(self,_uuid):
        self._uuid = _uuid

        db = get_key('dealer',self.uuid)
        # Check to see if the dealer address has a registered identity
        if self.is_registered():
            pass

    def register(self):
        """
        Save the Dealer as an Identity on the blockchain
        """
        pass

    @property
    def uuid(self):
        return self._uuid
    
    @property
    def is_registered(self):
        return self._is_registered

    def to_json(self):
        return json.dumps({
            'uuid'          : self.uuid,
            'is_registered' : self.is_registered,
            'public_key'    : self.public_key,
            'timestamp'     : self.timestamp,
            })
    
class Deck:

    def from_uuid(uuid):
        self.tx_id = 0
        self.timestamp = 0
        self.dealer = 0
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

