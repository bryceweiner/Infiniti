import time
import hashlib
import struct
from cStringIO import StringIO
from collections import OrderedDict

from node import version as node_version
from node.protocol import fields, utils
from node.protocol.exceptions import UnknownMessageException

from params import *
from db import open_db

class SerializerMeta(type):
    """The serializer meta class. This class will create an attribute
    called '_fields' in each serializer with the ordered dict of
    fields present on the subclasses.
    """
    def __new__(meta, name, bases, attrs):
        attrs["_fields"] = meta.get_fields(bases, attrs, fields.Field)
        return super(SerializerMeta, meta).__new__(meta, name, bases, attrs)

    @classmethod
    def get_fields(meta, bases, attrs, field_class):
        """This method will construct an ordered dict with all
        the fields present on the serializer classes."""
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, field_value in list(attrs.iteritems())
                  if isinstance(field_value, field_class)]

        for base_cls in bases[::-1]:
            if hasattr(base_cls, "_fields"):
                fields = list(base_cls._fields.items()) + fields

        fields.sort(key=lambda it: it[1].count)
        return OrderedDict(fields)


class SerializerABC(object):
    """The serializer abstract base class."""
    __metaclass__ = SerializerMeta


class Serializer(SerializerABC):
    """The main serializer class, inherit from this class to
    create custom serializers.

    Example of use::

        class VerAckSerializer(Serializer):
            model_class = VerAck
    """
    def serialize(self, obj, fields=None):
        """This method will receive an object and then will serialize
        it according to the fields declared on the serializer.

        :param obj: The object to serializer.
        """
        bin_data = StringIO()
        for field_name, field_obj in self._fields.iteritems():
            if fields:
                if field_name not in fields:
                    continue
            attr = getattr(obj, field_name, None)
            field_obj.parse(attr)
            bin_data.write(field_obj.serialize())

        return bin_data.getvalue()

    def deserialize(self, stream):
        """This method will read the stream and then will deserialize the
        binary data information present on it.

        :param stream: A file-like object (StringIO, file, socket, etc.)
        """
        model = self.model_class()
        for field_name, field_obj in self._fields.iteritems():
            value = field_obj.deserialize(stream)
            setattr(model, field_name, value)
        return model


class SerializableMessage(object):
    def get_message(self, coin="tao"):
        """Get the binary version of this message, complete with header."""
        message_header = MessageHeader(coin)
        message_header_serial = MessageHeaderSerializer()

        serializer = getSerializer(self.command)
        bin_message = serializer.serialize(self)
        payload_checksum = \
            MessageHeaderSerializer.calc_checksum(bin_message)
        message_header.checksum = payload_checksum
        message_header.length = len(bin_message)
        message_header.command = self.command

        bin_header = message_header_serial.serialize(message_header)
        return bin_header + bin_message

    def get_field_names(self):
        return getSerializer(self.command)._fields.keys()

    def __repr__(self):
        attrs = [ "%s=%s" % (name, getattr(self, name)) for name in self.get_field_names() ]
        return "<%s %s>" % (self.__class__.__name__, ", ".join(attrs))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        for name in self.get_field_names():
            if getattr(self, name) != getattr(other, name):
                return False

        return True


class MessageHeader(object):
    """The header of all bitcoin messages."""
    def __init__(self, coin="tao"):
        self.magic = param_query(NETWORK,'p2p_magic')
        self.command = "None"
        self.length = 0
        self.checksum = 0

    def _magic_to_text(self):
        """Converts the magic value to a textual representation."""
        return binascii.hexlify(param_query(NETWORK,'p2p_magic'))

    def __repr__(self):
        return "<%s Magic=[%s] Length=[%d] Checksum=[%d]>" % \
            (self.__class__.__name__, self._magic_to_text(),
                self.length, self.checksum)


class MessageHeaderSerializer(Serializer):
    """Serializer for the MessageHeader."""
    model_class = MessageHeader
    magic = fields.UInt32LEField()
    command = fields.FixedStringField(12)
    length = fields.UInt32LEField()
    checksum = fields.UInt32LEField()

    @staticmethod
    def calcsize():
        return struct.calcsize("i12sii")

    @staticmethod
    def calc_checksum(payload):
        """Calculate the checksum of the specified payload.

        :param payload: The binary data payload.
        """
        sha256hash = hashlib.sha256(payload)
        sha256hash = hashlib.sha256(sha256hash.digest())
        checksum = sha256hash.digest()[:4]
        return struct.unpack("<I", checksum)[0]


