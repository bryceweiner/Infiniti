import leveldb
MAX_RETRY_CREATE_DB = 5

def open_db(filename):
    db_default_path = (filename, "wallet_test")[filename == ""]
    db_path = db_default_path
    retry_count = 0
    db = None
    while db is None and retry_count < MAX_RETRY_CREATE_DB:
        try:
            db = leveldb.LevelDB(db_path, create_if_missing=True)
        except leveldb.LevelDBError:
            db_path = db_default_path + str(retry_count)
        retry_count += 1
    return db

