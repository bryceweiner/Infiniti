#from __future__ import print_function
from wallet.wallet import Wallet
from wallet.vault import Vault
from wallet.address import Address
import os,sys,ast,time,base64
import time, json, binascii
from providers.cryptoid import Cryptoid
from providers import TaoNode
from decimal import Decimal, getcontext
from os import listdir
from os.path import isfile, join
from utils.encoder import DecimalEncoder
from infiniti.params import *
from infiniti.logger import *
from utils.crypto import sign_and_verify, verify_message
from p2p import version
from utils.db import *
from infiniti.factories import process_block,process_infiniti
from utils.helpers import *

import qrencode, threading

if USE_RPC:
	_CONNECTION = TaoNode()
else:
	_CONNECTION = Cryptoid(NETWORK)

def importwallet(filename):
	try:
		with open(filename,'r') as infile:
			data = infile.read()
			data = ast.literal_eval(base64.b64decode(data))

			db = open_db(os.path.join(WALLET_PATH,data["wallet"]))
			wb = writebatch()
			wb.put("_root",data["root_id"])
			wb.put("hmac",data["hmac"])
			wb.put("entropy",data["entropy"])
			for k in data["keys"]:
				wb.put("k.{0}.{1}".format(k[0],k[1]),"\x00")
			db.write(wb)
		return "Import successful! Wallet name: {0}".format(import_name)
	except:
		return "Import failed! Filename name: {0}".format(filename)

def exportwallet(wallet):
	db = open_db(os.path.join(WALLET_PATH,wallet))
	it = db.iteritems()
	it.seek_to_first()
	q = { "wallet" : wallet }
	a = []
	for k,v in it:
		if k[0] =="k":
			_,addr_type,child = k.split('.')
			a.append((addr_type,child))
		elif k == "_root":
			q.update({
					"root_id" : v
				})	
		elif k == "entropy":
			q.update({
					"entropy" : v
				})	
		elif k == "hmac":
			q.update({
					"hmac" : v
				})	
	q.update({
			"keys" : a
		})	
			
	result = base64.b64encode(str(q).encode('ascii')).decode('ascii')
	qr_code = "ip://" + result
	qr = qrencode.encode(qr_code,qrencode.QR_ECLEVEL_L)
	qr[2].save('wallet_qr_{0}_{1}_{2}.png'.format(qr[0],qr[1],wallet))
	return result

def get_status(k):
	db = open_db(os.path.join(DATA_PATH,"status"))
	v = db.get(k)
	return v

def getinfo():
	info = _CONNECTION.getinfo()
	infiniti = {
		"infiniti_version" : version,
		"connections" : get_status('connected_peers'),
		"tao_node_info" : info,
	}
	return json.dumps(infiniti,cls=DecimalEncoder, sort_keys=True, indent=4)

def sync(reindex=False):
	syncwallets()

def signmessage(fn,passphrase,address,message):
	w = Wallet(fn).fromFile(passphrase)
	#try:
	infiniti = address[:1]=='i'
	for k in w.Keys:
		if k.address(infiniti) == address:
			sig = k.sign_msg(message)
	return json.dumps({
			"address":k.address(infiniti),
			"message":message,
			"signature":sig
		}, sort_keys=True, indent=4)

def verifymessage(address,message,signature):
	infiniti = address[:1]=='i'
	return json.dumps({ "verified" : verify_message(address, signature, message, prefix=VERWIF['XTO'][0]) } )

def listunspent(fn):
	try:
		w = Wallet(fn).fromFile('')
		utxo = json.loads(w.get_status("utxo"))
		info = _CONNECTION.getinfo()
		for u in utxo:
			u.update({ "confirmations" : str(int(info['blocks']) - int(u["height"]))})
		return json.dumps(utxo, sort_keys=True, indent=4)
	except:
		pass

def createwallet(passphrase):
	seed,nonce = Wallet().create_seed()
	wallet = Wallet().fromSeed(seed,nonce,passphrase,wallet_path=os.path.dirname(os.path.abspath(__file__)))
	wallet.update_status("height",str(_CONNECTION.parameters.start_height))
	wallet.update_status("utxo",json.dumps([]))
	wallet.update_status("current","ready")
	wallet.update_status("updated",str(0))
	d = {
		"passphrase":passphrase,
		"nonce" : binascii.hexlify(nonce),
		"seed":seed,
		"data_file":wallet._fn() 
	}
	return json.dumps(d, sort_keys=True, indent=4)

def addressbalance(address):
	c = _CONNECTION
	balance = 0
	balance += Decimal(c.getbalance(address))
	d = { "balance":balance }
	return json.dumps(d,cls=DecimalEncoder, sort_keys=True, indent=4)

def address_in_wallet(fn,passphrase,address):
	sync(fn,passphrase)
	wallet = Wallet(fn).fromFile(passphrase)
	d = { "address_in_wallet" : False }
	for k in wallet.Keys:
		if k.address() == address:
			d = { "address_in_wallet" : True }
	return json.dumps(d, sort_keys=True, indent=4)

def dumpaddress(fn,passphrase,address):
	wallet = Wallet(fn).fromFile(passphrase)
	for k in wallet.Keys:
		if k.address() == address:
			d = k.dump()
		elif k.address(True) == address:
			d = k.dump()

	return json.dumps(d, sort_keys=True, indent=4)

def listaddresses(fn):
	keys = Wallet(fn).pubkeysOnly()
	a = []
	for k in keys:
		a.append({
			'address_type':k.address_type(),
			NETWORK:k.address(), 
			'infiniti':k.address(True)
			} )
	d = { "addresses" : a }
	return json.dumps(d, sort_keys=True, indent=4)

def newaddress(fn,passphrase,addr_type=0):
	"""
	getnetaddress
	"""
	#try:
	wallet = Wallet(fn).fromFile(passphrase)
	# Address Types
	# addr_type == 0, deposit
	# addr_type == 1, change
	# addr_type == 2, staking
	# addr_type == 3, Dealer
	# Address types aren't programmatically important, but help to organize
	if addr_type is None:
		addr_type = 0
	k = wallet.create_address(save=True,addr_type=addr_type)
	dump = ({
			'address_type':k.address_type(),
			NETWORK : k.address(),
			'infiniti' : k.address(True),
		})
	d = { "address" : dump }
	return json.dumps(d, sort_keys=True, indent=4)
	#except:
	#	return "Password incorrect."

def walletbalance(fn,passphrase):
	sync(fn,passphrase)
	wallet = Wallet(fn).fromFile(passphrase)
	c = _CONNECTION
	balance = 0
	for k in wallet.Keys:
		balance += Decimal(c.getbalance(k.address()))
	d = { "balance": balance }
	return json.dumps(d, cls=DecimalEncoder, sort_keys=True, indent=4)

def listwallets():
	return [f for f in listdir(WALLET_PATH) if True]

def getheight():
	db = open_db(join_path(DATA_PATH,"status"))
	h = db.get('height')
	return int(h) if h is not None else param_query(NETWORK,'start_height')

def putheight(height):
	db = open_db(join_path(DATA_PATH,"status"))
	h = db.put('height',str(height))

def syncwallets(logger=None):
	"""
	For every wallet, find it's height and sync it

	- Get the last block we processed from the status table
	- For each block:
		- Loop through the transactions:
			- If an address involved in either the txin or txout
				are in any of our wallets, save the block and the transaction
			- If the transaction is an Infiniti transaction, save the data
				to tables, as well as the block and transaction
			- Ignore everything else
	- We could do this via the P2P network, but it's more convenient
		through the RPC connection
	"""
	# First, lets gather up the wallet addresses
	wallet_list = [x[0] for x in os.walk(WALLET_PATH)]	
	wallet_list.remove(WALLET_PATH)
	address_obj = []
	address_list = []
	if logger is None:
		print "Gathering addresses."
	else:
		logger.info("{0} sync - Gathering addresses.".format(NETWORK))		
	for wallet_name in wallet_list:
		keys = Wallet(wallet_name).pubkeysOnly()
		for key in keys:
			# address_list is used as an index for intersections
			address_obj.append(Address(key.addresses[0],key.pubkey,os.path.basename(os.path.normpath(wallet_name))))
			address_list.append(key.addresses[0])

	# Loop through blocks from the chaintip to the start height
	end_height = getheight()
	start_block = _CONNECTION.getinfo()["blocks"]
	next_block_hash = _CONNECTION.getblockhash(start_block)
	cur_block = 0xFFFFFFFF
	infiniti_tx = []
	while cur_block > end_height:
		try:
			block = _CONNECTION.getblock(next_block_hash)
		except:
			# This should not happen
			break
		else:
			if logger is None:
				print "Start height: {0}, End height: {1}, Current block: {2}".format(end_height,start_block,block["height"])
			else:
				logger.info("{0} sync - Start height: {1}, End height: {2}, Current block: {3}".format(NETWORK,end_height,start_block,block["height"]))		
			cur_block = block['height']
			address_obj = process_block(_CONNECTION,next_block_hash,address_list,address_obj)
			next_block_hash = block['previousblockhash']
	
	# Now that we've collected all outstanding Infiniti TX, let's process them
	for i in infiniti_tx:
		process_infiniti(i)
	for a in address_obj:
		a.save()

def createvault(shares=15,shares_required=5,num_addr=5,verwif=VERWIF,pwd_array=None):
	v = Vault(shares,shares_required,num_addr,verwif,pwd_array).create()
	return json.dumps(v)


