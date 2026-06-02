# trade_lens/celery.py
import os
from celery import Celery

# Встановлюємо змінну оточення, щоб Celery знав, де шукати налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

# Створюємо екземпляр додатку Celery
app = Celery('core')

# Завантажуємо налаштування з файлу settings.py.
# namespace='CELERY' означає, що всі налаштування Celery в settings.py
# мають починатися з префіксу CELERY_ (наприклад, CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Цей рядок каже Celery автоматично шукати файли tasks.py у всіх твоїх додатках (наприклад, в analytics)
app.autodiscover_tasks()