import leveldb, secp256k1, time, sengen, binascii, os
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto import Random
from infiniti.hdkey import HDKey, HD_HARDEN
from secp256k1 import ALL_FLAGS
from utils.crypto import *
from utils.db import *
from infiniti.params import *
import itertools
from binascii import b2a_hex
MAX_ADDRESS = 0xFFFFFFFF

class Key(object):
    _child = None
    _addr_type = None
    key = None
    has_wif = True
    addresses = []
    pubkey = None
    def __init__(self,addr_type,child,key):
        self._child = child
        self._addr_type = addr_type
        self.key = key

    def child(self):
        return int(self._child)

    def addr_type(self):
        return int(self._addr_type)

    def address_type(self):
        if self.addr_type()==0:
            return "deposit"
        elif self.addr_type()==1:
            return "change"
        elif self.addr_type()==2:
            return "staking"
        elif self.addr_type()==3:
            return "dealer"

    def db_key(self):
        return "k.{0}.{1}".format(self.addr_type(),self.child())        

    def db_value(self):
        return "{0}".format(self.key.PublicKey())     

    def address(self, ipaddr = False):
        if ipaddr:
            return self.addresses[1]
        else:
            return self.addresses[0]

    def public_key(self):
        if self.has_wif:
            return self.key.PublicKey()
        else:
            return self.pubkey

    def private_key(self):
        if self.has_wif:
            return self.key.PrivateKey()
        else:
            return 0x00

    def wif(self):
        if self.has_wif:
            return self.key.WalletImportFormat()
        else:
            return ''

    def dump(self):
        return self.key.dump()

    def sign_msg(self, msg):
        if self.has_wif:
            return sign_and_verify(self.key, msg, False)
        else:
            return None

    def verify_msg(self, address, signature, message):
        infiniti = True if address[:1]=='i' else False
        return verify_message(address, signature, message, infinit)

    def save(self,filename):
        if self.has_wif:
            db = open_db(filename)
            db.put(self.db_key(),self.db_value())

    def __repr__(self):
        return "< Wallet.Key - [Address Type]={0}, [Child]={1} >".format(self.addr_type(),self.child())

