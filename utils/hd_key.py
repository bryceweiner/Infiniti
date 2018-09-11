#!/usr/bin/env python
#
# Copyright 2014 Corgan Labs
# See LICENSE.txt for distribution terms
#

import os
import hmac
import hashlib
import ecdsa
import struct
import codecs
import base58

from hashlib import sha256
from binascii import b2a_hex, hexlify
from ecdsa.curves import SECP256k1
from ecdsa.ecdsa import int_to_string, string_to_int
from ecdsa.numbertheory import square_root_mod_prime as sqrt_mod
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from infiniti.params import NETWORK, param_query

MIN_ENTROPY_LEN = 128        # bits
HD_HARDEN    = 0x80000000 # choose from hardened set of child keys
CURVE_GEN       = ecdsa.ecdsa.generator_secp256k1
CURVE_ORDER     = CURVE_GEN.order()
FIELD_ORDER     = SECP256k1.curve.p()
INFINITY        = ecdsa.ellipticcurve.INFINITY
EX_TEST_PRIVATE = [ codecs.decode('04358394', 'hex') ] # Version strings for testnet extended private keys
EX_TEST_PUBLIC  = [ codecs.decode('043587CF', 'hex') ] # Version strings for testnet extended public keys

class HDKey(object):

    # Static initializers to create from entropy or external formats
    #
    @staticmethod
    def fromEntropy(entropy, public=False, testnet=False):
        "Create a HDKey using supplied entropy >= MIN_ENTROPY_LEN"
        if entropy == None:
            entropy = os.urandom(MIN_ENTROPY_LEN/8) # Python doesn't have os.random()
        if not len(entropy) >= MIN_ENTROPY_LEN/8:
            raise ValueError("Initial entropy %i must be at least %i bits" %
                                (len(entropy), MIN_ENTROPY_LEN))
        I = hmac.new(b"Tao seed", entropy, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        # FIXME test Il for 0 or less than SECP256k1 prime field order
        key = HDKey(secret=Il, chain=Ir, depth=0, index=0, fpr=b'\0\0\0\0', public=False, testnet=testnet)
        if public:
            key.SetPublic()
        return key

    @staticmethod
    def fromExtendedKey(xkey, public=False, encoded=True):
        """
        Create a HDKey by importing from extended private or public key string

        If public is True, return a public-only key regardless of input type.
        """
        # Sanity checks
        if encoded:
            raw = base58.check_decode(xkey)
            if len(raw) != 78:
                raise ValueError("extended key format wrong length")

        # Verify address version/type
        version = raw[:4]
        if version in param_query(NETWORK,'hd_prv'):
            is_testnet = False
            is_pubkey = False
        elif version in EX_TEST_PRIVATE:
            is_testnet = True
            is_pubkey = False
        elif version in param_query(NETWORK,'hd_pub'):
            is_testnet = False
            is_pubkey = True
        elif version in EX_TEST_PUBLIC:
            is_testnet = True
            is_pubkey = True
        else:
            raise ValueError("unknown extended key version")

        # Extract remaining fields
        # Python 2.x compatibility
        if type(raw[4]) == int:
            depth = raw[4]
        else:
            depth = ord(raw[4])
        fpr = raw[5:9]
        child = struct.unpack(">L", raw[9:13])[0]
        chain = raw[13:45]
        secret = raw[45:78]

        # Extract private key or public key point
        if not is_pubkey:
            secret = secret[1:]
        else:
            # Recover public curve point from compressed key
            # Python3 FIX
            lsb = secret[0] & 1 if type(secret[0]) == int else ord(secret[0]) & 1
            x = string_to_int(secret[1:])
            ys = (x**3+7) % FIELD_ORDER # y^2 = x^3 + 7 mod p
            y = sqrt_mod(ys, FIELD_ORDER)
            if y & 1 != lsb:
                y = FIELD_ORDER-y
            point = ecdsa.ellipticcurve.Point(SECP256k1.curve, x, y)
            secret = ecdsa.VerifyingKey.from_public_point(point, curve=SECP256k1)

        key = HDKey(secret=secret, chain=chain, depth=depth, index=child, fpr=fpr, public=is_pubkey, testnet=is_testnet)
        if not is_pubkey and public:
            key = key.SetPublic()
        return key


    # Normal class initializer
    def __init__(self, secret, chain, depth, index, fpr, public=False, testnet=False):
        """
        Create a public or private HDKey using key material and chain code.

        secret   This is the source material to generate the keypair, either a
                 32-byte string representation of a private key, or the ECDSA
                 library object representing a public key.

        chain    This is a 32-byte string representation of the chain code

        depth    Child depth; parent increments its own by one when assigning this

        index    Child index

        fpr      Parent fingerprint

        public   If true, this keypair will only contain a public key and can only create
                 a public key chain.
        """

        self.public = public
        if public is False:
            self.k = ecdsa.SigningKey.from_string(secret, curve=SECP256k1)
            self.K = self.k.get_verifying_key()
        else:
            self.k = None
            self.K = secret

        self.C = chain
        self.depth = depth
        self.index = index
        self.parent_fpr = fpr
        self.testnet = testnet


    # Internal methods not intended to be called externally
    #
    def hmac(self, data):
        """
        Calculate the HMAC-SHA512 of input data using the chain code as key.

        Returns a tuple of the left and right halves of the HMAC
        """         
        I = hmac.new(self.C, data, hashlib.sha512).digest()
        return (I[:32], I[32:])


    def CKDpriv(self, i):
        """
        Create a child key of index 'i'.

        If the most significant bit of 'i' is set, then select from the
        hardened key set, otherwise, select a regular child key.

        Returns a HDKey constructed with the child key parameters,
        or None if i index would result in an invalid key.
        """
        # Index as bytes, BE
        i_str = struct.pack(">L", i)

        # Data to HMAC
        if i & HD_HARDEN:
            data = b'\0' + self.k.to_string() + i_str
        else:
            data = self.PublicKey() + i_str
        # Get HMAC of data
        (Il, Ir) = self.hmac(data)

        # Construct new key material from Il and current private key
        Il_int = string_to_int(Il)
        if Il_int > CURVE_ORDER:
            return None
        pvt_int = string_to_int(self.k.to_string())
        k_int = (Il_int + pvt_int) % CURVE_ORDER
        if (k_int == 0):
            return None
        secret = (b'\0'*32 + int_to_string(k_int))[-32:]
        
        # Construct and return a new HDKey
        return HDKey(secret=secret, chain=Ir, depth=self.depth+1, index=i, fpr=self.Fingerprint(), public=False, testnet=self.testnet)


    def CKDpub(self, i):
        """
        Create a publicly derived child key of index 'i'.

        If the most significant bit of 'i' is set, this is
        an error.

        Returns a HDKey constructed with the child key parameters,
        or None if index would result in invalid key.
        """

        if i & HD_HARDEN:
            raise Exception("Cannot create a hardened child key using public child derivation")

        # Data to HMAC.  Same as CKDpriv() for public child key.
        data = self.PublicKey() + struct.pack(">L", i)

        # Get HMAC of data
        (Il, Ir) = self.hmac(data)

        # Construct curve point Il*G+K
        Il_int = string_to_int(Il)
        if Il_int >= CURVE_ORDER:
            return None
        point = Il_int*CURVE_GEN + self.K.pubkey.point
        if point == INFINITY:
            return None

        # Retrieve public key based on curve point
        K_i = ecdsa.VerifyingKey.from_public_point(point, curve=SECP256k1)

        # Construct and return a new HDKey
        return HDKey(secret=K_i, chain=Ir, depth=self.depth+1, index=i, fpr=self.Fingerprint(), public=True, testnet=self.testnet)


    # Public methods
    #
    def ChildKey(self, i):
        """
        Create and return a child key of this one at index 'i'.

        The index 'i' should be summed with HD_HARDEN to indicate
        to use the private derivation algorithm.
        """
        if self.public is False:
            return self.CKDpriv(i)
        else:
            return self.CKDpub(i)


    def SetPublic(self):
        "Convert a private HDKey into a public one"
        self.k = None
        self.public = True


    def PrivateKey(self):
        "Return private key as string"
        if self.public:
            raise Exception("Publicly derived deterministic keys have no private half")
        else:
            return self.k.to_string()


    def PublicKey(self,compressed=True):
        "Return compressed public key encoding"
        if compressed:      
            if self.K.pubkey.point.y() & 1:
                ck = b'\3'+int_to_string(self.K.pubkey.point.x())
            else:
                ck = b'\2'+int_to_string(self.K.pubkey.point.x())
            return ck
        else:
            return self.K.to_string()

    def ChainCode(self):
        "Return chain code as string"
        return self.C


    def Identifier(self,compressed=True):
        "Return key identifier as string"
        cK = self.PublicKey(compressed)
        return hashlib.new('ripemd160', sha256(cK).digest()).digest()


    def Fingerprint(self):
        "Return key fingerprint as string"
        return self.Identifier()[:4]


    def Address(self, ip = False):
        "Return compressed public key address"
        addressversion = param_query(NETWORK,'address_version') if not ip else '\x66'
        vh160 = addressversion + self.Identifier()
        return base58.check_encode(vh160)

    def P2WPKHoP2SHAddress(self):
        "Return P2WPKH over P2SH segwit address"
        pk_bytes = self.PublicKey()
        assert len(pk_bytes) == 33 and (pk_bytes.startswith(b"\x02") or pk_bytes.startswith(b"\x03")), \
            "Only compressed public keys are compatible with p2sh-p2wpkh addresses. " \
            "See https://github.com/bitcoin/bips/blob/master/bip-0049.mediawiki."
        pk_hash = hashlib.new('ripemd160', sha256(pk_bytes).digest()).digest()
        push_20 = bytes.fromhex('0014')
        script_sig = push_20 + pk_hash
        address_bytes = hashlib.new('ripemd160', sha256(script_sig).digest()).digest()
        prefix = b"\xc4" if self.testnet else b"\x05"
        return base58.check_encode(prefix + address_bytes)


    def WalletImportFormat(self):
        "Returns private key encoded for wallet import"
        if self.public:
            raise Exception("Publicly derived deterministic keys have no private half")
        addressversion = param_query(NETWORK,'wif_version') if not self.testnet else '\xef'
        raw = addressversion + self.k.to_string() + '\x01' # Always compressed
        return base58.check_encode(raw)


    def ExtendedKey(self, private=True, encoded=True):
        "Return extended private or public key as string, optionally base58 encoded"
        if self.public is True and private is True:
            raise Exception("Cannot export an extended private key from a public-only deterministic key")
        if not self.testnet:
            version = param_query(NETWORK,'hd_prv')[0] if private else param_query(NETWORK,'hd_pub')[0]
        else:
            version = EX_TEST_PRIVATE[0] if private else EX_TEST_PUBLIC[0]
        depth = bytes(bytearray([self.depth]))
        fpr = self.parent_fpr
        child = struct.pack('>L', self.index)
        chain = self.C
        if self.public is True or private is False:
            data = self.PublicKey()
        else:
            data = b'\x00' + self.PrivateKey()
        raw = version+depth+fpr+child+chain+data
        if not encoded:
            return raw
        else:
            return base58.check_encode(raw)

    # RSA Functions
    def GenerateRSA(self):
        bits = 2048
        self.rsa = RSA.generate(bits, randfunc=PRNG(self.Entropy()))

    def RSAPublic(self):
        if self.rsa is None:
            self.GenerateRSA()
        return self.rsa.publickey().exportKey("PEM") 

    def RSAPrivate(self):
        if self.rsa is None:
            self.GenerateRSA()
        return self.rsa.exportKey("PEM")

    def RSAEncrypt(self, msg, recipient_key=None):
        if recipient_key is None:
            recipient_key = RSA.importKey(self.RSAPublic())
        pko = PKCS1_OAEP.new(recipient_key)
        enc = pko.encrypt(msg)
        return base64.b64encode(enc)

    def RSADecrypt(self, enc):
        enc = base64.b64decode(enc)
        pko = PKCS1_OAEP.new(RSA.importKey(self.RSAPrivate()))
        dec = pko.decrypt(enc)
        return six.text_type(dec, encoding='utf8')

    def Sign_Tx(self, data):
        """Digest and then sign the data."""
        digest = hashlib.sha256(hashlib.sha256(data).digest()).digest()
        sig = self.k.sign_digest(digest, sigencode=ecdsa.util.sigencode_der)
        # 01 is hashtype
        return sig + '\01'

    def __repr__(self):
        return "<HDKey hexkey=[%s]>" % b2a_hex(self.Identifier())

    # Debugging methods
    #
    def dump(self):
        "Dump key fields mimicking the BIP0032 test vector format"
        i = {
            "hex" : b2a_hex(self.Identifier()),
            "fpr": b2a_hex(self.Fingerprint()),
            "tao addr":  self.Address(),
            "ip addr": self.Address(True),
            "pubkey":  b2a_hex(self.PublicKey()),
            "xpub hex":  b2a_hex(self.ExtendedKey(private=False, encoded=False)),
            "xpub b58":  self.ExtendedKey(private=False, encoded=True),
            "RSA Pub":  self.RSAPublic(),
        }
        if self.public is False:
            i.update({
                "xprv hex":  b2a_hex(self.ExtendedKey(private=True, encoded=False)),
                "xprv b58":  self.ExtendedKey(private=True, encoded=True),
                "hex":  hexlify(self.PrivateKey()),
                "chaincode":  b2a_hex(self.C),
                "wif":  self.WalletImportFormat(),
                "RSA Prv":  self.RSAPrivate(),
            })
        return i
