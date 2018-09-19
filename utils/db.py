import rocksdb,time,ast
from infiniti.params import *

MAX_RETRY_CREATE_DB = 100

def writebatch():
	return rocksdb.WriteBatch()

def open_db(filename, logger=None, read_only=False):
	db_default_path = (filename, "wallet_test")[filename == ""]
	db_path = db_default_path
	retry_count = 0
	db = None
	save_err=None
	while db is None and retry_count < MAX_RETRY_CREATE_DB:
		try:
			db = rocksdb.DB(db_path, rocksdb.Options(create_if_missing=True), read_only)
		except Exception as err:
			save_err=err
			time.sleep(.1)
		retry_count += 1
	if retry_count == MAX_RETRY_CREATE_DB:
		raise save_err
	return db

def uuid_exists(object_db,uuid):
	try:
		_db = open_db(join_path(DATA_PATH,object_db))
		it = _db.iteritems()
		it.seek(uuid)
		items =   dict(itertools.takewhile(lambda item: item[0].startswith(uuid), it))  
		return len(items) == 0        
	except Exception as err:
		raise err

def get_infiniti_object(object_db,uuid):
	"""
	All Inifiniti objects have a unique UUID, so just dump the object
	"""
	try:
		_db = open_db(join_path(DATA_PATH,object_db))
		it = _db.iteritems()
		it.seek(uuid)
		result = {}
		for key,value in dict(itertools.takewhile(lambda item: item[0].startswith(uuid), it)):
			_uuid,_field = key.split('.')
			_value = value
			result.update = { _field : _value }
		return result
	except Exception as err:
		raise err

def put_infiniti_object(object_db,obj):
	try:
		_db = open_db(join_path(DATA_PATH,object_db))
		wb = writebatch()
		for attr in dir(obj):
			if attr.startswith('_') and not attr.startswith('__'):
				wb.put("{0}.{1}".format(obj.uuid,attr),getattr(obj,attr))
		db.write(wb)
		return True
	except Exception as err:
		raise err

def addresses_by_wallet(wallet,network=NETWORK):
	db = open_db(join_path(join_path(DATA_PATH,network),'addresses'))
	it = db.iteritems()
	it.seek_to_first()
	addresses = []
	for k,v in it:
		w, t, n = v.split('|')
		if w == wallet:
			addresses.append(k)
	return addresses

def balance_by_address(address,network=NETWORK):
	db = open_db(join_path(join_path(DATA_PATH,network),'utxo'))
	it = db.iteritems()
	it.seek_to_first()
	total = 0
	for k,v in it:
		addr,amt = v.split('|')
		if address == addr:
			total += Decimal(amt)
	return total