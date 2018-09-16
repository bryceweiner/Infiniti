from collections import namedtuple
from decimal import Decimal
from sys import platform
from infiniti.exceptions import *
import codecs, os, time
from utils.helpers import *

INFINIT_VERSION = 0x000001

NETWORK = "Tao"
BASE_UTXO_ID = 0x100001
OP_RETURN_KEY = 'd6901b0cbe0f48420fc5814866b7c3de8d08c4e721a7afc655d5b5a0f8534f23'

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PID_FILE =  os.path.join(ROOT_PATH,'infiniti')

if platform == "linux" or platform == "linux2":
    USER_CONFIG_PATH = '~/.{0}/{1}.conf'
elif platform == "darwin":
    USER_CONFIG_PATH = "~/Library/Application Support/{0}/{1}.conf"
elif platform == "win32":
    USER_CONFIG_PATH = ""

DATA_PATH = os.path.join(ROOT_PATH, 'data')
WALLET_PATH = os.path.join(ROOT_PATH, 'wallets')

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)
if not os.path.exists(join_path(DATA_PATH,NETWORK)):
    os.makedirs(join_path(DATA_PATH,NETWORK))
if not os.path.exists(WALLET_PATH):
    os.makedirs(WALLET_PATH)

USE_RPC = True

INFINITI_DEBUG = True # infiniti object debug mode. No blockchain transaction commits.

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
    'seeds',
    'utxo_id_suppport',
    'tx_comment_support',
    'proof_of_stake',
    'segwit',
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
        136760,
        "Tao Signed Message:\n",
        "\x42",
        "\x4c",
        [ codecs.decode('0488b21e', 'hex') ],
        [ codecs.decode('0488ade4', 'hex') ],
        0x0000c1c4b036f822bd91dc2006b5575b9c3617903925b8e738803e094cd23f20,
        61402,
        0xE11ED11D,
        15150,
        (
            ('127.0.0.1:15150',int(time.time())),
            ('71.91.134.199:15150',int(time.time())),
            ('94.130.51.181:15150',int(time.time())),
            ('45.32.194.188:15150',int(time.time())),
            ('107.191.62.58:15150',int(time.time())),
            ('173.249.2.29:15150',int(time.time())),
            ('67.171.226.167:15150',int(time.time())),
            ('45.51.24.49:15150',int(time.time())),
            ('47.199.215.76:15150',int(time.time())),
            ('73.203.83.188:15150',int(time.time())),
            ('75.70.53.54:15150',int(time.time())),
            ('73.34.110.174:15150',int(time.time())),
            ('173.66.238.22:15150',int(time.time())),
            ('96.44.189.195:15150',int(time.time())),
        ),
        True,
        True,
        True,
        False,
),)

VERWIF = { 
            "DGB" : (30,128) ,
            "VIA" : (71,199) ,
            "SYS" : (63,128) ,
            "BTC" : (0, 128) ,
            "UNO" : (130,224) ,
            "IOC" : (103, 231) ,
            "DOGE" : (30,158) ,
            "XTO" : (66,76),
            "DASH" : (76,204) ,
            "MZC" : (50,224) ,
            "XVG" : (30,158) ,
            "VTC" : (71,128) ,
            "XPM" : (23,131) ,
            "PPC" : (55,183) ,
            "VRC" : (70,198) ,
            "FLO" : (35,176) ,
            "TX" : (66,153) ,
            "PINK" : (3,131) ,
            "BLK" : (25,153) ,
    }


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

