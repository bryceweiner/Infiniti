from ip_deck_pb2 import DeckSpawn
from ip_identity_pb2 import Identity
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

On-wire metadata should consist of a JSON object of any combination of the following fields 
with the following constraints:

real_name : string
organization : string
email : properly formatted email address
image : IPFS CID of image object    

TODO:Deck transfer?

"""
class ObjectStatus(Enum):
    UNREGISTERED = 0    # Not found in the blockchain
    MEMPOOL = 1         # In the mempool, but not yet in a block
    PENDING = 2         # In the blockchain, but unconfirmed
    ACTIVE = 3          # Fully confirmed in the blockchain

class InfinitiObject(object):

    @property
    def object_type(self):
        return self._object_type
    
    @property
    def protobuf_class(self):
        return self._protobuf_class

    def __init__(self):
        if self._uuid is None:
            self._uuid = uuid.uuid4()
            self._block_height = 0
            self._network = NETWORK
            self._tx_id = ''
            self._status = ObjectStatus.UNREGISTERED
            self._fee = params_query(self._network,'Infiniti_fee')
        else:
            self.from_uuid(self._uuid)

    def from_uuid(self,_uuid):
        self._uuid = _uuid

        data = get_infiniti_object('dealer',self._uuid)
        for k,v in data:
            setattr(self,k,v)

        # Check to see if the dealer address has a registered identity
        if self.active():
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

    def is_unique(self):
        """
        Check that the uuid doesn't match a uuid in the database to prevent "object stomping,"
        or trying to claim the object by submitting a new transaction with a uuid which is already
        assigned to an object as a malicious transaction
        """
        # Dealer database
        return not uuid_exists('identity', self._uuid) and 
        # Deck database
            not uuid_exists('decks', self._uuid) and
        # Card database
            not uuid_exists('cards', self._uuid) and
        # Vote datavase 
            not uuid_exists('votes', self._uuid) and
        # Metaproof database
            not uuid_exists('metaproofs', self._uuid) and
        # Claims database
            not uuid_exists('claims', self._uuid)

    def is_ready(self):
        """
        If the object passes consensus validation on the blockchain and the protocol, it's 
        ready to be consumed by applications.
        """
        return self.is_valid() and self.active()

    def creator_is_valid(self):
        """
        Verify the fee was paid to create the Infiniti message 

        Returns True or False
        """
        raise NotImplementedError

    def fee_is_valid(self):
        """
        Verify the fee was paid to create the Infiniti message and that it was 
        greater to or equal than params_query(self._network,'Infiniti_fee')

        Returns True or False
        """
        raise NotImplementedError

    def parse_metadata(self):
        """
        Parse the metadata for the object type 
        """
        raise NotImplementedError

    def register(self):
        """
        Save the Dealer as an Identity on the blockchain as well as the local database

        The "active" flag is set to True when the Dealer appears in the blockchain

        Saves to DB only
        """
        raise NotImplementedError

    def consensus_is_valid(self):
        """
        Per object consensus validator.

        If not needed, still must be overloaded to return True
        """
        raise NotImplementedError

    def is_valid(self):
        """
        Run consensus validation on the object: 

        Returns True or False

        Must implement fee_is_valid nad 
        """
        return self.is_unique() and self.creator_is_valid() and self.fee_is_valid(self) and self.consensus_is_valid()

class Dealer(InfinitiObject):
    """
    A Dealer is an identity object required for Deck spawn operations.

    Dealer objects exist for metadata associations as well as to create light friction for 
    creating Infiniti decks.

    A user only ever needs one Dealer identity to spawn an unlimited number of Infiniti Decks.
    """
    object_type = 'dealer'
    protobuf_class = 'Identity'

    def __init__(self,uuid=None):
        self._uuid = uuid
        super(InfinitiObject,self).__init__()
        if self.block_height == 0: # Impossible, so must be new object
            self._version = 0
            self._public_key = ''
            self._rsa_public_key = ''
            self._metadata = ''
            self._creator = ''  # for a dealer object, the creator is the address which generated the Infiniti
                                # transaction, otherwise it's the uuid of identity object, pubkey must match 
                                # issuer of the deckspan transaction
    def consensus_is_valid(self):
        return True

    def creator_is_valid(self):
        pass

    def fee_is_valid(self):
        """
        TODO:blockchain
        """
        if INFINITI_DEBUG:
            return True
        else:
            return self._fee >= params_query(self._network,'Infiniti_fee')

    def create_metadata(self,real_name,organization,email,img_cid):
        return json.dumps({
            'real_name':real_name[0:100]
            'organization':real_name[0:100]
            'email':real_name[0:100]
            'img_cid':img_cid[0:46]
        })

    def parse_metadata(self):
        return json.loads(self._metadata)

    def register(self):
        """
        TODO:blockchain
        """
        if INFINITI_DEBUG:
            # save to disk only
            pass
        else:
            pass

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
    """
            self._creator = ''  # for a dealer object, the creator is the address which generated the Infiniti
                                # transaction, otherwise it's the uuid of identity object, pubkey must match 
                                # issuer of the deckspan transaction
            self._stxo = '' # This is the transaction hash of the funding transaction from the blockchain txin
                            # for the Infiniti transaction which creates the object, which provides the pubkey 
                            # to validate creator, thereby proving the identity of the dealer is the same 
                            # public key.  If no such TX hash exists, or if the addresses do not match, the 
                            # Dealer object is invalid.

    """
    pass