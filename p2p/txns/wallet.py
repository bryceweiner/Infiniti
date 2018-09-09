from node.txns.scripts import pay_to_pubkey_hash, op_return_script
from node.protocol.serializers import TxIn, TxOut, Tx, TxSerializer
from node.protocol.fields import VariableStringField
from binascii import b2a_hex

class Teller(object):
    """
    A Teller can be used to create transactions.

    Currently doesn't deal w/ change
    """

    def __init__(self, key):
        """
        Args:
            private_key: a PrivateKey
        """
        self.key = key
        self.private_key = key.PrivateKey()
        self.public_key = key.PublicKey()
        self.address = key.Address()

    def make_infiniti_tx(self, output, destination, amount, data, fee=100000):
        """
        Create an OP_RETURN transaction.

        Args:
            output: The previous output transaction reference, as an OutPoint structure
            destination: The address to transfer to
            amount: The amount to transfer (in Satoshis)
            data: the data to be hashed into the OP_RETURN
            fee: The amount to reserve for the miners.  Default is 10K Satoshi's.

        Returns:
            A Tx object suitable for serialization / transfer on the wire.
        """
        txin = TxIn()
        txin.previous_output = output
        txin.signature_script = pay_to_pubkey_hash(self.address)

        txout = TxOut()
        txout.value = amount - fee
        txout.pk_script = pay_to_pubkey_hash(destination)

        txout = TxOut()
        txout.value = 0
        txout.pk_script = op_return_script()

        tx = Tx()
        tx.data = data
        tx.tx_in.append(txin)
        tx.tx_out.append(txout)

        raw = TxSerializer().serialize(tx).encode('hex') + "01000000"
        sig = self.key.Sign_Tx(raw.decode('hex'))

        s = VariableStringField()
        s.parse(sig)
        txin.signature_script = s.serialize()

        s = VariableStringField()
        s.parse(b2a_hex(self.PublicKey()))
        txin.signature_script += s.serialize()
        tx.tx_in = [txin]

        return tx

    def make_standard_tx(self, output, destination, amount, fee=10000):
        """
        Create a standard transaction.

        Args:
            output: The previous output transaction reference, as an OutPoint structure
            destination: The address to transfer to
            amount: The amount to transfer (in Satoshis)
            fee: The amount to reserve for the miners.  Default is 10K Satoshi's.

        Returns:
            A Tx object suitable for serialization / transfer on the wire.
        """
        txin = TxIn()
        txin.previous_output = output
        txin.signature_script = pay_to_pubkey_hash(self.key.Address())

        txout = TxOut()
        txout.value = amount - fee
        txout.pk_script = pay_to_pubkey_hash(destination)

        tx = Tx()
        tx.tx_in.append(txin)
        tx.tx_out.append(txout)

        raw = TxSerializer().serialize(tx).encode('hex') + "01000000"
        sig = self.key.Sign_Tx(raw.decode('hex'))

        s = VariableStringField()
        s.parse(sig)
        txin.signature_script = s.serialize()

        s = VariableStringField()
        s.parse(b2a_hex(self.PublicKey()))
        txin.signature_script += s.serialize()
        tx.tx_in = [txin]

        return tx
