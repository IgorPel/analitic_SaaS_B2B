import os

from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    store_name = serializers.CharField(max_length=255)

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1]
        if ext is not '.csv':
            raise serializers.ValidationError('File must be .csv')
        return value
