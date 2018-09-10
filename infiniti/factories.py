def process_block(raw_block):
	"""
	 Scan the block for 
		A) Tranascations for addresses in our wallet
		B) Infiniti transactions

	 It's not obvious, but the object is from p2p.serializers

	 The way the P2P network is constructed, all messages
	 along the wire are deserialized into programmatic objects
	"""
	for tx in raw_block.txns:
		# scan through the txout for an OP_RETURN where the 
		# payload is our key
		pass
def process_mempool(raw_tx):
	pass

def process_infiniti(tx):
	pass