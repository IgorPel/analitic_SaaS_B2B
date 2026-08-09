from datetime import timezone
import os
from .models import Store, Order, Product

from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    store_id = serializers.UUIDField()
    company_id = serializers.UUIDField()


    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1]
        if ext != '.csv':
            raise serializers.ValidationError('File must be .csv')
        return value


class AnalyticsSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    store_id = serializers.UUIDField()
    product_id = serializers.UUIDField(required=False)
    top = serializers.IntegerField(required=False)
    limits = serializers.IntegerField(required=False)

    statuses = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Order.Status.choices 
        ),
        required=False
    )

    orders_by = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        store_id = data.get('store_id')
        fields = data.get('fields')
        product_id = data.get('product_id')
        orders_by = data.get('orders_by')
        limits = data.get('limits')
        


        if limits is not None and limits < 0:
            raise serializers.ValidationError("Top value cannot be negative.")

        if product_id and Product.objects.filter(id=product_id).count() == 0:
            raise serializers.ValidationError("Product does not exist.")

       
        if fields:
            for field in fields:
                if field not in self.context['fields']:
                    raise serializers.ValidationError(f"{self.context['name']} didn`t have '{field}' field.")

        if orders_by:
            for order_by in orders_by:
                if order_by not in self.context['fields']:
                    raise serializers.ValidationError(f"{self.context['name']} didn`t have '{order_by}' field.")


        if Store.objects.filter(id=store_id).exists() == 0:
            raise serializers.ValidationError("Store does not exist.")

        if start_date and data['start_date'] > timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the future.")

        
        if end_date and data['end_date'] and data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date cannot be greater than end date.")
        
        if not start_date and not end_date:
            data['end_date'] = timezone.now().date()
            data['start_date'] = data['end_date'] - timedelta(days=30) 

        return data

