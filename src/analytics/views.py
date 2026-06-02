from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .tasks import process_warehouse_data
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
        file_obj = request.FILES.get('file')
        company_id = request.data.get('company_id')

        if not file_obj or not file_obj.name.endswith('.csv'):
            return Response({"error": "Please upload a valid .csv file."}, status=status.HTTP_400_BAD_REQUEST)

        file_name = f"{uuid.uuid4()}_{file_obj.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # ВАЖЛИВО: Викликаємо задачу асинхронно через .delay()
        #task = process_sales_data.delay(file_path, company_id)

        # Миттєво повертаємо ID задачі клієнту
        return Response({
            "message": "File uploaded successfully. Processing started.",
           # "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

class StoreDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):

        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']


            store_name = serializer.validated_data['store_name']
            company_id = serializer.validated_data['company_id']

            file_name = f"{uuid.uuid4()}_{file_obj.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)

            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            task = process_warehouse_data.delay(file_path, store_name, company_id)

            # Миттєво повертаємо ID задачі клієнту
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

class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        thirdy_days = timezone.now() - timedelta(days=30)
        company = request.user.company

        result_aggr = Order.objects.filter(
            customer__company=company,
            created_at__gte=thirdy_days,
            status=Order.Status.COMPLETED
        ).aggregate(
            total_revenue=Sum('total_cost'),
            avg_cheack=Avg('total_cost'),
            order_count=Count('id'),
        )

        revenue_by_day = Order.objects.filter(
            customer__company=company,
            created_at__gte=thirdy_days,
            status=Order.Status.COMPLETED
        ).aggregate(
            date=TruncDate('created_at'),
        ).values('date').aggregate(
            daily_revenue=Sum('total_cost'),
        ).order_by('date')

        top_products = Order.objects.filter(
            categories__company=company,
            order_items__status=Order.Status.COMPLETED,
        ).annotate(
            revenue_generated=Sum(
                F('order_items__quantity') * F('order_items__price_at_purchase')
            )
        ).order_by('revenue_generated')[:5]

        return Response({
            "result_aggr": result_aggr,
            "charts": {
                "revenue_by_day": revenue_by_day
            },
            'top_products': [
                {"name:": p.name, "revenue": p.revenue}
                for p in top_products
            ]
        })