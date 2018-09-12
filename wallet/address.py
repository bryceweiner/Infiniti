from utils.db import *
from infiniti.params import *
import os

class Address(object):
	incoming_value = 0
	outgoing_value = 0
	utxo = []
	pubkey = None
	address = None
	wallet = None
	def __init__(self,address=None,public_key = None,wallet=None):
		self.pubkey = public_key
		self.address = address
		self.wallet = wallet

	def current_balance(self):
		return self.incoming_value - self.outgoing_value

	def save(self):
		db.open_db(o)

	def __repr__(self):
		return self.address