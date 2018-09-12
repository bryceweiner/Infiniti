import hashlib,base58,struct,ecdsa,base64,sys,secp256k1,binascii,datetime
from crypto import *
from hashlib import sha256
from secp256k1 import ALL_FLAGS
from infiniti.params import *
from Crypto.Random import random

def Hash(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def valid_address(data):
    raw = base58.check_decode(data)
    version = raw[:1].encode("hex")
    return (version == str(int(param_query(NETWORK,'address_version').encode('hex')))) or (version == "66")

def public_key_to_address(public_key,ip=False):
    i = hashlib.new('ripemd160', hashlib.sha256(public_key).digest()).digest()
    prefix_to_use = str(int(param_query(NETWORK,'address_version').encode('hex'))) if not ip else '66'
    vh160 = prefix_to_use.decode('hex')+i
    return base58.check_encode(vh160)

def modular_sqrt(a, p):
    """ Find a quadratic residue (mod p) of 'a'. p
    must be an odd prime.
    
    Solve the congruence of the form:
    x^2 = a (mod p)
    And returns x. Note that p - x is also a root.
    
    0 is returned is no square root exists for
    these a and p.
    
    The Tonelli-Shanks algorithm is used (except
    for some simple cases in which the solution
    is known from an identity). This algorithm
    runs in polynomial time (unless the
    generalized Riemann hypothesis is false).
    """
    # Simple cases
    #
    if legendre_symbol(a, p) != 1:
        return 0
    elif a == 0:
        return 0
    elif p == 2:
        return p
    elif p % 4 == 3:
        return pow(a, (p + 1) / 4, p)
    
    # Partition p-1 to s * 2^e for an odd s (i.e.
    # reduce all the powers of 2 from p-1)
    #
    s = p - 1
    e = 0
    while s % 2 == 0:
        s /= 2
        e += 1
        
    # Find some 'n' with a legendre symbol n|p = -1.
    # Shouldn't take long.
    #
    n = 2
    while legendre_symbol(n, p) != -1:
        n += 1
        
    # Here be dragons!
    # Read the paper "Square roots from 1; 24, 51,
    # 10 to Dan Shanks" by Ezra Brown for more
    # information
    #
    
    # x is a guess of the square root that gets better
    # with each iteration.
    # b is the "fudge factor" - by how much we're off
    # with the guess. The invariant x^2 = ab (mod p)
    # is maintained throughout the loop.
    # g is used for successive powers of n to update
    # both a and b
    # r is the exponent - decreases with each update
    #
    x = pow(a, (s + 1) / 2, p)
    b = pow(a, s, p)
    g = pow(n, s, p)
    r = e
    
    while True:
        t = b
        m = 0
        for m in xrange(r):
            if t == 1:
                break
            t = pow(t, 2, p)
            
        if m == 0:
            return x
        
        gs = pow(g, 2 ** (r - m - 1), p)
        g = (gs * gs) % p
        x = (x * gs) % p
        b = (b * g) % p
        r = m
        
def legendre_symbol(a, p):
    """ Compute the Legendre symbol a|p using
    Euler's criterion. p is a prime, a is
    relatively prime to p (if p divides
    a, then a|p = 0)
    
    Returns 1 if a has a square root modulo
    p, -1 otherwise.
    """
    ls = pow(a, (p - 1) / 2, p)
    return -1 if ls == p - 1 else ls

def sign_message(private_key, message, compressed=True):
    privkey = secp256k1.PrivateKey()
    privkey.set_raw_privkey(private_key)
    message = message.encode('utf8')
    fullmsg = (pack_varint(len(param_query(NETWORK,'message_magic'))) + param_query(NETWORK,'message_magic') + pack_varint(len(message)) + message)
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
    fullmsg = (pack_varint(len(param_query(NETWORK,'message_magic'))) + param_query(NETWORK,'message_magic') + pack_varint(len(message)) + message)
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
    return public_key_to_address(pubser,prefix) == address

def sign_and_verify(key, message, infiniti = False, compressed=True):
    s = sign_message(key.PrivateKey(), message, compressed)
    assert verify_message(key.Address(infiniti), s, message, infiniti)
    return s

def pack_varint(integer):
    if integer>0xFFFFFFFF:
        packed="\xFF"+pack_uint64(integer)
    elif integer>0xFFFF:
        packed="\xFE"+struct.pack('<L', integer)
    elif integer>0xFC:
        packed="\xFD".struct.pack('<H', integer)
    else:
        packed=struct.pack('B', integer)
    
    return packed

def pack_uint64(integer):
    upper=int(integer/4294967296)
    lower=integer-upper*4294967296
    
    return struct.pack('<L', lower)+struct.pack('<L', upper)

def hex_to_bin(hex):
    try:
        raw=binascii.a2b_hex(hex)
    except Exception:
        return None
        
    return raw
    
def bin_to_hex(string):
    return binascii.b2a_hex(string).decode('utf-8')

def pack_time(_time=time.time()):
    return binascii.unhexlify(str(int(time.mktime(time.gmtime(_time))) - time.timezone))

def unpack_time(_time):
    return datetime.utcfromtimestamp(int(binascii.hexlify(_time)))

def nonce():
    """
    Return a random int between 0 and (2^32)-1
    """
    return random.randint(0, 4294967295)
