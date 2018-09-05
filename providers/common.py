'''Common provider class with basic features.'''

from decimal import Decimal, getcontext
getcontext().prec = 8
import request

from exceptions import *
from params import _params, param_query
from networks import Constants, net_query

from abc import ABCMeta,abstractmethod

class Provider(object):
    __metaclass__ = ABCMeta

    net = ""

    headers = {"User-Agent": "infiniti-protocol"}

    connection = None

    @staticmethod
    def _netname(name):
        '''resolute network name,
        required because some providers use shortnames and other use longnames.'''

        try:
            _long = net_query(name).name
            short = net_query(name).shortname

        except AttributeError:
            raise UnsupportedNetwork('''This blockchain network is not supported by the Infiniti Protocol, check networks.py for list of supported networks.''')

        return {'long': long,
                'short': short}

    @property
    def network(self):
        '''return network full name'''

        return self._netname(self.net)['long']

    @property
    def parameters(self):
        '''load network parameters.'''

        return param_query(self.network)

    @property
    def network_properties(self):
        '''network parameters [min_fee, denomination, ...]'''

        return net_query(self.network)

    @property
    def is_testnet(self):
        """testnet or not?"""

        if "testnet" in self.network:
            return True
        else:
            return False

