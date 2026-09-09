from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 5


def validate_image_size(image):
    limit_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if image.size > limit_bytes:
        raise ValidationError(f'La imagen no puede superar {MAX_IMAGE_SIZE_MB} MB.')