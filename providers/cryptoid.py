from decimal import Decimal, getcontext
getcontext().prec = 8
from httplib import HTTPResponse
import json
from operator import itemgetter
import requests

#from taopy.structs.transaction import TxIn, Sequence, ScriptSig

#from infiniti.exceptions import InsufficientFunds
from providers.common import Provider


class Cryptoid(Provider):

    '''API wrapper for http://chainz.cryptoid.info blockexplorer.'''

    api_key = '5693a4dae99f'
    api_url_fmt = 'https://chainz.cryptoid.info/{net}/api.dws'
    explorer_url = 'https://chainz.cryptoid.info/explorer/'

    def __init__(self, network):
        self.net = self._netname(network)['short'].lower()
        self.api_url = self.api_url_fmt.format(net=self.format_name(self.net))

    @staticmethod
    def format_name(net):
        '''take care of specifics of cryptoid naming system'''

        #if net.startswith('t') or 'testnet' in net:
        #    net = net[1:] + '-test'
        #else:
        net = net

        return net

    def get_url(self,url):
        '''Perform a GET request for the url and return a dictionary parsed from
        the JSON response.'''

        r = requests.get(url, headers=self.headers)

        if r.status_code != 200:
            r.raise_for_status()
        return r.json()

    def api_req(self, query):

        query = "?q=" + query + "&key=" + self.api_key
        return self.get_url(self.api_url + query)

    def getblockcount(self):

        return int(self.api_req('getblockcount'))

    def getblock(self, blockhash):
        '''query block using <blockhash> as key.'''

        query = 'block.raw.dws?coin={net}&hash={blockhash}'.format(
            net=self.format_name(self.net),
            blockhash=blockhash,
        )
        return self.get_url(self.explorer_url + query)

    def getblockhash(self, blocknum):
        '''get blockhash'''

        query = 'getblockhash' + '&height=' + str(blocknum)
        return self.api_req(query)

    def getdifficulty(self):

        pos_difficulty = self.api_req('getdifficulty')
        return {"proof-of-stake": pos_difficulty}

    def getbalance(self, address):

        query = 'getbalance' + '&a=' + address
        return Decimal(self.api_req(query))

    def getreceivedbyaddress(self, address):

        query = 'getreceivedbyaddress' + "&a=" + address
        return Decimal(self.api_req(query))

    def listunspent(self, address):

        query = 'unspent' + "&active=" + address
        return self.api_req(query)['unspent_outputs']

    def select_inputs(self, address, amount):
        '''select UTXOs'''

        utxos = []
        utxo_sum = Decimal(-0.01)  # starts from negative due to minimal fee
        for tx in sorted(self.listunspent(address=address), key=itemgetter('confirmations')):

                utxos.append(
                    TxIn(txid=tx['tx_hash'],
                         txout=tx['tx_ouput_n'],
                         sequence=Sequence.max(),
                         script_sig=ScriptSig.unhexlify(tx['script']))
                         )

                utxo_sum += Decimal(int(tx['value']) / 100000000)
                if utxo_sum >= amount:
                    return {'utxos': utxos, 'total': utxo_sum}

        if utxo_sum < amount:
            raise InsufficientFunds('Insufficient funds.')

        raise Exception("undefined behavior :.(")

    def getrawtransaction(self, txid, decrypt=0):

        query = 'tx.raw.dws?coin={net}&id={txid}'.format(
            net=self.format_name(self.net),
            txid=txid,
        )
        if not decrypt:
            query += '&hex'
            return self.get_url(self.explorer_url + query)['hex']

        return self.get_url(self.explorer_url + query)

    def listtransactions(self, address):

        query = 'address.summary.dws?coin={net}&id={addr}'.format(
            net=self.format_name(self.net),
            addr=address,
        )
        response = self.get_url(self.explorer_url + query)
        return [tx[1].lower() for tx in response["tx"]]
