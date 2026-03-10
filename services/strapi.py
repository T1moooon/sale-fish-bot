import requests

from config import env


def get_products(token):
    headers = {'Authorization': f'bearer {token}'}
    url = f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}/api/products'
    response = requests.get(url, headers=headers, params={'populate': 'picture'})
    response.raise_for_status()
    return response.json()


def get_or_create_cart(token, tg_id):
    headers = {'Authorization': f'Bearer {token}'}
    cart = get_cart_by_tg_id(headers, tg_id)
    if not cart:
        return create_cart(headers, tg_id)
    return cart


def add_product_to_cart(token, tg_id, product_document_id, quantity_kg=1.0):
    headers = {'Authorization': f'Bearer {token}'}
    cart = get_or_create_cart(token, tg_id)
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
    url = f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}/api/carts'
    params = {'filters[tg_id][$eq]': str(tg_id)}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    carts = response.json().get('data') or []
    return carts[0] if carts else None


def create_cart(headers, tg_id):
    url = f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}/api/carts'
    payload = {'data': {'tg_id': str(tg_id)}}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']


def get_cart_item(headers, cart_document_id, product_document_id):
    url = f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}/api/cart-items'
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
    url = f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}/api/cart-items'
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
    url = (
        f'{env.str("STRAPI_BASE_URL", "http://localhost:1337")}'
        f'/api/cart-items/{cart_item_document_id}'
    )
    payload = {'data': {'quantity_kg': float(quantity_kg)}}
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['data']
