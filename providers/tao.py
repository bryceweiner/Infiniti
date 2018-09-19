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
from infiniti.factories import process_block

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
        raise NotImplementedError

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