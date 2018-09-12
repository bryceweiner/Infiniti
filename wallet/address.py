class Address(object):
	incoming_value = 0
	outgoing_value = 0
	utxo = []
	pubkey = None
	address = None

	def __init__(self,address=None,public_key = None):
		self.pubkey = public_key
		self.address = address

	def current_balance(self):
		return self.incoming_value - self.outgoing_value

	def __repr__(self):
		return self.address