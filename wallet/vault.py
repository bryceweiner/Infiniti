from wallet.wallet import Wallet
import secretsharing
from Crypto import Random

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

	def __init__(self,parts=15,pieces=5,num_addr=0,verwif=None,pwd_array=None):
		if verwif is not None:
			self.verwif = verwif
		else:
			self.verwif = VERWIF
		self.num_addr = num_addr

	def load(self,filename):
		pass

    def create(self, seed, nonce):
		self.seed, self.nonce = self.create_seed()
        self.seed = seed
        entropy_from_seed = self.entropy_from_seed(seed,nonce)
        self._root = HDKey.fromEntropy(entropy_from_seed, public, testnet)
        self._primary = self._root.ChildKey(0)
        start_point = self._primary.ChildKey(0+HD_HARDEN)

        for vw in self.verwif:
        	x = 0
        	while x < self.num_addr:
        		key = start_point.ChildKey(x)
        return self

	def save(self,filename):
		if len(pwd_array) != parts:
			return None

		max_addr = len(verwif)
		x = 0
		while x < num_addr:
			x++
			for vw in verwif:
