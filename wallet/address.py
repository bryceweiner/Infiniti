from utils.db import *
from infiniti.params import *
import os
from utils.helpers import *

class Address(object):
	incoming_value = 0
	outgoing_value = 0
	utxo = []
	stxo = []
	pubkey = None
	address = None
	wallet = None

	def __init__(self,address=None,public_key = None,wallet_name=None):
		self.pubkey = public_key
		self.address = address
		self.wallet = wallet_name

	def current_balance(self):
		return self.incoming_value - self.outgoing_value

	def _save_addr_db(self):
		path = join_path(DATA_PATH,NETWORK)
		addrdb = open_db(join_path(path,'addresses'))
		addrdb.put(self.address,"{0}|{1}|{2}".format(self.wallet,str(self.incoming_value),str(self.outgoing_value)))

	def _save_utxo_db(self):
		wb = writebatch()		
		if len(self.stxo)>0:
			for stxo in self.stxo:
				wb.delete(stxo)
		for utxo in self.utxo:
			wb.put(utxo[0],"{0}|{1}".format(self.address,str(utxo[1])))
		path = join_path(DATA_PATH,NETWORK)
		utxodb = open_db(join_path(path,'utxo'))
		utxodb.write(wb)

	def save(self):
		self._save_addr_db()
		self._save_utxo_db()

	def __repr__(self):
		return self.address