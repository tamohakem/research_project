import base64
import uuid

from django.core.files.base import ContentFile


def image_from_data_url(data_url, filename_prefix='face-capture'):
    if not data_url:
        return None

    try:
        header, encoded = data_url.split(';base64,', 1)
    except ValueError:
        return None

    extension = 'jpg'
    if header.endswith('/png'):
        extension = 'png'
    elif header.endswith('/webp'):
        extension = 'webp'

    try:
        image_bytes = base64.b64decode(encoded)
    except (TypeError, ValueError):
        return None

    filename = f'{filename_prefix}-{uuid.uuid4().hex}.{extension}'
    return ContentFile(image_bytes, name=filename)
