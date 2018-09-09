from collections import namedtuple
from decimal import Decimal
import codecs

from exceptions import *
from sys import platform
import os
BASE_UTXO_ID = 0x100001
OP_RETURN_KEY = 0xd6901b0cbe0f48420fc5814866b7c3de8d08c4e721a7afc655d5b5a0f8534f23

if platform == "linux" or platform == "linux2":
    USER_CONFIG_PATH = '~/.{0}/{1}.conf'
elif platform == "darwin":
    USER_CONFIG_PATH = "~/Library/Application Support/{0}/{1}.conf"
elif platform == "win32":
    USER_CONFIG_PATH = ""

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(ROOT_PATH, 'data') 
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

TEXT_PATH = os.path.join(ROOT_PATH, 'wallet')
if not os.path.exists(TEXT_PATH):
    os.makedirs(TEXT_PATH)

TRANSACTION_PATH = os.path.join(DATA_PATH, 'tx')
if not os.path.exists(TRANSACTION_PATH):
    os.makedirs(TRANSACTION_PATH)

INDEX_PATH = os.path.join(DATA_PATH, 'index')
if not os.path.exists(INDEX_PATH):
    os.makedirs(INDEX_PATH)

PROTOCOL_PATH = os.path.join(DATA_PATH, 'protocol')
if not os.path.exists(PROTOCOL_PATH):
    os.makedirs(PROTOCOL_PATH)

USE_RPC = True

NETWORK = "Tao"

_params = namedtuple('_params', [
    'network_name',
    'network_shortname',
    'Infiniti_fee',
    'local_rpc_config',
    'rpc_url',
    'rpc_port',
    'rpc_username',
    'rpc_password',
    'start_height',
    'message_magic',
    'address_version',
    'wif_version',
    'hd_pub',
    'hd_prv',
    'genesis_hash',
    'protocol_version',
    'p2p_magic',
    'p2p_port',
])

params = (
    ## Tao mainnet
    _params(
        "Tao", 
        "XTO", 
        Decimal(0.0001),
        True,
        "127.0.0.1",
        15151,
        "",
        "",
        134500,
        "Tao Signed Message:\n",
        "\x42",
        "\x4c",
        [ codecs.decode('0488b21e', 'hex') ],
        [ codecs.decode('0488ade4', 'hex') ],
        0x0000c1c4b036f822bd91dc2006b5575b9c3617903925b8e738803e094cd23f20,
        61402,
        0xE11ED11D,
        15150,
),)

def net_query(name):
    for p in params:
        if name in (p.network_name, p.network_shortname,):
                return p
    raise UnsupportedNetwork

def param_query(name,key=None):
    '''Find the _params for a network by its long or short name. Raises
    UnsupportedNetwork if no _params is found.
    '''
    for p in params:
        if name in (p.network_name, p.network_shortname,):
            if key is not None:
                for n, value in p._asdict().iteritems():
                    if n == key:
                        return value
            else:
                return p
    raise UnsupportedNetwork