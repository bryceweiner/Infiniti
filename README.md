![Infiniti](https://puu.sh/BvSoL/b5154a4580.png)
# Infiniti - A cryptocurrency interoperability protocol for Bitcoin-style blockchains
The Infiniti protocol was built after years of research and experimentation with various blockchain-based asset models, from Counterparty to ERC721 tokens.  Each have their pluses and minuses but, on the whole, none have been designed with mainstream consumer applications in mind.  The Infiniti protocol is designed to bridge that gap and allow for quickly scalable applications with a low long term operating cost, and without sacrificing the economic stability of a true cryptocurrency.

The Infiniti protocol will work on those Bitcoin-based blockchains which contain transaction comments.  The structure of the asset protocol is very simple to understand and allows for complexity equal to that of any existing smart contract platform.
### IPFS and Tao clients required
IPFS is integrated directly into the operation of an Infiniti node and is a required component.  Infiniti uses its own IPFS key store to manage objects. If IPFS is already installed for another application it’s recommended Infiniti be installed in a virtual machine, such as Vagrant.  IPFS is used to serve files and objects associated with various Infiniti objects. The [Tao blockchain client](https://github.com/taoblockchain/tao-core) is also required.
```sh
sudo apt-get install ipfs
ipfs init
```
## What Does It Do?
Put simply, Infiniti takes advantage of those aspects of Bitcoin-based cryptocurrencies that make them common and implements them as a multi-blockchain smart contract system with predictable costs of operation.
## How Does It Do This?
To accomplish this, Infiniti provides:
- A means to directly interface with a cryptocurrent peer-to-peer network without the core client
- A means to create and manage hierarchical deterministic wallets which are used to manage identity
- A means to create and manage token assets Tao (XTO) blockchain
- A means to query cryptocurrency blockchains running Infiniti clients other than Tao
- Implementation of a new concept of a "metaproof": a cryptographic proof based on blockchain usage
- Implementation of a method of conducting blockchain-based voting

To create a wallet using the CLI:
```sh
ip_cli createwallet –p “password” > wallet.json
```
To export an Infiniti wallet:
```sh
ip_cli exportwallet –w [data_file] > wallet_[data_file]_export.json
```
To import an Infiniti wallet:
```sh
ip_cli importwallet –f wallet_[data_file]_export.json
```
To create a vault:
```sh
ip_cli createvault > vault_file.json
```
To create a vault for a specific cryptocurrency:
```sh
ip_cli createvault –b XTO > vault_file.json
```
To open a vault:
```sh
echo $p1 = [‘1-share’,…]
ip_cli open vault openvault –p “password” -1 $p1 –n 5
```
To start the node:
```sh
ip_node start
```
To stop the node:
```sh
ip_node stop
```