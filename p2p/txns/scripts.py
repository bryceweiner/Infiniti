from utils import base58
from params import OP_RETURN_KEY

def pay_to_pubkey_hash(key):
    """
    76       A9             14
    OP_DUP OP_HASH160    Bytes to push

    89 AB CD EF AB BA AB BA AB BA AB BA AB BA AB BA AB BA AB BA   88         AC
                     Data to push                     OP_EQUALVERIFY OP_CHECKSIG
    """
    h = '76a914' + base58.check_decode(key).encode('hex') + '88ac'
    return h.decode('hex')

def op_return_script():
    """
    6a        89 AB CD EF AB BA AB BA AB BA AB BA AB BA AB BA
    OP_RETURN data to push 
    """
    h = '6a' + str(OP_RETURN_KEY).encode('hex')
    return h.decode('hex')
