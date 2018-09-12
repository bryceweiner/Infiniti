class Address(object):
	incoming_value = 0
	outgoing_value = 0
	utxo = []
	
	def __init__(self):
		pass

	def current_balance(self):
		return self.incoming_value - self.outgoing_value