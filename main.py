import logging

from bot import run_bot
from config import env


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    bot_token = env.str('TG_BOT_TOKEN')
    run_bot(bot_token)
