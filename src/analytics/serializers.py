from django.utils import timezone
import os
from .models import Store, Order, Product, Company, ImportIssue
from django.db import transaction

from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import timedelta

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    store_name = serializers.CharField(max_length=255)

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1]
        if ext != '.csv':
            raise serializers.ValidationError('File must be .csv')
        return value


class AnalyticsSerializer(serializers.Serializer):

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    stores_id = serializers.ListField(child=serializers.UUIDField(), required=False)
    product_id = serializers.UUIDField(required=False)


    top = serializers.IntegerField(required=False)
    limits = serializers.IntegerField(required=False)

    formation = serializers.ChoiceField(
        choices=['LINE', 'BAR', 'PIE', 'TABLE'],
        required=False
    )

    statuses = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Order.Status.choices
        ),
        required=False
    )

    orders_by = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    fields = serializers.ListField(child=serializers.CharField(), required=False, default=list)


    group_and_limit = serializers.JSONField(required=False)
    fill_blank = serializers.JSONField(required=False)
    unique_dates = serializers.BooleanField(required=False)
    graphs = serializers.CharField(max_length=255, required=False)
    x_axis = serializers.CharField(max_length=255, required=False)


    def _check_allowed_fields(self, value_list):
        """Універсальний метод для перевірки списку полів (fields та orders_by)"""
        allowed = self.context.get('fields', [])
        table_name = self.context.get('name', 'Table')
        for field in value_list:
            clean_field = field.lstrip('-')
            if clean_field not in allowed:
                raise serializers.ValidationError(f"{table_name} didn't have '{field}' field.")
        return value_list

    def validate_fields(self, value):
        return self._check_allowed_fields(value)

    def validate_orders_by(self, value):
        return self._check_allowed_fields(value)

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist.")
        return value

    def validate_stores_id(self, value):
        unique_stores = set(value)
        existing_stores = set(Store.objects.filter(id__in=unique_stores).values_list('id', flat=True))
        missing = unique_stores - existing_stores
        if missing:
            raise serializers.ValidationError(f"Stores: {missing}; do not exist.")
        return value

    def validate_start_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the future.")
        return value


    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date and not end_date:
            data['end_date'] = timezone.now().date()
            data['start_date'] = data['end_date'] - timedelta(days=30)
        elif start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date cannot be greater than end date.")

        return data

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(allow_blank=True, required=False, default='')
    company_name = serializers.CharField(required=True, write_only=True)


    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    def validate_company_name(self, value):
        clean_name = value.strip()
        if len(clean_name) == 0:
            raise serializers.ValidationError("Company name cannot be empty.")
        return clean_name

    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        password = validated_data.pop('password')
        email = validated_data.pop('email')

        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                password=password,
                email=email
            )
            company = Company.objects.create(
                name=company_name,
                owner=user
            )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    company_id = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    stores = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'company_id', 'company_name', 'stores']

    def get_company_id(self, obj):
        company = obj.companies.first()
        return str(company.id) if company else None

    def get_company_name(self, obj):
        company = obj.companies.first()
        return company.name if company else None

    def get_stores(self, obj):
        company = obj.companies.first()
        if not company:
            return []
        stores = Store.objects.filter(company=company)
        return [{"id": str(s.id), "name": s.name} for s in stores]


class ImportIssueSerializer(serializers.ModelSerializer):
    tasks_id = serializers.ListField(child=serializers.UUIDField(), required=False)

    class Meta:
        model = ImportIssue
        fields = ['task_id', 'row_number', 'type', 'description']

    def get_issues(self, obj):
        result = []
        company = obj.companies.first()
        if self.tasks_id:
            issues = ImportIssue.objects.filter(company=company, task_id__in=self.tasks_id)
        else:
            issues = ImportIssue.objects.filter(company=company)

        for issue in issues:
            result.append({
                issue.task_id: {
                    'row_number': issue.row_number,
                    'type': issue.type,
                    'description': issue.description
                }
            })


