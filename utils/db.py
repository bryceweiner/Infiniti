import rocksdb

MAX_RETRY_CREATE_DB = 100

def writebatch():
    return rocksdb.WriteBatch()

def open_db(filename):
    db_default_path = (filename, "wallet_test")[filename == ""]
    db_path = db_default_path
    retry_count = 0
    db = None
    while db is None and retry_count < MAX_RETRY_CREATE_DB:
        try:
            db = rocksdb.DB(db_path, rocksdb.Options(create_if_missing=True))
        except Exception:
            pass
        retry_count += 1
    return db

