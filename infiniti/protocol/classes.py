from ip_deck_pb2 import DeckSpawn

class IssueMode(Enum):

    NONE = 0x00     # No issuance allowed.
    CUSTOM = 0x01   # Custom issue mode, verified by client aware of this.
    ONCE = 0x02     # A single card_issue transaction allowed.
    MULTI = 0x04    # Multiple card_issue transactions allowed.
    MONO = 0x08     # All card transaction amounts are equal to 1.
    SINGLETON = 0x18    # Initial CardTransfer is serialized, maximum number 
                        # of Initial CardTransfers (by amount). (ONCE | MULTI)

class Identity:
    def __init__(self, version, uuid, public_key, rsa_public_key, metadata):
        self.version = version
        self.uuid = uuid
        self.public_key = public_key
        self.rsa_public_key = rsa_public_key
        self.metadata = metadata

class Deck:
    def __init__(self, name, version, uuid, num_decimals, production, asset_data,
                    issue_mode, fee, dealer, tx_confirmations, tx_id ):
        self.name = name
        self.version = version
        self.uuid = uuid 
        self.num_decimals = num_decimals
        self.production = production
        self.asset_data = asset_data
        self.issue_mode = issue_mode
        self.fee - fee
        self.issuer = issuer
        self.tx_confirmations = tx_confirmations
        self.tx_id = tx_id

    def from_tx(tx_id):
        """
        Load a deck spawn from a transaction ID
        """
        pass

class CardTransafer:
    def __init__(self, version, amount, uuid, num_decimals, asset_data,
                    tx_id, sender, recipient, block_height, timestamp,
                    infiniti_seq):
        self.version = version
        self.amount = amount
        self.uuid = uuid
        self.num_decimals = num_decimals
        self.asset_data = asset_data

    @property
    def is_issuance(self):
        """
        An issuance transaction is a CardTransfer originating from a Dealer
        """
        return self._is_issuance
    