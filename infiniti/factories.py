from utils.helpers import *
from utils.db import *
from infiniti.params import *
import json
from utils.encoder import DecimalEncoder

def gettransaction(rpc,tx_hash):
	tx_raw = rpc.getrawtransaction(tx_hash)
	return rpc.decoderawtransaction(tx_raw)

def save_transaction(tx):
	db = open_db(join_path(join_path(DATA_PATH,NETWORK),"tx"))
	db.put(tx["txid"],json.dumps(tx,cls = DecimalEncoder))

def save_block(block):
	db = open_db(join_path(join_path(DATA_PATH,NETWORK),"block"))
	db.put(block["hash"],json.dumps(block,cls = DecimalEncoder))

def process_infiniti(tx):
	db = open_db(join_path(DATA_PATH,'infiniti'))

def process_block(rpc,block_hash,address_list,address_obj):
	"""

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

	 Scan the block for 
		A) Tranascations for addresses in our wallet
		B) Infiniti transactions

	 The way the P2P network is constructed, all messages
	 along the wire are deserialized into programmatic objects
	"""
	_save_block = False
	block = rpc.getblock(block_hash)
	for tx_hash in block['tx']:
		proof_of_stake = False
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
				_save_block = True
			else:
				if 'nonstandard' not in txout["scriptPubKey"]['type']:
					intersection = list(set(txout["scriptPubKey"]["addresses"]) & set(address_list))
					if len(intersection) > 0:
						save_tx = True
						_save_block = True
						for i in intersection:
							index = address_list.index(i)
							address_obj[index].incoming_value += float(txout["value"])
							address_obj[index].utxo.append((tx_hash,float(txout["value"]),block["height"]))
		for txin in tx["vin"]:
			# For each txin, find the original TX and see if
			# it came from one of our addresses and subtract
			# the balance accordingly
            # Let's look back in time and see if this is our address
			if 'txin' in txin:
				txin_tx = gettransaction(rpc,txin["txid"])
				for x in txin_tx['vout']:
					if x['n'] == txin['vout']:
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
			save_transaction(tx)
	if _save_block:
		save_block(block)
	return address_obj

def process_mempool(raw_tx):
	pass
