import os

from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    store_id = serializers.UUIDField()
    company_id = serializers.UUIDField()


    def validate_file(self, value):
        print(value)
        ext = os.path.splitext(value.name)[1]
        print(ext)
        if ext != '.csv':
            raise serializers.ValidationError('File must be .csv')
        return value
