import redis

from config import env


_database = None


def get_database_connection():
    global _database
    if _database is None:
        database_password = env.str('DATABASE_PASSWORD')
        database_host = env.str('DATABASE_HOST')
        database_port = env.int('DATABASE_PORT')
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password,
        )
    return _database
