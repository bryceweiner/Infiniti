from taorpc.authproxy import AuthServiceProxy, JSONRPCException
from providers.common import Provider
from operator import itemgetter
from decimal import Decimal, getcontext
getcontext().prec = 8
import os, os.path, sys, json, time, requests
from infiniti.params import *
from utils.encoder import DecimalEncoder,DecimalDecoder
from utils.db import *
from wallet.wallet import Wallet

class Client:
    '''JSON-RPC Client.'''

    def userpass(self, dir='Tao'):
        '''Reads config file for username/password'''

        source = os.path.expanduser(USER_CONFIG_PATH).format(dir,dir.lower())
        dest = open(source, 'r')
        with dest as conf:
            for line in conf:
                if line.startswith('rpcuser'):
                    username = line.split("=")[1].strip()
                if line.startswith("rpcpassword"):
                    password = line.split("=")[1].strip()

        return username, password

    def batch(self, reqs):
        """ send batch request using jsonrpc 2.0 """
        return self.connection.batch_(reqs)

class TaoNode(Client, Provider):
    '''JSON-RPC connection to local Peercoin node'''

    def __init__(self, testnet=False, username=None, password=None,
                 ip=None, port=None, directory=None):
        if not ip:
            self.ip = self.parameters.rpc_url  # default to localhost
        else:
            self.ip = ip

        if not username and not password:
            if not directory:
                try:
                    self.username, self.password = self.userpass()  # try to read from ~/.ppcoin
                except:
                    self.username, self.password = self.parameters.rpc_username, self.parameters.rpc_password  # try some other directory
            else:
                self.username, self.password = self.parameters.rpc_username, self.parameters.rpc_password  # try some other directory
        else:
            self.username = username
            self.password = password
        if testnet is True:
            self.testnet = True
            self.port = 9904
        else:
            self.testnet = False
            self.port = self.parameters.rpc_port
        if port is not None:
            self.port = port
        self.url = 'http://{0}:{1}@{2}:{3}'.format(self.username,self.password,self.ip, self.port)
        self.connection = AuthServiceProxy(self.url)

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            # Python internal stuff
            raise AttributeError
        #if self.__service_name is not None:
        #    name = "%s.%s" % (self.__service_name, name)
        return getattr(AuthServiceProxy(self.url), name)

    def sync(self,fn,passphrase, full=False):
        """
            Traverse the blockchain and update an index of all data belonging to addresses in this wallet
        """
        wallet = Wallet(fn).fromFile(passphrase)
        if full:
            wallet.update_status("height",str(self.parameters.start_height))
            utxo = []
            wallet.update_status("utxo",json.dumps(utxo))
        start_block = wallet.block_height()

        # Unspent transaction outputs
        utxo = json.loads(wallet.get_status("utxo"))
        # Spent transaction outputs
        stxo = []
        addresses= []
        transaction_value = []

        for k in wallet.Keys:
            addresses.append(k.address())

        info = self.getinfo()
        sys.stdout.write('Syncing.')
        sys.stdout.flush()
        wallet.update_status("current","sync")
        try:
            current_status = wallet.get_status("current")
        except:
            current_status = 'ready'
        if current_status == 'sync':
            wallet.update_status("updated",str(int(time.time())))
            while info["blocks"] > start_block:
                block = self.getblockbynumber(start_block)
                if start_block > 0:
                    for tx_hash in block["tx"]:
                        raw = self.getrawtransaction(tx_hash)
                        tx = self.decoderawtransaction(raw)

                        """
                            Let's extract everything we need from this TX 
                            Create an index to this block and store all the data we need
                            Throw out the data we don't need
                        """
                        this_tx_reward = 0
                        this_tx_value = 0
                        this_tx_fees = 0
                        this_tx_unmodified_value = 0
                        this_tx_total_vin = 0
                        this_tx_total_vout = 0
                        proof_of_stake = False
                        # Gather up all of the inputs for addresses we own
                        for txin in tx["vin"]:
                            # Let's look back in time and see if this is our address
                            if not ("coinbase" in txin):
                                raw = self.getrawtransaction(txin["txid"])
                                txin_tx = self.decoderawtransaction(raw)
                                # Now lets loop through the old TX vout's to find us or not
                                for txout in txin_tx["vout"]:
                                    if txout["n"] == txin["vout"]:
                                        # We have a match, this one is ours we spent, so collect it
                                        intersection = list(set(txout["scriptPubKey"]["addresses"]) & set(addresses))
                                        if len(intersection) > 0:
                                            stxo.append({ 
                                                "txhash_in":txin["txid"],
                                                "txhash_out":tx_hash,
                                                "address":intersection[0],
                                                "value":txout["scriptPubKey"]["value"]
                                                })
                                            this_tx_total_vin += Decimal(txout["scriptPubKey"]["value"])
                        # Gather up all of the outputs for addresses we own
                        for txout in tx["vout"]:
                            try:
                                intersection = list(set(txout["scriptPubKey"]["addresses"]) & set(addresses))
                            except:
                                # No addresses in this txout
                                intersection = ()
                            is_mine = (len(intersection)>0)
                            if is_mine:
                                proof_of_stake = (txout['n']==0 and txout['value']==0)
                                if proof_of_stake and (txout['scriptPubKey']['type']=='nonstandard' and txout['value']>0 and txout['scriptPubKey']['asm']==""):
                                    this_tx_reward = txout["value"]
                                else:
                                    for a in intersection:
                                        _new_val = txout["value"]
                                        utxo.append({
                                            "tx_hash" : tx_hash,
                                            "value" : _new_val,
                                            "address" : a,
                                            "height" : block["height"]
                                        })
                                        this_tx_unmodified_value += _new_val
                        this_tx_value = this_tx_unmodified_value - this_tx_total_vin - this_tx_reward
                        this_tx_fees = this_tx_unmodified_value - this_tx_total_vin - this_tx_reward - this_tx_value
                        if this_tx_value > 0:
                            transaction_value.append({
                                "txhash" : tx_hash,
                                "value" : this_tx_value,
                                "fees" : this_tx_fees,
                                "reward" : this_tx_reward
                                })
                info = self.getinfo()
                wallet.update_status("height",str(int(start_block)))
                if wallet.block_height() % 5 == 0: 
                    sys.stdout.write('.')
                    sys.stdout.flush()
                start_block += 1
            for tx in utxo:
                for _tx in stxo:
                    if tx["tx_hash"] == _tx["txhash_in"]:
                        utxo.remove(tx)
            print "\n"
            wallet.update_status("utxo",json.dumps(utxo,cls=DecimalEncoder))     
            wallet.update_status("current","ready")
            wallet.update_status("updated",str(int(time.time())))
            return json.loads(wallet.get_status("utxo"))

    @property
    def is_testnet(self):
        '''check if node is configured to use testnet or mainnet'''

        if self.getinfo()["testnet"] is True:
            return True
        else:
            return False

    @property
    def network(self):
        '''return which network is the node operating on.'''

        if self.is_testnet:
            return "xto"
        else:
            return "xto"
"""
    def listunspent(
        self,
        address="",
        minconf=1,
        maxconf=999999,
    ):
        if address:
            return self.req("listunspent", [minconf, maxconf, [address]])

        return self.req("listunspent", [minconf, maxconf])
"""