from django.urls import path
from .views import StoreDataUploadView  # Імпортуємо ваш клас

urlpatterns = [
    # Використовуємо .as_view(), оскільки це клас
    path('upload-store-data/', StoreDataUploadView.as_view(), name='store-data-upload'),
]