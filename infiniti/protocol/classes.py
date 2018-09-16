from ip_deck_pb2 import DeckSpawn
from utils.db import *
from utils.helpers import *
from infiniti.params import *
import uuid
from Crypto.Random import get_random_bytes
from enum import Enum
"""

All fields of Infiniti objects to be saved to the database should begin with "_"

Issuing a deck requires:
    - A transaction registering a dealer identity
    - A transaction from that dealer spawning the deck 
    - A transaction from the dealer which is a CardTransfer transaction specifying the UUID of the deck which was created

Each object has an active() flag which indicates the confirmation status of the object in the blockchain

TODO:Deck transfer?

"""
class ObjectStatus(Enum):
    UNREGISTERED = 0    # Not found in the blockchain
    MEMPOOL = 1         # In the mempool, but not yet in a block
    PENDING = 2         # In the blockchain, but unconfirmed
    ACTIVE = 3          # Fully confirmed in the blockchain

class Dealer(object):
    def __init__(self,uuid=None):
        if uuid is None:
            self._uuid = uuid.uuid4()
        else:
            self.from_uuid(uuid)

    def from_uuid(self,_uuid):
        self._uuid = _uuid

        data = get_infiniti_object('dealer',self._uuid)
        for k,v in data:
            setattr(self,k,v)

        # Check to see if the dealer address has a registered identity
        if self.active():
            pass

    def register(self):
        """
        Save the Dealer as an Identity on the blockchain as well as the local database

        The "active" flag is set to True when the Dealer appears in the blockchain

        TODO:blockchain

        Saves to DB only
        """

        pass

    def uuid(self):
        return self._uuid
    
    def active(self):
        """
        TODO:blockchain

        Defaults to ObjectStatus.ACTIVE

        Normal operation would be ObjectStatus.UNREGISTERED until the object was entered into
        the blockchain, ObjectStatus.PENDING if the object is unconfirmed, or ObjectStatus.ACTIVE
        if the block containing the message is fully confirmed.
        """
        self._status = ObjectStatus.ACTIVE
        return self._status

    def to_json(self):
        return json.dumps({
            'uuid'          : self._uuid,
            'is_registered' : self.active(),
            'public_key'    : self._public_key,
            'timestamp'     : self._timestamp,
            'rsa_key'       : self._rsa_key,
            'metadata'      : self._metadata,
            })
    
class Deck(object):
    pass