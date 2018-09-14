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
from utils.crypto import sign_and_verify, verify_message,public_key_to_address
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

def dumpaddress(fn,passphrase,address,coin):
	wallet = Wallet(fn).fromFile(passphrase)
	d = None
	for k in wallet.Keys:
		if k.address(VERWIF[coin][0]) == address:
			d = k.wif(VERWIF[coin][1])
	if d is None:
		return "ERROR: address not found!"
	else:
		d.update({ 'address':k.address(VERWIF[coin][0]) })
		return json.dumps(d, sort_keys=True, indent=4)

def listaddresses(fn):
	keys = Wallet(fn).pubkeysOnly()
	results = []

	q = [[],[],[],[]]
	for k in keys:
		q[k.addr_type()].append(k)

	for keys in q:
		_at = ''
		_attr = 0
		_chld = 0
		_keys = []
		for key in keys:
			a = []
			_at = key.address_type()
			_attr = key.addr_type()
			_chld = key.child()
			for _k,v in VERWIF.iteritems():
				a.append({
						_k:k.address(v[0])
					})
			a.append({
					'infiniti':k.address(103)
				})
			_keys.append({	'key' 			: 'm/0/{0}h/{1}'.format(_attr,_chld),
							'addresses'		: a,
				})
		_a = {
				'address_type' 	: _at,
				'keys':_keys
			}
		if len(_keys) > 0:
			results.append(_a)
	return json.dumps(results, sort_keys=True, indent=4)

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
	children = (_k for _k in wallet.Keys if _k.addr_type() == int(addr_type))
	child = 0
	for c in children:
		child += 1
	k = wallet.create_address(save=True,addr_type=addr_type,child=child)
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

def createvault(shares,shares_required,num_addr,verwif,pwd_array=None):
	#shares=15,shares_required=5,num_addr=5,verwif=VERWIF,pwd_array=None
	if shares is None:
		shares = 15
	if shares_required is None:
		shares_required = 5
	if num_addr is None:
		num_addr =5
	if verwif is None:
		verwif = VERWIF

	v = Vault(shares,shares_required,num_addr,verwif,pwd_array)
	return v

def openvault(num_addr,shares,passphrase,pwd_array=None):
	# TEST ME
	wallet = Vault().open(num_addr,ast.literal_eval(shares), passphrase, pwd_array=None)
	wallet.update_status("height",str(_CONNECTION.parameters.start_height))
	wallet.update_status("utxo",json.dumps([]))
	wallet.update_status("current","ready")
	wallet.update_status("updated",str(0))
	d = {
		"passphrase":passphrase,
		"data_file":wallet._fn() 
	}
	print json.dumps(d, sort_keys=True, indent=4)
	return listaddresses(wallet._fn())

