from decimal import Decimal

from django.test import TestCase

import csv
import io
from django.urls import reverse
from rest_framework.test import APITestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Company, Customer, ImportIssue, Order, OrderItem, Store, Category, Product, PriceHistory



# Create your tests here.
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CatalogUploadIntegrationTest(APITestCase):

    def setUp(self):
        
        self.company = Company.objects.create(name="Test Company")
        self.store = Store.objects.create(name="Test Store", company=self.company)

       
        self.upload_url = reverse('store-data-upload')

    def test_api_upload_creates_categories_and_products(self):
        
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['product_sku', 'product_name', 'category_path', 'price'])
       
        writer.writerow(['SKU-1001', 'iPhone 15', 'Техніка > Електроніка > Смартфони', '1000.00'])
        
        writer.writerow(['SKU-1002', 'Чохол', 'Техніка > Аксесуари', '50.00'])

       
        csv_file = SimpleUploadedFile(
            "test_catalog.csv",
            csv_content.getvalue().encode('utf-8'),
            content_type="text/csv"
        )

        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'store_id': self.store.id,
            'company_id': self.company.id
        }, format='multipart')

        self.assertEqual(response.status_code, 202, response.data)

        self.assertEqual(Category.objects.count(), 4)

        root_category = Category.objects.get(name="Техніка")
        self.assertIsNone(root_category.parent)
        sub_category = Category.objects.get(name="Електроніка")
        self.assertEqual(sub_category.parent, root_category)  
        smartphones = Category.objects.get(name="Смартфони")
        self.assertEqual(smartphones.parent, sub_category)  
        accessories = Category.objects.get(name="Аксесуари")
        self.assertEqual(accessories.parent, root_category) 

        self.assertEqual(Product.objects.count(), 2)

        iphone = Product.objects.get(sku='SKU-1001')
        self.assertEqual(iphone.name, 'iPhone 15')
   
        self.assertIn(smartphones, iphone.category.all())
        self.assertEqual(iphone.store, self.store) 

