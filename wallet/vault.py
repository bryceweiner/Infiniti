from wallet import Wallet
from secretsharing import HexToHexSecretSharer
from Crypto import Random
from Crypto.Cipher import AES
import sengen, base64, binascii, json
from infiniti.hdkey import HDKey, HD_HARDEN
from utils.crypto import public_key_to_address
from collections import OrderedDict
from infiniti.params import *

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

	"""
	verwif = None
	num_shares = 0
	shares_required = 0
	pwd_array = 0
	num_addr=0
	seed = None
	nonce = 0
	deposit_addresses = {}
	shares = []
	encrypted = False

	def __init__(self,num_shares=15,shares_required=5,num_addr=0,verwif=None,pwd_array=None):
		if verwif is not None:
			self.verwif = verwif
		else:
			self.verwif = VERWIF
		self.num_addr = num_addr
		self.num_shares = num_shares
		self.shares_required = shares_required
		self.pwd_array = pwd_array
		self.create()

	def create(self):
		if self.pwd_array is not None and (len(self.pwd_array) != self.shares):
			return None

		#Generate the seed
		self.seed, self.nonce = self.create_seed()
		entropy_from_seed = self.entropy_from_seed(self.seed,self.nonce)

		#Generate deposit addresses
		self._root = HDKey.fromEntropy(entropy_from_seed)
		self._primary = self._root.ChildKey(0)
		start_point = self._primary.ChildKey(0+HD_HARDEN)
		self.deposit_addresses = {}
		for k in sorted(self.verwif):
			x = 0
			addr = []
			while x < self.num_addr:
				key = start_point.ChildKey(x)
				addr.append(public_key_to_address(key.PublicKey(),self.verwif[k][0]))
				x += 1
			self.deposit_addresses.update({ k : addr })

		#Split the seed
		self.shares = HexToHexSecretSharer.split_secret(binascii.hexlify(entropy_from_seed),self.shares_required,self.num_shares)

		#Encrypt the shares if a pwd_array is provided
		#Shares are encrypte against passwords in the same order provided
		#This is never revealed during use
		if self.pwd_array is not None:
			self.encrypted = True
			x = 0
			for pwd in pwd_array:
				self.shares[x] = self.AESEncrypt(pwd,self.shares[x])
				x += 1

	def open(self,num_addr,shares, passphrase, pwd_array=None):
		# Rebuild the seed from shares
		_shares = []
		x = 0
		for share in shares:
			if pwd_array is not None:
				_shares.append(self.AESEncrypt(pwd_array[x],share))
			else:
				_shares.append(share)

			x += 1

		entropy_from_seed = HexToHexSecretSharer.recover_secret(_shares)
		w = self.fromEntropy(binascii.unhexlify(entropy_from_seed), passphrase)
		x = 0
		while x < num_addr:
			key = w.create_address(save=True, addr_type=0 )
			x += 1
		return w

	def __repr__(self):
		return json.dumps({
			"deposit_addresses" 	: self.deposit_addresses,
			"shares"				: self.shares,
			"shares_required"		: self.shares_required,
			"encrypted"				: self.encrypted,
		}, sort_keys=True, indent=4)

