from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0003_alter_company_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='dashboard_preferences',
            field=models.JSONField(blank=True, default=dict, help_text='Зберігає конфігурацію віджетів для фронтенду'),
        ),
    ]
