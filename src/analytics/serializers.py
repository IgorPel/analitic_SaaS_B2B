from collections import defaultdict
from dataclasses import field
from functools import cache

from django.utils import timezone
import os
from .models import Category, ImportTask, Store, Order, Product, Company, ImportIssue
from django.db import transaction

from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import datetime, time, timedelta

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
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        elif start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date cannot be greater than end date.")

        if start_date:
            data['start_date'] = timezone.make_aware(datetime.combine(start_date, time.min))
        if end_date:
            data['end_date'] = timezone.make_aware(datetime.combine(end_date, time.max))

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

        return result


class IssuesSerializer(serializers.Serializer):
    tasks_id = serializers.ListField(child=serializers.UUIDField(), required=False)
    issues = serializers.SerializerMethodField()

    def get_issues(self, obj):
        result = []
        company = obj.companies.first()
        issues = ImportIssue.objects.filter(task__company=company)
        issues = issues.filter(task__id__in=self.tasks_id) if self.tasks_id else issues
        issues = issues.values(
            'id',
            'type',
            'object_id',
            'row_number',
            'raw_data',
            'task__file_name',
        )

        unique_orders = set()
        unique_products = set()
        
        for issue in issues:
            if issue['type'] == 'MISSING_SKU':
                unique_products.add(issue['object_id'])
            else:
                unique_orders.add(issue['object_id'])


        orders_in_db = {
        (o['store_id'], o['order_id']): o
            for o in Order.objects.filter(
                store__company=company,
                order_id__in=unique_orders
            ).values('store_id', 'order_id', 'status', 'order_date', 'customer__email', 'total_price')
        }

        products_in_db = {
            (p['store_id'], p['sku']): p
            for p in Product.objects.filter(
                store__company=company,
                sku__in=unique_products
            ).values('store_id', 'sku', 'name', 'current_price')
        }

        # 4. Групуємо помилки навколо об'єкта (Замовлення або Товару)
        grouped_objects = {}

        for issue in issues:
            obj_id = issue['object_id']
            store_id = issue['task__store_id']
            issue_type = issue['type']
            is_product = (issue_type == 'MISSING_SKU')
            entity_key = ('PRODUCT' if is_product else 'ORDER', store_id, obj_id)

            if entity_key not in grouped_objects:
                grouped_objects[entity_key] = {
                    'entity_type': 'PRODUCT' if is_product else 'ORDER',
                    'object_id': obj_id,
                    'store_id': store_id,
                    'file_name': issue['task__file_name'],
                    'current_db_state': (
                        products_in_db.get((store_id, obj_id))
                        if is_product
                        else orders_in_db.get((store_id, obj_id))
                    ),
                    'conflicts_by_type': defaultdict(lambda: {
                        'issue_ids': [],      
                        'rows': [],           
                        'conflicting_values': [] 
                    })
                }

            conflict_group = grouped_objects[entity_key]['conflicts_by_type'][issue_type]
            conflict_group['issue_ids'].append(issue['id'])
            conflict_group['rows'].append(issue['row_number'])
            if issue['raw_data'] not in conflict_group['conflicting_values']:
                conflict_group['conflicting_values'].append(issue['raw_data'])

        return list(grouped_objects.values())


class OrderSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    order_id = serializers.CharField(max_length=255, required=False)
    customer = serializers.EmailField(max_length=255, required=False) # EmailField краще перевірить пошту!
    store = serializers.UUIDField(required=False)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    order_date = serializers.DateTimeField(required=False)
    status = serializers.ChoiceField(choices=Order.Status.choices, required=False)


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField(max_length=100, required=False)
    sku = serializers.CharField(max_length=100, required=False)
    category = serializers.ListField(child=serializers.CharField(), required=False)
    store = serializers.UUIDField(required=False)
    current_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)


class ResolveIssueSerializer(serializers.Serializer):
    # allow_empty=False автоматично замінює ручну перевірку `if not value:`
    issue_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, required=True)
    entity_type = serializers.ChoiceField(choices=['ORDER', 'PRODUCT'], required=True)
    object_id = serializers.CharField(max_length=255, required=True)
    resolved_data = serializers.DictField(required=False, default=dict)
    store_id = serializers.UUIDField(required=True)

    def validate(self, data):
        company = self.context['request'].user.companies.first()
        entity_type = data['entity_type']
        object_id = data['object_id']
        store_id = data['store_id']
        unique_issue_ids = set(data['issue_ids'])
        raw_resolved_data = data.get('resolved_data', {})

        # 1. Перевіряємо, що всі issue_ids існують і належать цій компанії/магазину/об'єкту
        count = ImportIssue.objects.filter(
            id__in=unique_issue_ids,
            object_id=object_id,
            task__store_id=store_id,  # <-- Кома на місці
            task__company=company
        ).count()

        if count != len(unique_issue_ids):
            raise serializers.ValidationError({"issue_ids": "Some issue IDs do not exist or do not belong to this object."})

        # 2. Твій елегантний тернарний вибір таблиці, поля та серіалізатора:
        table, field, serializer_cls = (
            (Order, 'order_id', OrderSerializer)
            if entity_type == 'ORDER'
            else (Product, 'sku', ProductSerializer)
        )

        # Перевіряємо існування об'єкта саме в цьому магазині та компанії
        if not table.objects.filter(store_id=store_id, store__company=company, **{field: object_id}).exists():
            raise serializers.ValidationError({"object_id": f"{entity_type} with ID '{object_id}' does not exist in this store."})

        # 3. Валідуємо resolved_data через обраний OrderSerializer або ProductSerializer
        nested_serializer = serializer_cls(data=raw_resolved_data)
        nested_serializer.is_valid(raise_exception=True)

        # Записуємо вже очищені дані (де дата — це datetime, а ціна — Decimal)
        data['resolved_data'] = nested_serializer.validated_data
        return data

    def save(self):

        company = self.context['request'].user.companies.first()
        entity_type = self.validated_data['entity_type']
        object_id = self.validated_data['object_id']
        store_id = self.validated_data['store_id']
        resolved_data = self.validated_data.get('resolved_data', {})
        issue_ids = self.validated_data['issue_ids']


        with transaction.atomic():
            issue_ids = ImportIssue.objects.filter(id__in=issue_ids, task__store_id=store_id, task__company=company)

            if entity_type == 'ORDER':

                order = Order.objects.select_for_update().get(store_id=store_id, store__company=company, order_id=object_id)

                if 'customer' in resolved_data:
                    customer, _ = User.objects.get_or_create(company=company, email=resolved_data['customer'])
                    order.customer = customer
                if 'order_date' in resolved_data:
                    order.order_date = resolved_data['order_date']
                if 'status' in resolved_data:
                    order.status = resolved_data['status']

                order.save()

            elif entity_type == 'PRODUCT' and resolved_data:
                product = Product.objects.select_for_update().get(store_id=store_id, sku=object_id)
                if 'name' in resolved_data:
                    product.name = resolved_data['name']
                if 'current_price' in resolved_data:
                    product.current_price = resolved_data['current_price']
                product.save()

                if 'category_ids' in resolved_data:
                    categories = Category.objects.filter(store_id=store_id, id__in=resolved_data['category_ids'])
                    product.category.set(categories)

            # Перевіряємо, чи закрилися всі помилки у відповідних ImportTask
            deleted_count, _ = issue_ids.delete()

            
        cache.clear()
        return {
            "status": "resolved",
            "object_id": object_id,
            "deleted_issues": deleted_count
        }