class IPv4Address(object):
    """The IPv4 Address (without timestamp)."""
    def __init__(self):
        self.services = fields.SERVICES["NODE_NETWORK"]
        self.ip_address = "0.0.0.0"
        self.port = 0

    def _services_to_text(self):
        """Converts the services field into a textual
        representation."""
        services = []
        for service_name, flag_mask in fields.SERVICES.iteritems():
            if self.services & flag_mask:
                services.append(service_name)
        return services

    def __repr__(self):
        services = self._services_to_text()
        if not services:
            services = "No Services"
        p = (self.__class__.__name__, self.ip_address, self.port, services)
        return "<%s IP=[%s:%d] Services=%r>" % p


class IPv4AddressSerializer(Serializer):
    """Serializer for the IPv4Address."""
    model_class = IPv4Address
    services = fields.UInt64LEField()
    ip_address = fields.IPv4AddressField()
    port = fields.UInt16BEField()

class IPv4AddressTimestamp(IPv4Address):
    """The IPv4 Address with timestamp."""

    def save(self):
        db = open_db(PEERS_DB_PATH)
        db.Put(self.ip_address + ":" + self.port, self.timestamp)

    def __init__(self):
        super(IPv4AddressTimestamp, self).__init__()
        self.timestamp = time.time()

    def __repr__(self):
        services = self._services_to_text()
        if not services:
            services = "No Services"
        return "<%s Timestamp=[%s] IP=[%s:%d] Services=%r>" % \
            (self.__class__.__name__, time.ctime(self.timestamp),
                self.ip_address, self.port, services)

class IPv4AddressTimestampSerializer(Serializer):
    """Serializer for the IPv4AddressTimestamp."""
    model_class = IPv4AddressTimestamp
    timestamp = fields.UInt32LEField()
    services = fields.UInt64LEField()
    ip_address = fields.IPv4AddressField()
    port = fields.UInt16BEField()


class Version(SerializableMessage):
    """The version command."""
    command = "version"

    def __init__(self,dest='',dest_port='',ip_address='',port=0):
        i = IPv4Address()
        i.ip_address = ip_address
        i.port = port
        p = IPv4Address()
        p.ip_address = dest
        p.port = dest_port
        self.version = param_query(NETWORK,'protocol_version')
        self.services = fields.SERVICES["NODE_NETWORK"]
        self.timestamp = time.time()
        self.addr_recv = p
        self.addr_from = i
        self.nonce = utils.nonce()
        self.user_agent = "/node:%s/" % node_version
        self.start_height = 0


class VersionSerializer(Serializer):
    """The version command serializer."""
    model_class = Version
    version = fields.Int32LEField()
    services = fields.UInt64LEField()
    timestamp = fields.Int64LEField()
    addr_recv = fields.NestedField(IPv4AddressSerializer)
    addr_from = fields.NestedField(IPv4AddressSerializer)
    nonce = fields.UInt64LEField()
    user_agent = fields.VariableStringField()
    start_height = fields.Int32LEField()


class VerAck(SerializableMessage):
    """The version acknowledge (verack) command."""
    command = "verack"


class VerAckSerializer(Serializer):
    """The serializer for the verack command."""
    model_class = VerAck

class Ping(SerializableMessage):
    """The ping command, which should always be
    answered with a Pong."""
    command = "ping"

    def __init__(self):
        self.nonce = utils.nonce()

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)


class PingSerializer(Serializer):
    """The ping command serializer."""
    model_class = Ping
    nonce = fields.UInt64LEField()


class Pong(SerializableMessage):
    """The pong command, usually returned when
    a ping command arrives."""
    command = "pong"

    def __init__(self):
        self.nonce = utils.nonce()

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)


class PongSerializer(Serializer):
    """The pong command serializer."""
    model_class = Pong
    nonce = fields.UInt64LEField()


class SmsgPing(SerializableMessage):
    """The secure message ping command, which should always be
    answered with a smsgPong."""
    command = "smsgPing"

    def __init__(self):
        pass

    def __repr__(self):
        return "<%s >" % (self.__class__.__name__)

class SmsgPingSerializer(Serializer):
    """The ping command serializer."""
    model_class = SmsgPing

class SmsgPong(SerializableMessage):
    """The secure message pong command, usually returned when
    a smsgping command arrives."""
    command = "smsgPong"
    def __init__(self):
        pass

    def __repr__(self):
        return "<%s Nonce=[%d]>" % (self.__class__.__name__, self.nonce)

class SmsgPongSerializer(Serializer):
    model_class = SmsgPong

class Inventory(SerializableMessage):
    """The Inventory representation."""
    def __init__(self):
        self.inv_type = fields.INVENTORY_TYPE["MSG_TX"]
        self.inv_hash = 0

    def type_to_text(self):
        """Converts the inventory type to text representation."""
        for k, v in fields.INVENTORY_TYPE.iteritems():
            if v == self.inv_type:
                return k
        return "Unknown Type"

    def __repr__(self):
        return "<%s Type=[%s] Hash=[%064x]>" % \
            (self.__class__.__name__, self.type_to_text(),
                self.inv_hash)

    def __eq__(self, other):
        return self.inv_type == other.inv_type and self.inv_hash == other.inv_hash


class InventorySerializer(Serializer):
    """The serializer for the Inventory."""
    model_class = Inventory
    inv_type = fields.UInt32LEField()
    inv_hash = fields.Hash()


class InventoryVector(SerializableMessage):
    """A vector of inventories."""
    command = "inv"

    def __init__(self):
        self.inventory = []

    def __repr__(self):
        #for i in self.inventory:
        #    print i
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.inventory)

    def __iter__(self):
        return iter(self.inventory)


class InventoryVectorSerializer(Serializer):
    """The serializer for the vector of inventories."""
    model_class = InventoryVector
    inventory = fields.ListField(InventorySerializer)


class AddressVector(SerializableMessage):
    """A vector of addresses."""
    command = "addr"

    def __init__(self):
        self.addresses = []

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.addresses)

    def __iter__(self):
        return iter(self.addresses)


class AddressVectorSerializer(Serializer):
    """Serializer for the addresses vector."""
    model_class = AddressVector
    addresses = fields.ListField(IPv4AddressTimestampSerializer)


class GetData(InventoryVector):
    """GetData message command."""
    command = "getdata"


class GetDataSerializer(Serializer):
    """Serializer for the GetData command."""
    model_class = GetData
    inventory = fields.ListField(InventorySerializer)


class NotFound(GetData):
    """NotFound command message."""
    command = "notfound"


class NotFoundSerializer(Serializer):
    """Serializer for the NotFound message."""
    model_class = NotFound
    inventory = fields.ListField(InventorySerializer)


class OutPoint(object):
    """The OutPoint representation."""
    def __init__(self):
        self.out_hash = 0
        self.index = 0

    def __repr__(self):
        return "<%s Index=[%d] Hash=[%064x]>" % \
            (self.__class__.__name__, self.index,
                self.out_hash)

class OutPointSerializer(Serializer):
    """The OutPoint representation serializer."""
    model_class = OutPoint
    out_hash = fields.Hash()
    index = fields.UInt32LEField()


class TxIn(object):
    """The transaction input representation."""
    def __init__(self):
        self.previous_output = None
        self.signature_script = "Empty"
        # See https://en.bitcoin.it/wiki/Protocol_specification#tx for definition.
        # Basically, this field should always be UINT_MAX, i.e. int("ffffffff", 16)
        self.sequence = 4294967295

    def save(self,tx_hash,pos):
        db = open_db(TXIN_PATH)
        db.Put(tx_hash + "_" + pos, self.serialize())

    def __repr__(self):
        return "<%s Sequence=[%d]>" % \
            (self.__class__.__name__, self.sequence)


class TxInSerializer(Serializer):
    """The transaction input serializer."""
    model_class = TxIn
    previous_output = fields.NestedField(OutPointSerializer)
    signature_script = fields.VariableStringField()
    sequence = fields.UInt32LEField()


class TxOut(object):
    """The transaction output."""
    def __init__(self):
        self.value = 0
        self.utxoid = BASE_UTXO_ID
        self.pk_script = "Empty"

    def save(self,tx_hash,pos):
        db = open_db(TXOUT_PATH)
        db.Put(tx_hash + "_" + pos, self.serialize())

    def get_value(self):
        return self.value // 100000000 + self.value % 100000000 / 100000000.0

    def __repr__(self):
        return "<%s Value=[%.8f]>" % (self.__class__.__name__, self.get_btc_value())


class TxOutSerializer(Serializer):
    """The transaction output serializer."""
    model_class = TxOut
    value = fields.Int64LEField()
    utxoid = fields.Int64LEField()
    pk_script = fields.VariableStringField()


class Tx(SerializableMessage):
    """The main transaction representation, this object will
    contain all the inputs and outputs of the transaction."""
    command = "tx"

    def __init__(self):
        self.version = 1
        self.time = 0
        self.tx_in = []
        self.tx_out = []
        self.lock_time = 0
        self.data = ""

    def save(self,block_hash,pos):
        db = open_db(TRANSACTION_PATH)
        db.Put(block_hash + "_" + str(pos), self.calculate_hash() )
        db = None # trigger garbage collection
        n = 0
        for txout in self.tx_out:
            txout.save(self.calculate_hash())
            n += 1
        n = 0
        for txin in self.tx_in:
            txin.save(self.calculate_hash())
            n += 1

    def _locktime_to_text(self):
        """Converts the lock-time to textual representation."""
        text = "Unknown"
        if self.lock_time == 0:
            text = "Always Locked"
        elif self.lock_time < 500000000:
            text = "Block %d" % self.lock_time
        elif self.lock_time >= 500000000:
            text = time.ctime(self.lock_time)
        return text

    def calculate_hash(self):
        """This method will calculate the hash of the transaction."""
        hash_fields = ["version", "time", "tx_in", "tx_out", "lock_time", "data"]
        serializer = TxSerializer()
        bin_data = serializer.serialize(self, hash_fields)
        h = hashlib.sha256(bin_data).digest()
        h = hashlib.sha256(h).digest()
        return h[::-1].encode("hex_codec")

    def __repr__(self):
        return "<%s Version=[%d] Lock Time=[%s] TxIn Count=[%d] Hash=[%s] TxOut Count=[%d] Data=[%s]>" \
            % (self.__class__.__name__, self.version, self._locktime_to_text(),
                len(self.tx_in), self.calculate_hash(), len(self.tx_out), self.data)


class TxSerializer(Serializer):
    """The transaction serializer."""
    model_class = Tx
    version = fields.UInt32LEField()
    time = fields.UInt32LEField()
    tx_in = fields.ListField(TxInSerializer)
    tx_out = fields.ListField(TxOutSerializer)
    lock_time = fields.UInt32LEField()
    data = fields.VariableStringField()


class BlockHeader(SerializableMessage):
    """The header of the block."""
    def __init__(self):
        self.version = 0
        self.prev_block = 0
        self.merkle_root = 0
        self.timestamp = 0
        self.bits = 0
        self.nonce = 0
        self.txns_count = 0

    def calculate_hash(self):
        """This method will calculate the hash of the block."""
        hash_fields = ["version", "prev_block", "merkle_root",
                       "timestamp", "bits", "nonce"]
        serializer = BlockSerializer()
        bin_data = serializer.serialize(self, hash_fields)
        h = hashlib.sha256(bin_data).digest()
        h = hashlib.sha256(h).digest()
        return h[::-1].encode("hex_codec")

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp),
                self.nonce, self.calculate_hash(), self.txns_count)


class BlockHeaderSerializer(Serializer):
    """The serializer for the block header."""
    model_class = BlockHeader
    version = fields.UInt32LEField()
    prev_block = fields.Hash()
    merkle_root = fields.Hash()
    timestamp = fields.UInt32LEField()
    bits = fields.UInt32LEField()
    nonce = fields.UInt32LEField()
    txns_count = fields.VariableIntegerField()


