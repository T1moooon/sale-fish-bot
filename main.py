import logging

from bot import run_bot
from config import TG_BOT_TOKEN


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    run_bot(TG_BOT_TOKEN)
