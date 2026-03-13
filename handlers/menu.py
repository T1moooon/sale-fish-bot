import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import env
from services.media import send_product_photo
from services.strapi import (
    add_product_to_cart,
    clear_cart,
    get_cart_items,
    get_products,
    remove_product_from_cart,
)
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
    if not update.effective_message:
        return 'START'
    update.effective_message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def button(update, context):
    query = update.callback_query
    if not query or not query.message:
        return 'HANDLE_MENU'
    if query.data == 'my_cart':
        query.answer()
        show_cart(query)
        return 'HANDLE_CART'

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
    if not selected_product:
        query.answer()
        return 'HANDLE_MENU'

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
    if not query or not query.message:
        return 'HANDLE_DESCRIPTION'
    if query.data == 'my_cart':
        query.answer()
        show_cart(query)
        return 'HANDLE_CART'

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


def get_cart_keyboard(cart_items):
    buttons = []
    for item in cart_items:
        product = item.get('product') or {}
        product_title = product.get('title')
        product_document_id = product.get('documentId')
        buttons.append(
            [
                InlineKeyboardButton(
                    f'Отказаться: {product_title}',
                    callback_data=f'remove:{product_document_id}',
                )
            ]
        )

    buttons.append(
        [InlineKeyboardButton('Очистить корзину', callback_data='clear_cart')]
    )
    buttons.append([InlineKeyboardButton('Оплатить', callback_data='checkout')])
    buttons.append([InlineKeyboardButton('В меню', callback_data='to_menu')])
    return InlineKeyboardMarkup(buttons)


def show_cart(query):
    if not query.message:
        return
    cart_items = get_cart_items(env.str('STRAPI_API_TOKEN'), query.message.chat_id)
    query.message.reply_text(
        get_cart_text(query.message.chat_id),
        reply_markup=get_cart_keyboard(cart_items),
    )


def handle_cart(update, context):
    query = update.callback_query
    if not query or not query.message:
        return 'HANDLE_CART'
    if query.data == 'to_menu':
        query.answer()
        return start(update, context)

    if query.data == 'clear_cart':
        clear_cart(env.str('STRAPI_API_TOKEN'), query.message.chat_id)
        query.answer()
        show_cart(query)
        return 'HANDLE_CART'

    if query.data == 'checkout':
        query.answer()
        query.message.reply_text('Введите вашу почту для оплаты:')
        return 'WAITING_EMAIL'

    if query.data.startswith('remove:'):
        product_document_id = query.data.split(':', 1)[1]
        remove_product_from_cart(
            env.str('STRAPI_API_TOKEN'),
            query.message.chat_id,
            product_document_id,
        )
        query.answer()
        show_cart(query)
        return 'HANDLE_CART'

    query.answer()
    return 'HANDLE_CART'


def handle_email(update, context):
    if not update.message or not update.message.text:
        return 'HANDLE_WAITING_EMAIL'
    email = update.message.text.strip()
    print(f'Email for payment: {email}')
    update.message.reply_text('Почта получена')
    return 'HANDLE_CART'


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
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception:
        logger.exception('Ошибка в handle_users_reply')
