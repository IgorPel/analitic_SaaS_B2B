from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .tasks import process_warehouse_data, process_sales_data
import uuid
import os
from django.conf import settings
from celery.result import AsyncResult
from .serializers import FileUploadSerializer, AnalyticsSerializer, RegisterSerializer, UserProfileSerializer
from .models import *
from .analytic_func import *
from django.core.cache import cache
from django.contrib.auth.models import User
from .serializers import ImportIssueSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

def fetch_with_cache(AnalyticClass : BasicAnalytics, prefix, **kwargs):
    key_parts = [prefix]
    key_parts.extend([f"{key}={value}" for key, value in kwargs.items()])
    cache_key = "_".join(key_parts)

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    som = AnalyticClass(**kwargs)
    som.func()
    print(f'Prefix - {prefix}', flush=True)
    print(f'Parametrs {kwargs}', flush=True)

    db_result = som.formulating(**kwargs)

    cache.set(cache_key, db_result, timeout=900)
    return db_result

class AnalyzeBasic(APIView):

    permission_classes = [IsAuthenticated]
    _analyzing_class : BasicAnalytics = None

    def get(self, request):
        serializer = AnalyticsSerializer(
            data=request.query_params,
            context={
                'fields': self._analyzing_class.possible_fields(),
                'name': f"{self._analyzing_class.AnalyzedTable()} in {self._analyzing_class.__name__}"
            }
        )
        serializer.is_valid(raise_exception=True)

        result = fetch_with_cache(
             AnalyticClass=self._analyzing_class,
             prefix=f'analytics:{self._analyzing_class.__name__}',
             **serializer.validated_data
         )

        return Response({
            "data": result,
            "message": "Result",
        }, status=status.HTTP_200_OK)


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

            company = request.user.companies.first()
            file_obj = serializer.validated_data['file']
            store_name = serializer.validated_data['store_name']
            store, created = Store.objects.get_or_create(name=store_name, company=company)


            file_name = f"{uuid.uuid4()}_{file_obj.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            task = process_sales_data.delay(file_path, str(company.id), str(store.id))

            return Response({
                "message": "File uploaded successfully. Processing started.",
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDataUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):

        company = request.user.companies.first()
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_obj = serializer.validated_data['file']
            store_name = serializer.validated_data['store_name']

            store, created = Store.objects.get_or_create(name=store_name, company=company)


            file_name = f"{uuid.uuid4()}_{file_obj.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', file_name)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)

            task = process_warehouse_data.delay(file_path, str(store.id), str(company.id))

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
        'status': task.status,
        'result': task.result if task.status != 'FAILURE' else str(task.result),
    }
    return Response(response)


class DashboardPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.companies.first()
        if not company:
            return Response([])

        prefs = company.dashboard_preferences if isinstance(company.dashboard_preferences, list) else []
        updated = False
        for widget in prefs:
            if isinstance(widget, dict) and not widget.get("id"):
                widget["id"] = str(uuid.uuid4())
                updated = True

        if updated:
            company.dashboard_preferences = prefs
            company.save()

        return Response(company.dashboard_preferences)


    def post(self, request):
        company = request.user.companies.first()
        if not company:
            return Response(
                {"error": "Компанію не знайдено."},
                status=status.HTTP_404_NOT_FOUND
            )
        new_widget = request.data

        if not isinstance(new_widget, dict):
            return Response(
                {"error": "Очікується об'єкт конфігурації віджета."},
                status=status.HTTP_400_BAD_REQUEST
            )


        if "id" not in new_widget:
            new_widget["id"] = str(uuid.uuid4())


        prefs = company.dashboard_preferences if isinstance(company.dashboard_preferences, list) else []
        prefs.append(new_widget)
        company.dashboard_preferences = prefs
        company.save()

        return Response(
            {"status": "created", "widget": new_widget, "data": company.dashboard_preferences},
            status=status.HTTP_201_CREATED
        )

    def patch(self, request):
        company = request.user.companies.first()
        if not company:
            return Response(
                {"error": "Компанію не знайдено."},
                status=status.HTTP_404_NOT_FOUND
            )
        if not isinstance(request.data, list):
            return Response(
                {"error": "Очікується масив об'єктів віджетів."},
                status=status.HTTP_400_BAD_REQUEST
            )

        company.dashboard_preferences = request.data
        company.save()
        return Response({"status": "updated", "data": company.dashboard_preferences})

    def delete(self, request, widget_id=None):
        company = request.user.companies.first()
        if not company:
            return Response(
                {"error": "Компанію не знайдено."},
                status=status.HTTP_404_NOT_FOUND
            )

        target_id = widget_id or request.query_params.get("id") or (
            request.data.get("id") if isinstance(request.data, dict) else None
        )
        if not target_id:
            return Response(
                {"error": "Необхідно вказати ID віджета для видалення."},
                status=status.HTTP_400_BAD_REQUEST
            )

        prefs = company.dashboard_preferences if isinstance(company.dashboard_preferences, list) else []
        initial_len = len(prefs)
        company.dashboard_preferences = [
            w for w in prefs if str(w.get("id")) != str(target_id)
        ]

        if len(company.dashboard_preferences) == initial_len:
            return Response(
                {"error": "Віджет із зазначеним ID не знайдено."},
                status=status.HTTP_404_NOT_FOUND
            )

        company.save()
        return Response(
            {"status": "deleted", "id": str(target_id), "data": company.dashboard_preferences},
            status=status.HTTP_200_OK
        )


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class TaskIssuesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.companies.first()

        tasks_id = request.query_params.getlist('tasks_id')
        queryset = ImportIssue.objects.filter(company=company)

        if tasks_id:
            queryset = queryset.filter(task_id__in=tasks_id)

        serializer = ImportIssueSerializer(queryset, many=True)
        return Response(serializer.data)


