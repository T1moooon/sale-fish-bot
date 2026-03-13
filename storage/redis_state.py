import redis

from config import DATABASE_HOST, DATABASE_PASSWORD, DATABASE_PORT


_database = None


def get_database_connection():
    global _database
    if _database is None:
        _database = redis.Redis(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            password=DATABASE_PASSWORD,
        )
    return _database
