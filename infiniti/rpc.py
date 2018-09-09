from wallet.wallet import Wallet
import os
import time
from providers.cryptoid import Cryptoid
from providers import TaoNode
from decimal import Decimal, getcontext
from os import listdir
from os.path import isfile, join
import json, binascii
from utils.encoder import DecimalEncoder
from infiniti.params import *
from infiniti.logger import *
from utils.crypto import sign_and_verify, verify_message
from p2p import version
from utils.db import *

if USE_RPC:
    _CONNECTION = TaoNode()
else:
    _CONNECTION = Cryptoid(NETWORK)

def importwallet():
    pass

def exportwallet():
    pass

def get_status(k):
    db = open_db(os.path.join(DATA_PATH,"status"))
    v = db.get(k)
    return v

def getinfo():
    info = _CONNECTION.getinfo()
    infiniti = {
        "infiniti_version" : version,
        "connections" : get_status('connected_peers'),
        "tao_node_info" : info,
    }
    return json.dumps(infiniti,cls=DecimalEncoder, sort_keys=True, indent=4)

def sync(fn,passphrase, reindex=False):
    try:
        _CONNECTION.sync(fn,passphrase,reindex)
    except:
        # core client is offline
        pass

def signmessage(fn,passphrase,address,message):
    w = Wallet(fn).fromFile(passphrase)
    #try:
    infiniti = address[:1]=='i'
    for k in w.Keys:
        if k.address(infiniti) == address:
            sig = k.sign_msg(message)
    return json.dumps({
            "address":k.address(infiniti),
            "message":message,
            "signature":sig
        }, sort_keys=True, indent=4)

def verifymessage(address,message,signature):
    infiniti = address[:1]=='i'
    return json.dumps({ "verified" : verify_message(address, signature, message, prefix=infiniti) } )

def listunspent(fn):
    try:
        w = Wallet(fn).fromFile('')
        utxo = json.loads(w.get_status("utxo"))
        info = _CONNECTION.getinfo()
        for u in utxo:
            u.update({ "confirmations" : str(int(info['blocks']) - int(u["height"]))})
        return json.dumps(utxo, sort_keys=True, indent=4)
    except:
        pass

def createwallet(passphrase):
    seed,nonce = Wallet().create_seed(WALLET_PATH)
    wallet = Wallet().fromSeed(seed,nonce,passphrase,wallet_path=os.path.dirname(os.path.abspath(__file__)))
    wallet.update_status("height",str(_CONNECTION.parameters.start_height))
    wallet.update_status("utxo",json.dumps([]))
    wallet.update_status("current","ready")
    wallet.update_status("updated",str(0))
    d = {
        "passphrase":passphrase,
        "nonce" : binascii.hexlify(nonce),
        "seed":seed,
        "data_file":wallet._fn() 
    }
    return json.dumps(d, sort_keys=True, indent=4)

def addressbalance(address):
    c = _CONNECTION
    balance = 0
    balance += Decimal(c.getbalance(address))
    d = { "balance":balance }
    return json.dumps(d,cls=DecimalEncoder, sort_keys=True, indent=4)

def address_in_wallet(fn,passphrase,address):
    sync(fn,passphrase)
    wallet = Wallet(fn).fromFile(passphrase)
    d = { "address_in_wallet" : False }
    for k in wallet.Keys:
        if k.address() == address:
            d = { "address_in_wallet" : True }
    return json.dumps(d, sort_keys=True, indent=4)

def dumpaddress(fn,passphrase,address):
    wallet = Wallet(fn).fromFile(passphrase)
    for k in wallet.Keys:
        if k.address() == address:
            d = k.dump()
        elif k.address(True) == address:
            d = k.dump()

    return json.dumps(d, sort_keys=True, indent=4)

def listaddresses(fn):
    wallet = Wallet(fn).fromFile()
    a = []
    for k in wallet.Keys:
        a.append((k.address_type(),k.address(), k.address(True)) )
    d = { "addresses" : a }
    return json.dumps(d, sort_keys=True, indent=4)

def newaddress(fn,passphrase,addr_type=0):
    """
    getnetaddress
    """
    wallet = Wallet(fn).fromFile(passphrase)
    # Address Types
    # addr_type == 0, deposit
    # addr_type == 1, change
    # addr_type == 2, staking
    # addr_type == 3, Dealer
    # Address types aren't programmatically important, but help to organize
    if addr_type is None:
        addr_type = 0
    k = wallet.create_address(save=True,addr_type=addr_type)
    d = { "new_address" : (k.address_type(),k.address(),k.address(True)) }
    return json.dumps(d, sort_keys=True, indent=4)

def walletbalance(fn,passphrase):
    sync(fn,passphrase)
    wallet = Wallet(fn).fromFile(passphrase)
    c = _CONNECTION
    balance = 0
    for k in wallet.Keys:
        balance += Decimal(c.getbalance(k.address()))
    d = { "balance": balance }
    return json.dumps(d, cls=DecimalEncoder, sort_keys=True, indent=4)

def listwallets():
    return [f for f in listdir(WALLET_PATH) if True]