class Wallet(object):
    seed = None
    encrypted_entropy = None
    Keys = []
    _root = None
    _primary = None
    _filename = None
    _hmac = None
    _fn = None

    def __init__(self,filename=None):
        if filename is not None:
            self._filename = os.path.join(WALLET_PATH, filename)

    @staticmethod
    def create_seed():
        nonce = Random.get_random_bytes(16)
        return sengen.generateSentences(wordlist_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),'100-0.txt'), markovLength=5), nonce

    @staticmethod
    def entropy_from_seed(seed,nonce):
        for x in range(9999):
            _10000_hash = sha256(seed).digest()
        for x in range(14999):
            _25000_hash = sha256(_10000_hash).digest()
        for x in range(49999):
            _50000_hash = sha256(_25000_hash).digest()
        for x in range(74999):
            _75000_hash = sha256(_50000_hash).digest()
        return _10000_hash + _25000_hash + _50000_hash + _75000_hash + nonce

    def encrypt_entropy(self,passphrase,raw):
        self._hmac = sha256(raw).digest()
        self.encrypted_entropy = self.AESEncrypt(passphrase,raw)
        return self.encrypted_entropy

    def decrypt_entropy(self,passphrase):
        d = self.AESDecrypt(passphrase,self.encrypted_entropy)
        if sha256(d).digest() == self._hmac:
            return d
        else:
            raise ValueError("HMAC decrypt failed") 

    def AESEncrypt(self, passphrase, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(passphrase, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def AESDecrypt(self, passphrase, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(passphrase, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (32 - len(s) % 32) * chr(32 - len(s) % 32)

    def _unpad(self,s):
        return s[:-ord(s[len(s)-1:])]

    def _fn(self):
        return binascii.hexlify(self.encrypted_entropy)[:8]

    def fromSeed(self, seed, nonce, passphrase, wallet_path = '.', public=False, testnet=False):
        self.seed = seed
        entropy_from_seed = self.entropy_from_seed(seed,nonce)
        self.encrypt_entropy(sha256(passphrase).digest(),entropy_from_seed)
        self._root = HDKey.fromEntropy(entropy_from_seed, public, testnet)
        self._primary = self._root.ChildKey(0)
        self._filename = os.path.join(WALLET_PATH, self._fn())
        self.save()
        return self

    def fromEntropy(self, entropy, wallet_path = '.', public=False, testnet=False):
        self._root = HDKey.fromEntropy(entropy, public, testnet)
        self._primary = self._root.ChildKey(0)
        return self

    def fromEncryptedEntropy(self, passphrase, entropy, wallet_path = '.', public=False, testnet=False):
        self.encrypted_entropy = entropy
        p = sha256(passphrase).digest()        
        d = self.decrypt_entropy(p)
        self._root = HDKey.fromEntropy(d, public, testnet)
        self._primary = self._root.ChildKey(0)
        return self

    def pubkeysOnly(self):
        """
        Load all of the extended keys from the wallet
        This way we can create any address necessary

        Return a list of HDKeys
        """
        db = open_db(self._filename)
        _root_xpubkey = binascii.unhexlify(db.get('_root'))
        it = db.iteritems()
        prefix = b'k.'
        it.seek(prefix)        
        for key, value in list(itertools.takewhile(lambda item: item[0].startswith(prefix), it)):
            addr,addr_type,child = key.split(".")
            key = Key(int(addr_type),child,None)
            key.pubkey = value
            key.addresses = (public_key_to_address(value,False),public_key_to_address(value,True))
            self.Keys.append(key)
        return self.Keys

    def fromFile(self,passphrase=None):
        self.load(passphrase)
        self.touch()
        return self

    def filename(self):
        return self._filename

    def create_address(self, save=False, addr_type=None , child=0):
        """
            create_address is a little tricky because it automatically moves to m/0h first
            Addresses are then always m/0h/0/x or 1/x for change addresses
        """
        k = self._primary.ChildKey(int(addr_type)+HD_HARDEN)
        if child is None:
            # Generate leaves sequentially
            child = 0
        children = (_k for _k in self.Keys if _k.addr_type() == int(addr_type))
        for c in children:
            child += 1
        # m/0h/k/x
        new_key = k.ChildKey(child)
        key = Key(int(addr_type),child,new_key)
        key.addresses = (new_key.Address(),new_key.Address(True))
        self.Keys.append(key)
        if save:
            key.save(self.filename())
        return key

    def touch(self):
        db = open_db(self._filename)
        db.put("updated",str(int(time.time())))        

    def block_height(self):
        try:
            return int(self.get_status('height'))
        except:
            return param_query(NETWORK,'start_height')

    def get_status(self,k):
        db = open_db(self._filename)
        return db.get(k)

    def update_status(self,k,v):
        db = open_db(self._filename)
        db.put(k,v)

    def dump_addresses(self):
        pass

    def save(self):
        db = open_db(self._filename)
        wb = writebatch()
        wb.put("entropy",self.encrypted_entropy)
        wb.put("hmac",self._hmac)
        wb.put("updated",str(int(time.time())))
        wb.put("_root",binascii.hexlify(self._root.ExtendedKey(private=False, encoded=False)))
        x = 0
        for key in self.Keys:
            wb.put(key.db_key(),key.db_value())
        db.write(wb)

    def load(self,passphrase):
        fn = self._filename
        db = open_db(self._filename)
        try:
            self.updated = db.get("updated")
        except:
            self.updated = 0
        self.encrypted_entropy = db.get("entropy")
        self._hmac = db.get("hmac")
        self.Keys = []
        if passphrase is not None:
            self.fromEncryptedEntropy(passphrase,self.encrypted_entropy) 
        it = db.iteritems()
        prefix = b'k.'
        it.seek(prefix)
        for key, value in list(itertools.takewhile(lambda item: item[0].startswith(prefix), it)):
            addr,addr_type,child = key.split(".")
            if passphrase is not None:
                _k = Key(int(addr_type),int(child),self._primary.ChildKey(int(addr_type)+HD_HARDEN).ChildKey(int(child)))
                _k.addresses = (_k.key.Address(),_k.key.Address(True))
                self.Keys.append(_k) 
                if value == "\x00": # Imported wallet, recreate the missing key
                    db.put(key,_k.public_key())    
            else:
                _k = Key(int(addr_type),int(child),None)
                _k.has_wif = False
                _k.addresses = (_k.key.Address(),_k.key.Address(True))
                self.Keys.append(_k)     
        self._filename = fn
