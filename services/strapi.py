import requests

from config import STRAPI_BASE_URL


def build_auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


def get_products(token):
    headers = build_auth_headers(token)
    url = f'{STRAPI_BASE_URL}/api/products'
    response = requests.get(url, headers=headers, params={'populate': 'picture'})
    response.raise_for_status()
    return response.json()


def add_product_to_cart(token, tg_id, product_document_id, quantity_kg=1.0):
    headers = build_auth_headers(token)
    cart = get_cart_by_tg_id(headers, tg_id)
    if not cart:
        cart = create_cart(headers, tg_id)
    cart_item = get_cart_item(
        headers,
        cart['documentId'],
        product_document_id,
    )
    if cart_item:
        new_quantity = float(cart_item.get('quantity_kg') or 0) + float(quantity_kg)
        update_cart_item(headers, cart_item['documentId'], new_quantity)
        return
    create_cart_item(
        headers,
        cart['documentId'],
        product_document_id,
        quantity_kg,
    )


def get_cart_by_tg_id(headers, tg_id):
    url = f'{STRAPI_BASE_URL}/api/carts'
    params = {'filters[tg_id][$eq]': str(tg_id)}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    carts = response.json().get('data') or []
    return carts[0] if carts else None


def create_cart(headers, tg_id):
    url = f'{STRAPI_BASE_URL}/api/carts'
    payload = {'data': {'tg_id': str(tg_id)}}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def get_cart_item(headers, cart_document_id, product_document_id):
    url = f'{STRAPI_BASE_URL}/api/cart-items'
    params = {
        'filters[cart][documentId][$eq]': cart_document_id,
        'filters[product][documentId][$eq]': product_document_id,
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    cart_items = response.json().get('data') or []
    return cart_items[0] if cart_items else None


def create_cart_item(
    headers,
    cart_document_id,
    product_document_id,
    quantity_kg,
):
    url = f'{STRAPI_BASE_URL}/api/cart-items'
    payload = {
        'data': {
            'quantity_kg': float(quantity_kg),
            'cart': cart_document_id,
            'product': product_document_id,
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def update_cart_item(headers, cart_item_document_id, quantity_kg):
    url = f'{STRAPI_BASE_URL}/api/cart-items/{cart_item_document_id}'
    payload = {'data': {'quantity_kg': float(quantity_kg)}}
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(token, tg_id):
    headers = build_auth_headers(token)
    cart = get_cart_by_tg_id(headers, tg_id)
    if not cart:
        return []

    url = f'{STRAPI_BASE_URL}/api/cart-items'
    params = {
        'filters[cart][documentId][$eq]': cart['documentId'],
        'populate': 'product',
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('data') or []


def remove_product_from_cart(token, tg_id, product_document_id):
    headers = build_auth_headers(token)
    cart = get_cart_by_tg_id(headers, tg_id)
    if not cart:
        return
    cart_item = get_cart_item(headers, cart['documentId'], product_document_id)
    if not cart_item:
        return
    delete_cart_item(headers, cart_item['documentId'])


def clear_cart(token, tg_id):
    headers = build_auth_headers(token)
    cart_items = get_cart_items(token, tg_id)
    for cart_item in cart_items:
        delete_cart_item(headers, cart_item['documentId'])


def delete_cart_item(headers, cart_item_document_id):
    url = f'{STRAPI_BASE_URL}/api/cart-items/{cart_item_document_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def save_order_email(token, tg_id, email):
    headers = build_auth_headers(token)
    cart = get_cart_by_tg_id(headers, tg_id)
    if not cart:
        cart = create_cart(headers, tg_id)
    order = get_order_by_cart_document_id(headers, cart['documentId'])
    if order:
        return update_order_email(headers, order['documentId'], email)
    return create_order(headers, cart['documentId'], email)


def get_order_by_cart_document_id(headers, cart_document_id):
    url = f'{STRAPI_BASE_URL}/api/orders'
    params = {'filters[cart][documentId][$eq]': cart_document_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    orders = response.json().get('data') or []
    return orders[0] if orders else None


def create_order(headers, cart_document_id, email):
    url = f'{STRAPI_BASE_URL}/api/orders'
    payload = {
        'data': {
            'email': email,
            'cart': cart_document_id,
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def update_order_email(headers, order_document_id, email):
    url = f'{STRAPI_BASE_URL}/api/orders/{order_document_id}'
    payload = {'data': {'email': email}}
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']
