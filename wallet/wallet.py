import leveldb, secp256k1, time, sengen, binascii, os
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto import Random
from utils.hd_key import HDKey, HD_HARDEN
from secp256k1 import ALL_FLAGS
from utils.crypto import *
from utils.db import *
from infiniti.params import *

MAX_ADDRESS = 0xFFFFFFFF

class Key(object):
    child = None
    addr_type = None
    key = None

    def __init__(self,child,addr_type,key):
        self.child = child
        self.addr_type = addr_type
        self.key = key

    def address(self, ipaddr = False):
        return self.key.Address(ipaddr)

    def public_key(self):
        return self.key.PublicKey()

    def private_key(self):
        return self.key.PrivateKey()

    def wif(self):
        return self.key.WalletImportFormat()

    def dump(self):
        return self.key.dump()

    def sign_msg(self, msg):
        return sign_and_verify(self.key, msg, False)

    def verify_msg(self, address, signature, message):
        infiniti = True if address[:1]=='i' else False
        return verify_message(address, signature, message, infinit)

    def save(self,filename):
        db = open_db(filename)
        db.Put("k_" + str(self.addr_type) + "_" + str(self.child),"m/0h/{0}/{1}: ".format(self.addr_type, self.child))

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
            self._filename = os.path.join(DATA_PATH, filename)

    @staticmethod
    def create_seed(path):
        nonce = Random.get_random_bytes(16)
        return sengen.generateSentences(wordlist_file = path + '/100-0.txt', markovLength=5), nonce

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
        return "wallet_" + binascii.hexlify(self.encrypted_entropy)[:8]

    def fromSeed(self, seed, nonce, passphrase, wallet_path = '.', public=False, testnet=False):
        self.seed = seed
        entropy_from_seed = self.entropy_from_seed(seed,nonce)
        self.encrypt_entropy(sha256(passphrase).digest(),entropy_from_seed)
        self._root = HDKey.fromEntropy(entropy_from_seed, public, testnet)
        self._primary = self._root.ChildKey(0+HD_HARDEN)
        self._filename = os.path.join(DATA_PATH, self._fn())
        self.save()
        return self

    def fromEntropy(self, entropy, wallet_path = '.', public=False, testnet=False):
        self._root = HDKey.fromEntropy(entropy, public, testnet)
        self._primary = self._root.ChildKey(0+HD_HARDEN)
        return self

    def fromEncryptedEntropy(self, passphrase, entropy, wallet_path = '.', public=False, testnet=False):
        self.encrypted_entropy = entropy
        p = sha256(passphrase).digest()        
        d = self.decrypt_entropy(p)
        self._root = HDKey.fromEntropy(d, public, testnet)
        self._primary = self._root.ChildKey(0+HD_HARDEN)
        return self

    def fromExtendedKey(self, xkey, public=False):
        self._root = HDKey.fromExtendedKey(xkey, public)
        self._primary = self._root.ChildKey(0+HD_HARDEN)
        return self

    def fromFile(self,passphrase):
        self.load(passphrase)
        self.touch()
        return self

    def filename(self):
        return self._filename

    def create_address(self, save=False, child=None , addr_type=0):
        """
            create_address is a little tricky because it automatically moves to m/0h first
            Addresses are then always m/0h/0/x or 1/x for change addresses
        """
        k = self._primary.ChildKey(addr_type)
        if child is None:
            # Generate leaves sequentially
            child = 0
            children = (_k for _k in self.Keys if _k.addr_type == addr_type)
            for c in children:
                child += 1
        # m/0h/k/x
        new_key = k.ChildKey(child)
        key = Key(child,addr_type,k.ChildKey(child))
        self.Keys.append(key)
        if save:
            key.save(self.filename())
        return key

    def touch(self):
        db = open_db(self._filename)
        db.Put("updated",str(int(time.time())))        

    def block_height(self):
        try:
            return int(self.get_status('height'))
        except:
            return param_query(NETWORK,'start_height')

    def get_status(self,k):
        db = open_db(self._filename)
        return db.Get(k)

    def update_status(self,k,v):
        db = open_db(self._filename)
        db.Put(k,v)

    def save(self):
        db = open_db(self._filename)
        db.Put("entropy",self.encrypted_entropy)
        db.Put("hmac",self._hmac)
        db.Put("updated",str(int(time.time())))
        x = 0
        wb = leveldb.WriteBatch()
        for key in self.Keys:
            wb.Put("k_" + str(key.child) + "_" + str(key.addr_type),"m/0h/{0}/{1}: ".format(key.addr_type, key.child))
        db.Write(wb)

    def load(self,passphrase):
        fn = self._filename
        db = open_db(self._filename)
        try:
            self.updated = db.Get("updated")
        except:
            self.updated = 0
        self.encrypted_entropy = db.Get("entropy")
        self._hmac = db.Get("hmac")
        self.Keys = []
        if passphrase != '':
            self.fromEncryptedEntropy(passphrase,self.encrypted_entropy) 
            for key, value in db.RangeIter():
                if key[:1] == 'k':
                    addr,addr_type,child = key.split("_")
                    self.create_address(save=False,addr_type=int(addr_type),child=int(child))       
        self._filename = fn

if __name__ == "__main__":
    passphrase = "This is my fairly long but not too long passphrase."

    seed = Wallet().create_seed()
    w = Wallet().fromSeed(seed,passphrase)
    print seed
    fn = w._filename
    print fn
    try:
        w = Wallet().fromFile(fn, passphrase)
    except:
        print "Uh oh! Wallet password failed!"
    w.create_address(save=True)
    for k in w.Keys:
        k.key.dump()
