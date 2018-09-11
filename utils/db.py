import rocksdb

MAX_RETRY_CREATE_DB = 100

def writebatch():
    return rocksdb.WriteBatch()

def open_db(filename, logger=None):
    db_default_path = (filename, "wallet_test")[filename == ""]
    db_path = db_default_path
    retry_count = 0
    db = None
    while db is None and retry_count < MAX_RETRY_CREATE_DB:
        try:
            db = rocksdb.DB(db_path, rocksdb.Options(create_if_missing=True))
        except Exception as err:
            if logger is not None:
                logger.error("DB: {0}{1}".format(err.errno, err.strerror))
            raise Exception
        retry_count += 1
    return db

