import logging

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from handlers.menu import handle_users_reply


logger = logging.getLogger(__name__)


def error_handler(update, context):
    logger.exception('Ошибка при обработке сообщения', exc_info=context.error)


def run_bot(token):
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_error_handler(error_handler)
    logger.info('TG Bot is starting...')
    updater.start_polling()
    updater.idle()
