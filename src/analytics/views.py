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
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count
from .models import Order
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from .serializers import FileUploadSerializer

# Create your views here.


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

