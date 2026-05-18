# tasks.py
from celery import shared_task
from .models import Product, Category, Company
import csv
import os


@shared_task(bind=True)
def process_sales_data(self, file_path, company_id):
    # bind=True дозволяє задачі оновлювати свій власний статус (наприклад, прогрес бар)
    company = Company.objects.get(id=company_id)
    products_to_create = []

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Збираємо об'єкти в пам'яті, НЕ зберігаючи їх одразу в базу
                products_to_create.append(
                    Product(
                        name=row['product_name'],
                        sku=row['sku'],
                        current_price=row['price'],
                        # ... інші поля ...
                    )
                )

                # Оновлюємо стан для фронтенду (наприклад, кожні 1000 рядків)
                if len(products_to_create) % 1000 == 0:
                    self.update_state(state='PROGRESS', meta={'processed': len(products_to_create)})

            # Масовий запис у базу одним потужним SQL-запитом
            Product.objects.bulk_create(products_to_create, ignore_conflicts=True)

    except Exception as e:
        # Логування помилки
        return {"status": "error", "message": str(e)}
    finally:
        # Видаляємо тимчасовий файл після обробки
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"status": "success", "processed_rows": len(products_to_create)}