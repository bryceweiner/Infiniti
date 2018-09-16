import os, time
import ipfsapi

def join_path(path,to_join):
	return os.path.join(path,to_join)

def ipfs_check(logger):
	try:
		ipfs_keystore = os.environ['IPFS_PATH'] + '/keystore'
	except:
		home = os.path.expanduser("~")
		ipfs_keystore = home + '/.ipfs/keystore'
	if os.access(ipfs_keystore, os.W_OK):
		pass
	else:
		# Path exists but we can't access it. Die. In a fire.
		raise IOError
	try:
		api = ipfsapi.connect('127.0.0.1', 5001)
	except:
		# Hmm... we failed... try this...
