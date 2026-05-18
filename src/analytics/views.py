from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .tasks import process_sales_data
import uuid
import os
from django.conf import settings
from celery.result import AsyncResult
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
        task = process_sales_data.delay(file_path, company_id)

        # Миттєво повертаємо ID задачі клієнту
        return Response({
            "message": "File uploaded successfully. Processing started.",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def cheack_task_status(request, task_id):
    task_id = AsyncResult(task_id)

    response = {
        'task_id': task_id,
        'state': task.status,
        'result': task.result,
    }
    return Response(response)