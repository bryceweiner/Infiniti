from collections import namedtuple
from decimal import Decimal
from infiniti.exceptions import *

# constants to be consumed by the backend
Constants = namedtuple('Constants', [
    'name',
    'shortname',
    'base58_prefixes',
    'base58_raw_prefixes',
    'bech32_hrp',
    'bech32_net',
    'xkeys_prefix',
    'xpub_version',
    'xprv_version',
    'wif_prefix',
    'from_unit',
    'to_unit',
    'min_tx_fee',
    'tx_timestamp',
    'op_return_max_bytes'
])
networks = (

    # Tao mainnet
    Constants(
        name='Tao',
        shortname='XTO',
        base58_prefixes={
            'T': 'p2pkh',
            '2': 'p2sh',
        },
        base58_raw_prefixes={
            'p2pkh': bytearray(b'\x42'),
            'p2sh': bytearray(b'\x03'),
        },
        bech32_hrp='tc',
        bech32_net='mainnet',
        xkeys_prefix='x',
        xpub_version=b'\x04\x88\xb2\x1e',
        xprv_version=b'\x04\x88\xad\xe4',
        wif_prefix=0x4c,
        from_unit=Decimal('1e-6'),
        to_unit=Decimal('1e6'),
        min_tx_fee=Decimal(0.0002),
        tx_timestamp=True,
        op_return_max_bytes=80
    ),
)

def net_query(name):
    '''Find the NetworkParams for a network by its long or short name. Raises
    UnsupportedNetwork if no NetworkParams is found.
    '''

    for net_params in networks:
        if name in (net_params.name, net_params.shortname,):
            return net_params

    raise UnsupportedNetwork