@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class SalesUploadIntegrationTest(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.store = Store.objects.create(name="Test Store", company=self.company)
        self.category = Category.objects.create(name="Test Category", company=self.company)

        self.first_product = Product.objects.create(
            sku='SKU-1001',
            name='iPhone 15',
            store=self.store,
            current_price=Decimal('1000.00')
        )

        self.first_product.category.add(self.category)


        self.second_product = Product.objects.create(
            sku='SKU-1002',
            name='Чохол',
            store=self.store,
            current_price=Decimal('50.00')
        )

        self.second_product.category.add(self.category)


        self.upload_url = reverse('sales-data-upload')

    def test_sales_api_customers(self):
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['order_id', 'customer_email', 'product_sku', 'quantity', 'price', 'order_date', 'status'])
        writer.writerow(['ORD-001', 'client0@test.com', 'SKU-1001', '2', '1000.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-001', 'client0@test.com', 'SKU-1002', '1', '50.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1001', '1', '1000.00', '2023-11-02', 'CANCELED'])

        csv_file = SimpleUploadedFile(
            "test_sales.csv",
            csv_content.getvalue().encode('utf-8'),
            content_type="text/csv"
        )

        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'store_id': self.store.id,
            'company_id': self.company.id
        }, format='multipart')

        
        self.assertEqual(response.status_code, 202) 
        self.assertEqual(Customer.objects.count(), 2)
        self.assertTrue(Customer.objects.filter(email='client0@test.com').exists())
        self.assertTrue(Customer.objects.filter(email='client1@test.com').exists())
        

    def test_sales_api_products(self):
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['order_id', 'customer_email', 'product_sku', 'quantity', 'price', 'order_date', 'status'])
            
       
        writer.writerow(['ORD-001', 'client0@test.com', 'SKU-1001', '2', '1000.00', '2023-11-01', 'COMPLETED'])
            
       
        writer.writerow(['ORD-001', 'client0@test.com', 'SKU-1002', '1', '50.00', '2023-11-01', 'COMPLETED'])

        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1001', '1', '1000.00', '2023-11-02', 'CANCELED'])

        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1003', '1', '100.00', '2023-11-02', 'CANCELED'])

        writer.writerow(['ORD-003', 'client2@test.com', 'SKU-1001', '1', '1000.00', '2023-11-02', 'CANCELED'])
        
        writer.writerow(['ORD-004', 'client1@test.com', 'SKU-1001', '1', '900.00', '2023-11-02', 'CANCELED'])
        

        csv_file = SimpleUploadedFile(
            "test_sales.csv",
            csv_content.getvalue().encode('utf-8'),
            content_type="text/csv"
        )

       
        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'store_id': self.store.id,
            'company_id': self.company.id
        }, format='multipart')

        self.assertEqual(response.status_code, 202) 
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(ImportIssue.objects.count(), 1)
        issue = ImportIssue.objects.first()
        self.assertEqual(issue.type, 'MISSING_SKU')
        self.assertEqual(issue.description, 'SKU \'SKU-1003\' created as draft.')
        self.assertEqual(issue.row_number, 4)
        
    
    def test_sales_api_orders(self):
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        writer.writerow(['order_id', 'customer_email', 'product_sku', 'quantity', 'price', 'order_date', 'status'])
            
        writer.writerow(['ORD-001', 'client0@test.com', 'SKU-1001', '2', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-001', 'client1@test.com', 'SKU-1001', '2', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1002', '1', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1001', '3', '10.00',  '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-002', 'client1@test.com', 'SKU-1001', '1', '150.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-003', 'client1@test.com', 'SKU-1002', '1', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-004', 'client1@test.com', 'SKU-1002', '1', '100.00', '2023-11-01', 'CANCELED'])
        writer.writerow(['ORD-005', 'client1@test.com', 'SKU-1002', '1', '100.00', '2023-11-01', 'RETURNED'])
        
        writer.writerow(['ORD-006', 'client0@test.com', 'SKU-1001', '2', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-006', 'client0@test.com', 'SKU-1001', '2', '100.00', '2024-11-01', 'COMPLETED'])
        
        writer.writerow(['ORD-007', 'client0@test.com', 'SKU-1001', '2', '100.00', '2023-11-01', 'COMPLETED'])
        writer.writerow(['ORD-007', 'client0@test.com', 'SKU-1001', '2', '100.00', '2023-11-01', 'CANCELED'])
       

        csv_file = SimpleUploadedFile(
            "test_sales.csv",
            csv_content.getvalue().encode('utf-8'),
            content_type="text/csv"
        )
        
        response = self.client.post(self.upload_url, {
            'file': csv_file,
            'store_id': self.store.id,
            'company_id': self.company.id
        }, format='multipart')


        self.assertEqual(response.status_code, 202)
        self.assertEqual(Order.objects.count(), 7)
        self.assertEqual(ImportIssue.objects.count(), 3)
        self.assertEqual(Order.objects.filter(order_id='ORD-002').first().total_price, Decimal(280.00))
        
        email_issue = ImportIssue.objects.filter(type='CUSTOMER_MISMATCH').first()
        self.assertEqual(email_issue.description, 'Order ORD-001 have more than one customer email.')
        self.assertEqual(email_issue.row_number, 2)
        
        self.assertEqual(Order.objects.filter(order_id='ORD-003').first().status, Order.Status.COMPLETED)
        self.assertEqual(Order.objects.filter(order_id='ORD-004').first().status, Order.Status.CANCELED)
        self.assertEqual(Order.objects.filter(order_id='ORD-005').first().status, Order.Status.RETURNED)

        time_issue = ImportIssue.objects.filter(type='DATE_MISMATCH').first()
        self.assertEqual(time_issue.description, 'Order ORD-006 have different date.')
        self.assertEqual(time_issue.row_number, 10)

        status_issue = ImportIssue.objects.filter(type='STATUS_MISMATCH').first()
        self.assertEqual(status_issue.description, 'Order ORD-007 have different status.')
        self.assertEqual(status_issue.row_number, 12)
