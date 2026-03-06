import io
import logging

import redis
import requests
from environs import Env
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)


_database = None
env = Env()
env.read_env()


def start(update, context):
    products = get_products(env.str('STRAPI_API_TOKEN'))
    keyboard = [
        [
            InlineKeyboardButton(
                product['title'],
                callback_data=str(product['id']),
            )
        ]
        for product in products['data']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def button(update, context):
    query = update.callback_query
    query.answer()
    products = get_products(env.str('STRAPI_API_TOKEN'))
    selected_product = next(
        (
            product
            for product in products['data']
            if str(product['id']) == str(query.data)
        ),
        None,
    )

    price = selected_product.get('price', 'Цена не указана')
    description = selected_product.get('description', 'Описание отсутствует')
    title = selected_product.get('title', 'Без названия')
    back_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Назад', callback_data='back')]]
    )

    picture = selected_product.get('picture') or {}
    picture_url = picture.get('url')

    if picture_url:
        image_url = f'http://localhost:1337{picture_url}'
        send_product_photo(
            context,
            query.message.chat_id,
            image_url,
            env.str('STRAPI_API_TOKEN'),
            caption=f'{title} ({price} ₽/кг)\n\n{description}',
            reply_markup=back_markup,
        )
        return 'HANDLE_DESCRIPTION'

    query.edit_message_text(
        text=f'{title} ({price} ₽/кг)\n\n{description}',
        reply_markup=back_markup,
    )
    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'back':
        return start(update, context)
    return 'HANDLE_DESCRIPTION'


def send_product_photo(
    context, chat_id, image_url, token, caption=None, reply_markup=None
):
    headers = {'Authorization': f'bearer {token}'}
    response = requests.get(image_url, headers=headers)
    response.raise_for_status()

    image = io.BytesIO(response.content)
    image.name = 'product.jpg'
    image.seek(0)

    context.bot.send_photo(
        chat_id=chat_id,
        photo=image,
        caption=caption,
        reply_markup=reply_markup,
    )


def handle_users_reply(update, context):
    db = get_database_connection()
    chat = update.effective_chat
    if not chat:
        return
    chat_id = chat.id

    if update.message and update.message.text == '/start':
        user_state = 'START'
    else:
        raw_state = db.get(chat_id)
        user_state = raw_state.decode('utf-8') if raw_state else 'START'

    states_functions = {
        'START': start,
        'HANDLE_MENU': button,
        'HANDLE_DESCRIPTION': handle_description,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception:
        logger.exception('Ошибка в handle_users_reply')


def get_products(token):
    headers = {'Authorization': f'bearer {token}'}
    url = 'http://localhost:1337/api/products?populate=picture'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_database_connection():
    global _database
    if _database is None:
        database_password = env.str('DATABASE_PASSWORD')
        database_host = env.str('DATABASE_HOST')
        database_port = env.int('DATABASE_PORT')
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password
        )
    return _database


def run_bot(token):
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    logger.info('TG Bot is starting...')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    bot_token = env.str('TG_BOT_TOKEN')
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    run_bot(bot_token)