class Block(BlockHeader):
    """The block message. This message contains all the transactions
    present in the block."""
    command = "block"

    def __init__(self):
        self.version = 0
        self.prev_block = 0
        self.merkle_root = 0
        self.timestamp = 0
        self.bits = 0
        self.nonce = 0
        self.txns = []
        self.blocksig = ""

    def save(self,db):
        db = open_db(BLOCK_PATH)
        db.Put(self.calculate_hash(),self.timestamp)
        db = None # trigger garbage collection
        n = 0
        for tx in self.txns:
            tx.save(self.calculate_hash(),n)
            n += 1

    def __len__(self):
        return len(self.txns)

    def __iter__(self):
        return iter(self.txns)

    def __repr__(self):
        return "<%s Version=[%d] Timestamp=[%s] Nonce=[%d] Hash=[%s] Tx Count=[%d] Block Signature=[%s]>" % \
            (self.__class__.__name__, self.version, time.ctime(self.timestamp),
                self.nonce, self.calculate_hash(), len(self), self.blocksig)


class BlockSerializer(Serializer):
    """The deserializer for the blocks."""
    model_class = Block
    version = fields.UInt32LEField()
    prev_block = fields.Hash()
    merkle_root = fields.Hash()
    timestamp = fields.UInt32LEField()
    bits = fields.UInt32LEField()
    nonce = fields.UInt32LEField()
    txns = fields.ListField(TxSerializer)
    blocksig = fields.VariableIntegerField()


class HeaderVector(SerializableMessage):
    """The header only vector."""
    command = "headers"

    def __init__(self):
        self.headers = []

    def __repr__(self):
        return "<%s Count=[%d]>" % (self.__class__.__name__, len(self))

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)


class HeaderVectorSerializer(Serializer):
    """Serializer for the block header vector."""
    model_class = HeaderVector
    headers = fields.ListField(BlockHeaderSerializer)


class MemPool(SerializableMessage):
    """The mempool command."""
    command = "mempool"


class MemPoolSerializer(Serializer):
    """The serializer for the mempool command."""
    model_class = MemPool


class GetAddr(SerializableMessage):
    """The getaddr command."""
    command = "getaddr"


class GetAddrSerializer(Serializer):
    """The serializer for the getaddr command."""
    model_class = GetAddr


class GetBlocks(SerializableMessage):
    """The getblocks command."""
    command = "getblocks"

    def __init__(self, hashes):
        self.version = param_query(NETWORK,'protocol_version')
        self.hash_count = len(hashes)
        self.hash_stop = 0
        self.block_hashes = hashes


class GetBlocksSerializer(Serializer):
    model_class = GetBlocks
    version = fields.UInt32LEField()
    hash_count = fields.VariableIntegerField()
    block_hashes = fields.BlockLocator()
    hash_stop = fields.Hash()


class GetHeaders(GetBlocks):
    command = "getheaders"

class GetHeadersSerializer(GetBlocksSerializer):
    model_class = GetHeaders

class Reject(SerializableMessage):
    command = "reject"

    def __init__(self):
        self.message = None
        # general "invalid" error code is default
        self.ccode = 0x10
        self.reason = "Unknown"
        self.data = None


class RejectSerializer(Serializer):
    model_class = Reject
    message = fields.VariableStringField()
    ccode = fields.FixedStringField(1)
    reason = fields.VariableStringField()
    data = fields.Hash()


CMD_MAPPING = {
    "version": VersionSerializer,
    "verack": VerAckSerializer,
    "ping": PingSerializer,
    "pong": PongSerializer,
    "inv": InventoryVectorSerializer,
    "addr": AddressVectorSerializer,
    "getdata": GetDataSerializer,
    "notfound": NotFoundSerializer,
    "tx": TxSerializer,
    "block": BlockSerializer,
    "headers": HeaderVectorSerializer,
    "mempool": MemPoolSerializer,
    "getaddr": GetAddrSerializer,
    "getblocks": GetBlocksSerializer,
    "getheaders": GetHeadersSerializer,
    "reject": RejectSerializer,
    "smsgPing": SmsgPingSerializer,
    "smsgPong": SmsgPongSerializer,
}


def getSerializer(msgtype):
    """
    Return a new serializer of the given msg type.
    """
    if msgtype not in CMD_MAPPING:
        raise UnknownMessageException("%s is not recognized" % msgtype)
    return CMD_MAPPING[msgtype]()
