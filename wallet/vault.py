from wallet.wallet import Wallet

verwif = (
			{ "DGB" : (30,128) },
			{ "VIA" : (71,199) },
			{ "SYS" : (63,128) },
			{ "BTC" : (0, 128) },
			{ "UNO" : (130,224) },
			{ "IOC" : (103, 231) },
			{ "DOGE" : (30,158) },
			{ "XTO" : (66,76) },
			{ "DASH" : (76,204) },
			{ "MZC" : (50,224) },
			{ "XVG" : (30,158) },
			{ "VTC" : (71,128) },
			{ "XPM" : (23,131) },
			{ "PPC" : (55,183) },
			{ "VRC" : (70,198) },
			{ "FLO" : (35,176) },
			{ "TX" : (66,153) },
			{ "PINK" : (3,131) },
			{ "BLK" : (25,153) },
		)

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

		Provide a two dimensional array of python bytestrings (\x00) and the
		resulting requested addresses will be Base58check encoded for every pair
		supplied, suitable for use on any matching cryptocurrency network as a
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

	def __init__(self,parts,pieces,verwif=None,pwd_array=None):
		pass

	def load(self,filename):
		pass

	def save(self,filename):
		pass


	if len(pwd_array) != parts:
		return None
