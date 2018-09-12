from utils.db import *
from infiniti.params import *

def gettransaction(rpc,tx_hash):
	tx_raw = rpc.getrawtransaction(tx_hash)
	return rpc.decoderawtransaction(tx_raw)

def save_transaction(tx):
	db = open_db(join_path(join_path(DATA_PATH,NETWORK)),"tx")

def save_block(tx):
	db = open_db(join_path(join_path(DATA_PATH,NETWORK)),"block")

def process_infiniti(tx):
	db = open_db(join_path(DATA_PATH,'infiniti'))

def process_block(rpc,block_hash,address_list,address_obj):
	"""
	 Scan the block for 
		A) Tranascations for addresses in our wallet
		B) Infiniti transactions

	 The way the P2P network is constructed, all messages
	 along the wire are deserialized into programmatic objects
	"""
	save_block = False
	block = rpc.getblock(block_hash)
	for tx_hash in block['tx']:
		save_tx = False
		is_infiniti = False
		tx_addresses = []
		tx = gettransaction(rpc,tx_hash)
		is_infiniti = False
		for txout in tx["vout"]:
			# Let's see if it's an Infiniti TX
			if txout['scriptPubKey']['asm'] == 'OP_RETURN {0}'.format(OP_RETURN_KEY):
				is_infiniti=True
				save_tx = True
				save_block = True
			else:
				if 'nonstandard' not in txout["scriptPubKey"]['type']:
					intersection = list(set(txout["scriptPubKey"]["addresses"]) & set(address_list))
					if len(intersection) > 0:
						save_tx = True
						_save_block = True
						for i in intersection:
							index = address_list.index(i)
							address_obj[index].incoming_value += float(txout["value"])
							address_obj[index].utxo.append((tx_hash,float(txout["value"])))
		for txin in tx["vin"]:
			# For each txin, find the original TX and see if
			# it came from one of our addresses and subtract
			# the balance accordingly
			if 'txin' in txin:
				txin_tx = gettransaction(rpc,txin["txid"])
				for x in txin_tx['vout']:
					# Intersect the address list
					intersection = list(set(x["scriptPubKey"]["addresses"]) & set(address_list))
					if len(intersection) > 0:
						save_tx = True
						_save_block = True
						for i in intersection:
							index = address_list.index(i)
							address_obj[index].outgoing_value += float(x["value"])
							address_obj[index].stxo.append(txin["txid"])

		if is_infiniti:
			process_infiniti(tx)			
		if save_tx:
			#write to disk
			save_transaction()
	if _save_block:
		#write to disk
		save_block(block)
	return address_obj

def process_mempool(raw_tx):
	pass
