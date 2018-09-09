import ZODB, ZODB.FileStorage, zc.zlibstorage

class Database(object):
	def __init__(self):
		block_db_file = ZODB.FileStorage.FileStorage('blocks.db')
		compressed_storage = zc.zlibstorage.ZlibStorage(block_db_file)
		self.block_db = ZODB.DB(compressed_storage)
		self.block_db.open()

		peers_db_file = ZODB.FileStorage.FileStorage('peers.db')
		compressed_storage = zc.zlibstorage.ZlibStorage(peers_db_file)
		self.peers_db = ZODB.DB(compressed_storage)
		self.peers_db.open()

		wallet_db_file = ZODB.FileStorage.FileStorage('wallet.db')
		compressed_storage = zc.zlibstorage.ZlibStorage(wallet_db_file)
		self.wallet_db = ZODB.DB(compressed_storage)
		self.wallet_db.open()
