import leveldb, secp256k1, time, sengen, binascii, os
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto import Random
from utils.hd_key import HDKey, HD_HARDEN
from secp256k1 import ALL_FLAGS
from utils.messages import *
from utils.db import *
from params import DATA_PATH, START_HEIGHT

MAX_ADDRESS = 0xFFFFFFFF

class Key(object):
    child = None
    change_val = None
    key = None

    def __init__(self,child,change_val,key):
        self.child = child
        self.change_val = change_val
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
        db.Put("k" + str(self.child), str(self.change_val))

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
        return sengen.generateSentences(wordlist_file = path + '/100-0.txt', markovLength=5)

    @staticmethod
    def entropy_from_seed(seed):
        for x in range(999):
            _1000_hash = sha256(seed).digest()
        for x in range(1499):
            _2500_hash = sha256(_1000_hash).digest()
        for x in range(4999):
            _5000_hash = sha256(_2500_hash).digest()
        for x in range(7499):
            _7500_hash = sha256(_5000_hash).digest()
        return _1000_hash + _2500_hash + _5000_hash + _7500_hash

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

    def fromSeed(self, seed, passphrase, wallet_path = '.', public=False, testnet=False):
        self.seed = seed
        entropy_from_seed = self.entropy_from_seed(seed)
        self.encrypt_entropy(sha256(passphrase).digest(),entropy_from_seed)
        self._root = HDKey.fromEntropy(entropy_from_seed, public, testnet)
        self._primary = self._root.ChildKey(0+HD_HARDEN)
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

    def create_address(self, save=False, child=None , change_val=0):
        """
            create_address is a little tricky because it automatically moves to m/0h first
            Addresses are then always m/0h/0/x or 1/x for change addresses
        """
        k = self._primary.ChildKey(change_val)
        if child is None:
            import random
            child = random.randint(0,MAX_ADDRESS)
        # m/0h/k/x
        key = Key(child,change_val,k.ChildKey(child))
        self.Keys.append(key)
        return key

    def touch(self):
        db = open_db(self._filename)
        db.Put("updated",str(int(time.time())))        

    def block_height(self):
        try:
            return int(self.get_status('height'))
        except:
            return START_HEIGHT

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
            wb.Put("k" + str(key.child), str(key.change_val))
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
        if passphrase != '':
            self.fromEncryptedEntropy(passphrase,self.encrypted_entropy) 
            for key, value in db.RangeIter():
                if key[:1] == 'k':
                    self.create_address(False,int(key[1:]),int(value))       
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
