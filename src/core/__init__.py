# trade_lens/__init__.py
from .celery import app as celery_app

# Це гарантує, що додаток Celery буде завантажений при старті Django
__all__ = ('celery_app',)