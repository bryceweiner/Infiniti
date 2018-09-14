from wallet.wallet import Wallet
from secretsharing import SecretSharer
from Crypto import Random
from Crypto.Cipher import AES

class Vault(Wallet):
	"""
		SSS, with a twist

		Provide a password array which will be used to AES-256 encrypt 
		each resulting part of the shared secret, output in base64

		The decrypted result is an unencrypted Infiniti wallet seed (the seed 
		is encrypted when it is imported later).  The pre-split
		object is a JSON object of two parts: the unencrypted wallet 
		entropy and an array of merkle addresses corresponding to the 
		generated deposit addresses.

		The idea being the Vault creates bank grade security for
		the storage of any cryptocurrency supported by the Infiniti platform,
		which happens to be every cryptocurrency that uses a SECP256k1 curve.

		Provide an array of tickers and the
		resulting requested addresses will be Base58check encoded for every 
		network supplied, suitable for use on the matching cryptocurrency network as a
		cold storage deposit address.

		Pre-split JSON:
		{
			merkle_addresses:[...],
			seed: "..."
		}  
	"""
	verwif = None
	parts = 0
	pieces = 0
	pwd_array = 0
	num_addr=0
	seed = None
	nonce = 0
	depost_addresses = {}
	shares = []

	def __init__(self,parts=15,pieces=5,num_addr=0,verwif=None,pwd_array=None):
		if verwif is not None:
			self.verwif = verwif
		else:
			self.verwif = VERWIF
		self.num_addr = num_addr
		self.parts = parts
		self.pieces = pieces
		self.pwd_array = pwd_array

	def load(self,filename):
		pass

    def create(self, seed, nonce):
    	if self.pwd_array is not None and (len(self.pwd_array) != self.parts):
    		return None

    	#Generate the seed
		self.seed, self.nonce = self.create_seed()
        self.seed = seed
        entropy_from_seed = self.entropy_from_seed(seed,nonce)

        #Generate deposit addresses
        self._root = HDKey.fromEntropy(entropy_from_seed, public, testnet)
        self._primary = self._root.ChildKey(0)
        start_point = self._primary.ChildKey(0+HD_HARDEN)
        self.deposit_addresses = {}
        for k,v in self.verwif:
        	x = 0
        	while x < self.num_addr:
        		key = start_point.ChildKey(x)
        		self.deposit_addresses.update({ k : pubkey_to_address(key.PublicKey(),v[0]) })
        		x += 1

        #Split the seed
		self.shares = SecretSharer.HexToHexSecretSharer(entropy_from_seed,self.pieces,self.parts)

		#Encrypt the parts if a pwd_array is provided
		if self.pwd_array is not None:
			x = 0
			for pwd in pwd_array:
				self.shares[x] = self.AESEncrypt(pwd,self.shares[x])
				x += 1

	def save(self,filename):
		if len(pwd_array) != parts:
			return None

		max_addr = len(verwif)
		x = 0
		while x < num_addr:
			x++
			for vw in verwif:
