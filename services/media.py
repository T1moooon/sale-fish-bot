import io

import requests

def send_product_photo(
    context, chat_id, image_url, token, caption=None, reply_markup=None
):
    headers = {'Authorization': f'Bearer {token}'}
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
