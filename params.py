from collections import namedtuple
from decimal import Decimal

from exceptions import *
from sys import platform
import os

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

TAO_RPC = True

START_HEIGHT = 134500

_params = namedtuple('PAParams', [
    'network_name',
    'network_shortname',
    'P2TH_wif',
    'P2TH_addr',
    'test_P2TH_wif',
    'test_P2TH_addr',
    'P2TH_fee',
])

params = (

    ## Tao mainnet
    _params("Tao", "XTO", "CK4NSWrSEAmDC6YqzDWq7niK2EzZ1ufvvLLczodmsCtEj7v5sB1x",
             "TpeCntDjXS2E3rJmJDpuqkhN1v93yzzVQx", "",
             "", Decimal(0.0002)),
)

def param_query(name):
    '''Find the PAParams for a network by its long or short name. Raises
    UnsupportedNetwork if no PAParams is found.
    '''

    for p in params:
        if name in (p.network_name, p.network_shortname,):
            return p

    raise UnsupportedNetwork