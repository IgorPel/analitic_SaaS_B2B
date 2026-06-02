from django.test import TestCase

# Create your tests here.
import csv
import io
from django.urls import reverse
from rest_framework.test import APITestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Company, Store, Category, Product


# Змушуємо Celery виконувати задачі синхронно під час тесту
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CatalogUploadIntegrationTest(APITestCase):

    def setUp(self):
        # 1. Готуємо базові дані (Компанія та Магазин)
        self.company = Company.objects.create(name="Test Company")
        self.store = Store.objects.create(name="Test Store", company=self.company)

        # URL твого ендпоінту (наприклад, 'api/upload-catalog/')
        # Якщо ти використовуєш router, тут буде ім'я url-шляху, наприклад 'catalog-upload'
        self.upload_url = reverse('catalog-upload')

    def test_api_upload_creates_categories_and_products(self):
        # 1. Створюємо CSV-файл прямо в оперативній пам'яті
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['product_sku', 'product_name', 'category_path', 'price'])
        # Товар 1: 3 рівні вкладеності
        writer.writerow(['SKU-1001', 'iPhone 15', 'Техніка > Електроніка > Смартфони', '1000.00'])
        # Товар 2: 2 рівні вкладеності (коренева категорія та сама)
        writer.writerow(['SKU-1002', 'Чохол', 'Техніка > Аксесуари', '50.00'])

        # 2. Пакуємо цей текст у віртуальний файл для POST-запиту
        csv_file = SimpleUploadedFile(
            "test_catalog.csv",
            csv_content.getvalue().encode('utf-8'),
            content_type="text/csv"
        )

        # 3. Робимо POST-запит до нашого APIView
        # Важливо: format='multipart' вказує DRF, що ми передаємо форму з файлом (form-data)
        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'store_id': self.store.id,
            'company_id': self.company.id
            # (Якщо ти береш це з токена, замість передачі ID треба просто авторизувати self.client)
        }, format='multipart')

        # 4. Перевіряємо, чи API прийняв файл (зазвичай це статус 200 OK або 202 Accepted)
        self.assertEqual(response.status_code, 200)

        # 5. ПЕРЕВІРКА БАЗИ ДАНИХ (Оскільки CELERY_TASK_ALWAYS_EAGER=True, таска ВЖЕ відпрацювала)

        # А) Перевіряємо категорії (Має бути створено 4 унікальні категорії: Техніка, Електроніка, Смартфони, Аксесуари)
        self.assertEqual(Category.objects.count(), 4)

        # Перевіряємо ієрархію (Дерево)
        root_category = Category.objects.get(name="Техніка")
        self.assertIsNone(root_category.parent)  # У кореня немає батька

        sub_category = Category.objects.get(name="Електроніка")
        self.assertEqual(sub_category.parent, root_category)  # Електроніка лежить в Техніці

        smartphones = Category.objects.get(name="Смартфони")
        self.assertEqual(smartphones.parent, sub_category)  # Смартфони лежать в Електроніці

        accessories = Category.objects.get(name="Аксесуари")
        self.assertEqual(accessories.parent, root_category)  # Аксесуари лежать прямо в Техніці

        # Б) Перевіряємо товари
        self.assertEqual(Product.objects.count(), 2)

        iphone = Product.objects.get(sku='SKU-1001')
        self.assertEqual(iphone.name, 'iPhone 15')
        self.assertEqual(iphone.category, smartphones)  # Товар прив'язався до правильної кінцевої категорії
        self.assertEqual(iphone.store, self.store)  # Товар прив'язався до переданого магазину