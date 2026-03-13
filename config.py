from environs import Env


env = Env()
env.read_env()


TG_BOT_TOKEN = env.str('TG_BOT_TOKEN')

DATABASE_HOST = env.str('DATABASE_HOST')
DATABASE_PORT = env.int('DATABASE_PORT')
DATABASE_PASSWORD = env.str('DATABASE_PASSWORD')

STRAPI_API_TOKEN = env.str('STRAPI_API_TOKEN')
STRAPI_BASE_URL = env.str('STRAPI_BASE_URL', 'http://localhost:1337')
