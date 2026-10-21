from django.urls import path
from .views import StoreDataUploadView, SalesDataUploadView, cheack_task_status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView
from .views import LTVChartAPIView, RevenueChartAPIView, AnalyzeSalesAPIView, GeneralStatsAPIView, TopProducts, TopCategories, DashboardPreferencesAPIView, UserProfileAPIView, TaskIssuesAPIView


urlpatterns = [
    path('upload-store-data/', StoreDataUploadView.as_view(), name='store-data-upload'),
    path('upload-sales-data/', SalesDataUploadView.as_view(), name='sales-data-upload'),
    path('check-status/<str:task_id>/', cheack_task_status, name='check-task-status'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', UserProfileAPIView.as_view(), name='me'),
    path('ltv/', LTVChartAPIView.as_view(), name='ltv'),
    path('revenue/', RevenueChartAPIView.as_view(), name='revenue'),
    path('analyze-sales/', AnalyzeSalesAPIView.as_view(), name='analyze-sales'),
    path('general-stats/', GeneralStatsAPIView.as_view(), name='general-stats'),
    path('top-products/', TopProducts.as_view(), name='top-products'),
    path('top-categories/', TopCategories.as_view(), name='top-categories'),
    path('dashboard-preferences/', DashboardPreferencesAPIView.as_view(), name='dashboard-preferences'),
    path('dashboard-preferences/<str:widget_id>/', DashboardPreferencesAPIView.as_view(), name='dashboard-preferences-detail'),
    path('task-issues/', TaskIssuesAPIView.as_view(), name='task-issues')
]
