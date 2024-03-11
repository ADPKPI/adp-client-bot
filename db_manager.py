from mysql.connector import pooling

class DBManager:
    _instance = None

    def __new__(cls, dbconfig):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls.pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)
        return cls._instance

    @staticmethod
    def get_connection():
        return DBManager._instance.pool.get_connection()
