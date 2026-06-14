from django.urls import path
from .views import StoreDataUploadView, SalesDataUploadView

  
urlpatterns = [
    path('upload-store-data/', StoreDataUploadView.as_view(), name='store-data-upload'),
    path('upload-sales-data/', SalesDataUploadView.as_view(), name='sales-data-upload'),
]