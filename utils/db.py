import rocksdb,time

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

