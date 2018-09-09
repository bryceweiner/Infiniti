import sqlite3, time

database_file = "node.sqlite"

class Database(object):
	connectionObject    = None
	cursorObject        = None

	def open(self):
		self.connectionObject    = sqlite3.connect(database_file, timeout=100)
		self.cursorObject        = self.connectionObject.cursor()

	def create(self):
		"""
			Create the SQLite database
		"""
		peer_table = """
			CREATE TABLE 'peers' ( 'ip_address' TEXT, 'port' INTEGER, 'last_seen' INTEGER, 'error' INTEGER,
				PRIMARY KEY(`ip_address`) );
		"""
		block_table = """
			CREATE TABLE `blocks` (
				`hash`	BLOB NOT NULL,
				`version`	BLOB NOT NULL,
				`hashPrev`	BLOB NOT NULL,
				`hashMerkleRoot`	BLOB NOT NULL,
				`nTime`	BLOB NOT NULL,
				`nBits`	BLOB NOT NULL,
				`nNonce` BLOB NOT NULL,
				PRIMARY KEY(`hash`)
			);
		"""
		block_index = """
			CREATE INDEX `block_hash_index` ON `blocks` (`hash` ASC);
		"""
		tx_table = """
			CREATE TABLE tx (
				`block_hash` BLOB NOT NULL,
				`hash` BLOB NOT NULL,
				`version` BLOB NOT NULL,
				`lockTime` BLOB NOT NULL,
				`time` BLOB NOT NULL,
				`data` BLOB NOT NULL,
				`pos` BLOB NOT NULL,
				PRIMARY KEY(`hash`)
			);
		"""		
		tx_index = """
			CREATE INDEX `txin_tx_index` ON `tx` (`hash` ASC);
		"""
		txin_table = """
			CREATE TABLE tx_in (
				`txhash` BLOB NOT NULL,
				`vout` BLOB NOT NULL,
				`scriptSig` BLOB NOT NULL,
				`sequence` BLOB NOT NULL,
				PRIMARY KEY(`vout`,`scriptSig`)				
			);
		"""
		txin_index = """
			CREATE INDEX `txin_txhash_index` ON `tx_in` (`txhash` ASC);
		"""
		txout_table = """
			CREATE TABLE tx_out (
				txhash BLOB NOT NULL,
				value BLOB NOT NULL,
				utxoid BLOB NOT NULL,
				pk_script BLOB NOT NULL,
				PRIMARY KEY(`pk_script`)
			);
		"""
		"""
		"value": 4.02717864,
		 "n": 3,
		 "scriptPubKey": {
			"asm": "",
			"hex": "",
			"type": "nonstandard"
		"""
		txout_index = """
			CREATE INDEX `txout_txhash_index` ON `tx_out` (`txhash` ASC);
		"""
		self.cursorObject.execute("select * from SQLite_master where type=\"table\"")
		tables = self.cursorObject.fetchall()

		peer_table_ok = False
		block_table_ok = False
		tx_table_ok = False
		txin_table_ok = False
		txout_table_ok = False

		# Make sure all our tables exist.
		for table in tables:
			if table[2] == "peers":
				peer_table_ok = True
			if table[2] == "blocks":
				block_table_ok = True
			if table[2] == "tx":
				tx_table_ok = True
			if table[2] == "tx_in":
				txin_table_ok = True
			if table[2] == "tx_out":
				txout_table_ok = True

		if not peer_table_ok:		
			self.cursorObject.execute(peer_table)
			seed_list = [
						('173.249.2.29',15150,0,0),
						('45.32.216.124',15150,0,0),
						('107.191.62.58',15150,0,0),
						('45.33.123.22',15150,0,0),
						('216.164.49.218',15150,0,0),
						]
			sql = """
					INSERT INTO peers (ip_address,port,last_seen,error) VALUES (?,?,?,?);

				"""
			self.cursorObject.executemany(sql,seed_list)
			self.connectionObject.commit()
		if not block_table_ok:		
			self.cursorObject.execute(block_table)
			self.connectionObject.commit()
			self.cursorObject.execute(block_index)
		if not tx_table_ok:		
			self.cursorObject.execute(tx_table)
			self.connectionObject.commit()
			self.cursorObject.execute(tx_index)
		if not txin_table_ok:		
			self.cursorObject.execute(txin_table)
			self.connectionObject.commit()
			self.cursorObject.execute(txin_index)
		if not txout_table_ok:		
			self.cursorObject.execute(txout_table)
			self.connectionObject.commit()
			self.cursorObject.execute(txout_index)
		self.connectionObject.commit()

	def close(self):
		self.connectionObject.close()

	def get_last_block(self):
		self.open()
		cmd = """
			SELECT hash FROM blocks ORDER BY Height DESC LIMIT 1
			"""
		self.threadsafe(cmd,())
		rows = self.cursorObject.fetchall()
		self.close()
		return rows

	def save_block(self,block):
		self.open()
		row_id = None
		rows = self.threadsafe("SELECT hash FROM blocks WHERE hash = ?", (sqlite3.Binary(block.calculate_hash()),))
		for row in rows:
			row_id = row[0]
		if row_id is None:
			cmd = """
				INSERT INTO `blocks` ( `hash`, `version`, `hashPrev`, `hashMerkleRoot`, `nTime`, `nBits`, `nNonce` )
				VALUES (?, ?, ?, ?, ?, ?, ?)
				"""
			self.threadsafe(cmd,(sqlite3.Binary(block.calculate_hash()),sqlite3.Binary(block.version),sqlite3.Binary(block.prev_block),sqlite3.Binary(block.merkle_root),sqlite3.Binary(block.timestamp),sqlite3.Binary(block.bits),sqlite3.Binary(block.nonce),))
			self.connectionObject.commit()
			row_id = c.lastrowid
		self.close()
		return row_id
	def save_tx(self,block_hash,tx,pos):
		self.open()
		row_id = None
		rows = self.threadsafe("SELECT hash FROM tx WHERE hash = ?", (sqlite3.Binary(tx.calculate_hash()),))
		for row in rows:
			row_id = row[0]
		if row_id is None:
			cmd = """
				INSERT OR IGNORE INTO tx (
					`block_hash`,
					`hash`,
					`version`,
					`lockTime`,
					`time`,
					`data`,
					`pos`)
					VALUES (?, ?, ?, ?, ?, ?, ?)
				);
			"""
			self.threadsafe(cmd,(sqlite3.Binary(block_hash),sqlite3.Binary(tx.calculate_hash()),sqlite3.Binary(tx.version),sqlite3.Binary(tx.lock_time),sqlite3.Binary(tx.data,pos)))
			self.connectionObject.commit()
			row_id = c.lastrowid
		self.close()
		return row_id

	def save_txin(self,txin,tx_hash):
		self.open()
		row_id = None
		rows = self.threadsafe("SELECT scriptSig FROM tx_in WHERE scriptSig = ?", (sqlite3.Binary(txin.signature_script),))
		for row in rows:
			row_id = row[0]
		if row_id is None:
			cmd = """
				INSERT OR IGNORE INTO tx_in (
					`txhash`,
					`vout`,
					`scriptSig`,
					`sequence`				
				) VALUES (?, ?, ?, ?)
			"""
			self.threadsafe(cmd,(sqlite3.Binary(tx_hash),sqlite3.Binary(txin.previous_output),sqlite3.Binary(txin.signature_script),sqlite3.Binary(txin.sequence)))
			self.connectionObject.commit()
			row_id = c.lastrowid
		self.close()
		return row_id

	def save_txout(self,txout,tx_hash):
		self.open()
		row_id = None
		rows = self.threadsafe("SELECT pk_script FROM tx_out WHERE pk_script = ?", (sqlite3.Binary(txout.pk_script),))
		for row in rows:
			row_id = row[0]
		if row_id is None:
			cmd = """
				INSERT OR IGNORE INTO tx_out (
					txhash,
					value,
					utxoid,
					pk_script
				) VALUES (?, ?, ?, ?, ?)
			"""
			self.threadsafe(cmd,(sqlite3.Binary(tx_hash),sqlite3.Binary(txout.value),sqlite3.Binary(txout.utxoid),sqlite3.Binary(txout.pk_script)))
			self.connectionObject.commit()
			row_id = c.lastrowid
		self.close()
		return row_id

	def get_peers(self):
		self.open()
		connect_time = 1 * 60 * 60 * 24 * 30 # 30 days 
		#seen_time = 1 * 60 * 5 # 5 minutes 
		last_time = int(time.time()) - connect_time
		#last_seen_time = int(time.time()) - seen_time
		cmd = """
			SELECT DISTINCT ip_address, port FROM peers WHERE error = 0 OR (error=50 OR last_seen < ?)
			"""
		self.threadsafe(cmd,(last_time,))
		rows = self.cursorObject.fetchall()
		self.close()
		return rows

	def threadsafe(self,cmd,args):
		for i in range(300): # give up after 90 seconds
			try:
				return self.cursorObject.execute(cmd, args)
			except sqlite3.OperationalError as e:
				if "locked" in str(e):
					 time.sleep(1)
				else:
					 pass
			else:
				pass

	def update_peer(self,peer,error):
		self.open()
		last_time = int(time.time())
		cmd = """
			UPDATE peers SET last_seen = ?, error = ? WHERE ip_address = ?
			"""
		self.threadsafe(cmd, (last_time,error, peer.peerip))
		self.connectionObject.commit()
		self.close()

	def save_peer(self,addr):
		"""
			Save a peer to the database.

			Peers are retained forever for data collection purposes,
			however they are only retried if seen in the last 30 days.
		"""
		cmd = """
			INSERT OR IGNORE INTO peers(ip_address,port,last_seen, error) VALUES (?, ?, ?, ?)
			"""
		self.open()
		self.threadsafe(cmd,(addr.ip_address, addr.port, addr.timestamp, 0))
		self.connectionObject.commit()
		self.close()
