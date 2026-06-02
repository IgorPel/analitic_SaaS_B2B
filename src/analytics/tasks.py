# tasks.py
from celery import shared_task
from click.core import batch

from .models import Product, Category, Company, Store, Customer
import csv
import os


def build_catogory_map(company_id):
    categories = Category.objects.filter(company_id=company_id)
    id_map = {category.id: category for category in categories}

    category_map = {}

    def full_path(category):
        path_parts = []
        current = category

        while current is not None:
            path_parts.insert(0, current.name)
            current = id_map[current.parent_id]

        return " > ".join(path_parts)

    for category in categories:
        full_path = full_path(category)
        category_map[full_path] = category

    return category_map


@shared_task(bind=True)
def process_warehouse_data(self, file_path, store_id, company_id):

    company = Company.objects.filter(company_id=company_id).first()

    if not company:
        raise Exception("Company not found")

    store = Store.objects.filter(company_id=company_id, store_id=store_id).first()

    if not store:
        return {"status": "error", "message": "Store not found"}

    category_map = build_catogory_map(company_id)
    products = Product.objects.filter(store=store)
    products_map = {product.sku: product for product in products}

    categores_to_create = []
    products_to_create = []
    mistakes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                sku = row['product_sku'].strip()
                raw_category_path = row['category_path'].strip()

                # --- 1. РОБОТА З КАТЕГОРІЯМИ (Level-by-Level) ---
                if raw_category_path not in category_map:
                    # Коли парсер бере цей рядок, він робить split(' > ')
                    part_categories = [cat.strip() for cat in raw_category_path.split('>')]
                    current_path = ""
                    parent_obj = None

                    # Далі він циклом йде по цьому масиву зліва направо
                    for part in part_categories:
                        current_path = f"{current_path} > {part}" if current_path else part

                        if current_path not in category_map:
                            # Створюємо ОДРАЗУ, щоб отримати ID для наступної (дочірньої) категорії
                            new_cat = Category.objects.create(
                                name=part,
                                parent=parent_obj,
                                company=company
                            )
                            category_map[current_path] = new_cat  # Додаємо в словник

                        # Робимо поточну категорію батьком для наступної ітерації
                        parent_obj = category_map[current_path]

                        # --- 2. РОБОТА З ТОВАРАМИ ---
                if sku not in products_map:
                    # Товар абсолютно новий
                    new_product = Product(
                        name=row['product_name'].strip(),
                        sku=sku,
                        category=category_map[raw_category_path],  # Беремо фінальний об'єкт з мапи
                        store=store,
                        current_price=row['price']
                    )
                    products_to_create.append(new_product)
                    # Ставимо тимчасову заглушку, щоб не додати цей же товар двічі з одного файлу
                    products_map[sku] = new_product
                else:
                    # Товар існує. Тут можна реалізувати Upsert (оновлення ціни)
                    existing_product = products_map[sku]

                    # Якщо це реальний об'єкт з бази (а не щойно створена заглушка)
                    if getattr(existing_product, 'id', None):
                        if str(existing_product.current_price) != str(row['price']):
                            # Ціна змінилася! Додаємо логіку PriceHistory
                            pass  # Твоя логіка створення PriceHistory
                            mistakes.append({
                                'type': 'PRICE_UPDATE',
                                'product_sku': sku,
                                'old_price': existing_product.current_price,
                                'new_price': row['price']
                            })
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if len(categores_to_create) > 0:
        for category in categores_to_create:
            category.save()

    if len(products_to_create) > 0:
        Product.objects.bulk_create(products_to_create)

    return {
        "status": "success",
        "info": {
            "products_created": len(products_to_create),
            "category_created": len(categores_to_create)
        },
        "notices": mistakes
    }


"""
@shared_task(bind=True)
def process_sales_data(self, file_path, company_id):
    # bind=True дозволяє задачі оновлювати свій власний статус (наприклад, прогрес бар)
    company = Company.objects.get(id=company_id)
    if not company:
        raise Exception("Company not found")

    stories = set(Store.objects.filter(company=company).values_list('name', flat=True))

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            skus_in_csv = {row['product_sku'] for row in batch}

            reader = csv.DictReader(file)

            set_customers = set()
            dict_order = dict()
            dict_products = dict()
            dict_categories = dict()
            for row in reader:

                if row['store_name'] not in stories:
                    return {"status": "failed",
                            "message": f'Store \"{row['store_name']}\" not found'}

                set_customers.add(row['customer_email'])
                dict_order[row['order_id']] = {
                    'customer_email': row['customer_email'],
                    'store_name': row['store_name']
                }
                dict_products[row['product_sku']] = {
                    'name': row['product_name'],
                    'sku': row['product_sku'],
                    'category': row['product_category'],
                    'store': row['product_store'],
                }

                dict_categories[row['category']] = {
                    'name': row['category'],
                    
                }

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

    return {"status": "success", "processed_rows": len(products_to_create)}"""