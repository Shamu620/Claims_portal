from pathlib import Path
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_supporting_documents(value):
    if value:
        max_size = 5 * 1024 * 1024 #5MB
        file_ext = Path(value.name).suffix.lstrip('.').lower() # removes the leading dot -> 'pdf' || value.split('.')[-1]
        if value.size > max_size:
            raise ValidationError('The document exceeds 5MB')
        if file_ext != 'pdf':
            raise ValidationError('Only pdf files are supported')
        return value

def validate_supporting_images(value):
    if value:
        max_size = 2 * 1024 * 1024  # 2MB
        file_ext=Path(value.name).suffix.lstrip('.').lower()  # removes the leading dot -> 'png' || value.split('.')[-1]
        if value.size > max_size:
            raise ValidationError('The image exceeds 2MB')
        if file_ext not in ['jpeg','jpg','png']:
            raise ValidationError('Only jpg, jpeg and png are supported')
        return value

def validate_time(value):
    if value:
        now = timezone.now().date()
        if value > now:
            raise ValidationError('The time cannot be in future')
        return value



