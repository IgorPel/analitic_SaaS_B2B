from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .tasks import process_warehouse_data, process_sales_data
import uuid
import os
from django.conf import settings
from celery.result import AsyncResult
from .serializers import FileUploadSerializer, AnalyticsSerializer
from .analytic_func import *
from django.core.cache import cache


# Create your views here.

def fetch_with_cache(AnalyticClass : BasicAnalytics, prefix, **kwargs):
    key_parts = [prefix]
    key_parts.extend([f"{key}={value}" for key, value in kwargs.items()])
    cache_key = "_".join(key_parts)

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    som = AnalyticClass(**kwargs)
    som.func()
    db_result = som.formulating()

    cache.set(cache_key, db_result, timeout=900)
    return db_result

class AnalyzeBasic(APIView):

    permission_classes = [IsAuthenticated]
    _analyzing_class : BasicAnalytics = None

    def get(self, request):
        serializer = AnalyticsSerializer(data=request.query_params,
                                         context={'fields': self._analyzing_class.possible_fields(),
                                                  'name': f"{self._analyzed_class._meta.verbose_name} in {self._analyzing_class.__name__}"})
        
        if serializer.is_valid():
            start = serializer.validated_data['start_date']
            end = serializer.validated_data['end_date']
            store_id = serializer.validated_data['store_id']
            product_id = serializer.validated_data['product_id']
            statuses = serializer.validated_data['statuses']
            fields = serializer.validated_data['fields']
            orders_by = serializer.validated_data['orders_by']
            limits = serializer.validated_data['limits']

            

            result = fetch_with_cache(AnalyticClass=self._analyzing_class, 
                                      prefix=f'analytics:{self._analyzing_class.__name__}',
                                      product_id=product_id,
                                      store_id=store_id,
                                      start_date=start,
                                      end_date=end,
                                      statuses = statuses,
                                      fields=fields,
                                      orders_by=orders_by,
                                      limits=limits)
            
            return Response({
                "data": result,
                "message": "Result",
            }, status=status.HTTP_200_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RevenueChartAPIView(AnalyzeBasic):
    _analyzing_class = Revenue
class LTVChartAPIView(AnalyzeBasic):
    _analyzing_class = LTV
class AnalyzeSalesAPIView(AnalyzeBasic):
    _analyzing_class = AnalyzeSales
    
class GeneralStatsAPIView(AnalyzeBasic):
    _analyzing_class = GeneralStats
class TopProducts(AnalyzeBasic):
    _analyzing_class = TopsProducts
class TopCategories(AnalyzeBasic):
    _analyzing_class = TopsCategories

class SalesDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']
            store_id = serializer.validated_data['store_id']
            company_id = serializer.validated_data['company_id']

            file_name = f"{uuid.uuid4()}_{file_obj.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            task = process_sales_data.delay(file_path, company_id, store_id)
            
            return Response({
                "message": "File uploaded successfully. Processing started.",
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']
            store_id = serializer.validated_data['store_id']
            company_id = serializer.validated_data['company_id']

            file_name = f"{uuid.uuid4()}_{file_obj.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            task = process_warehouse_data.delay(file_path, store_id, company_id)

            return Response({
                "message": "File uploaded successfully. Processing started.",
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def cheack_task_status(request, task_id):
    task = AsyncResult(task_id)

    response = {
        'task_id': task_id,
        'state': task.status,
        'result': task.result,
    }
    return Response(response)

