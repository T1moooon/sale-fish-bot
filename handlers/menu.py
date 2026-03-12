import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import env
from services.media import send_product_photo
from services.strapi import add_product_to_cart, get_cart_items, get_products
from storage.redis_state import get_database_connection


logger = logging.getLogger(__name__)


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
    keyboard.append([InlineKeyboardButton('Моя корзина', callback_data='my_cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def button(update, context):
    query = update.callback_query
    if query.data == 'my_cart':
        query.answer()
        query.message.reply_text(get_cart_text(query.message.chat_id))
        return 'HANDLE_MENU'

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
        [
            [
                InlineKeyboardButton(
                    'Добавить в корзину',
                    callback_data=f'add:{selected_product["documentId"]}',
                )
            ],
            [InlineKeyboardButton('Моя корзина', callback_data='my_cart')],
            [InlineKeyboardButton('Назад', callback_data='back')],
        ]
    )

    picture = selected_product.get('picture') or {}
    picture_url = picture.get('url')

    if picture_url:
        image_url = (
            f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}{picture_url}'
        )
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
    if query.data == 'my_cart':
        query.answer()
        query.message.reply_text(get_cart_text(query.message.chat_id))
        return 'HANDLE_DESCRIPTION'

    if query.data.startswith('add:'):
        product_document_id = query.data.split(':', 1)[1]
        add_product_to_cart(
            env.str('STRAPI_API_TOKEN'),
            query.message.chat_id,
            product_document_id,
        )
        query.answer()
        return 'HANDLE_DESCRIPTION'
    if query.data == 'back':
        query.answer()
        return start(update, context)
    query.answer()
    return 'HANDLE_DESCRIPTION'


def get_cart_text(chat_id):
    cart_items = get_cart_items(env.str('STRAPI_API_TOKEN'), chat_id)
    if not cart_items:
        return 'Ваша корзина пуста'

    lines = ['Ваша корзина:']
    for index, item in enumerate(cart_items, start=1):
        product = item.get('product') or {}
        title = product.get('title')
        quantity_kg = item.get('quantity_kg')
        lines.append(f'{index}. {title} — {quantity_kg} кг')
    return '\n'.join(lines)


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
