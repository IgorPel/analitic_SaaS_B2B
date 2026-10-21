import src.analytics.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0004_company_dashboard_preferences'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='dashboard_preferences',
            field=models.JSONField(blank=True, default=src.analytics.models.get_default_dashboard_preferences, help_text='Зберігає конфігурацію віджетів для фронтенду'),
        ),
    ]
