import base58
import ecdsa
import base64
import hashlib
import sys
from crypto import *
import secp256k1
from hashlib import sha256
from secp256k1 import ALL_FLAGS

msg_magic_str = "Tao Signed Message:\n" 

def sign_message(private_key, message, compressed=True):
    privkey = secp256k1.PrivateKey()
    privkey.set_raw_privkey(private_key)
    message = message.encode('utf8')
    fullmsg = (varint(len(msg_magic_str)) + msg_magic_str + varint(len(message)) + message)
    hmsg = Hash(fullmsg)

    rawsig = privkey.ecdsa_sign_recoverable(hmsg, raw=True)
    sigbytes, recid = privkey.ecdsa_recoverable_serialize(rawsig)

    meta = 27 + recid
    if compressed:
        meta += 4

    res = base64.b64encode(chr(meta).encode('utf8') + sigbytes)
    return res

def verify_message(address, signature, message, prefix=False):
    if len(signature) != 88:
        raise Exception("Invalid base64 signature length")

    message = message.encode('utf8')
    fullmsg = (varint(len(msg_magic_str)) + msg_magic_str + varint(len(message)) + message)
    hmsg = Hash(fullmsg)

    sigbytes = base64.b64decode(signature)
    if len(sigbytes) != 65:
        raise Exception("Invalid signature length")

    compressed = (ord(sigbytes[0:1]) - 27) & 4 != 0
    rec_id = (ord(sigbytes[0:1]) - 27) & 3

    p = secp256k1.PublicKey(ctx=None, flags=ALL_FLAGS)
    sig = p.ecdsa_recoverable_deserialize(sigbytes[1:], rec_id)

    # Recover the ECDSA public key.
    recpub = p.ecdsa_recover(hmsg, sig, raw=True)
    pubser = secp256k1.PublicKey(recpub, ctx=None).serialize(compressed=compressed)
    return public_key_to_bc_address(pubser,prefix) == address

def sign_and_verify(key, message, infiniti = False, compressed=True):
    s = sign_message(key.PrivateKey(), message, compressed)
    assert verify_message(key.Address(infiniti), s, message, infiniti)
    return s


