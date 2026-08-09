from decimal import Decimal

from django.test import TestCase

import csv
import io
import os
from django.urls import reverse
from rest_framework.test import APITestCase
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Company, Customer, ImportIssue, Order, OrderItem, Store, Category, Product, PriceHistory
from django.utils import timezone
from datetime import timedelta, time, datetime, timezone
from .analytic_func import *




def upload_data(self, url, path, store=None):
    if not store:
        store = self.store

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, path) 
            
    with open(file_path, 'rb') as csv_file:
        response = self.client.post(url, {
            'file': csv_file,
            'store_id': store.id,
            'company_id': self.company.id
        }, format='multipart')
    
    return response


# Create your tests here.
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CatalogUploadIntegrationTest(APITestCase):

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.store = Store.objects.create(name="Test Store", company=self.company)      
        self.upload_url = reverse('store-data-upload')

    def test_api_upload_creates_categories_and_products(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'test_data', 'test_upload_catalog.csv') 
        
        with open(file_path, 'rb') as csv_file:
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
        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_customers.csv')
        self.assertEqual(response.status_code, 202) 
        self.assertEqual(Customer.objects.count(), 3)
        self.assertTrue(Customer.objects.filter(email='client0@test.com').exists())
        self.assertTrue(Customer.objects.filter(email='client1@test.com').exists())
        self.assertTrue(Customer.objects.filter(email='client2@test.com').exists())
        
        

    def test_sales_api_products(self):

        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_product.csv')
        self.assertEqual(response.status_code, 202) 
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(ImportIssue.objects.count(), 1)
        issue = ImportIssue.objects.first()
        self.assertEqual(issue.type, 'MISSING_SKU')
        self.assertEqual(issue.description, 'SKU \'SKU-1003\' created as draft.')
        self.assertEqual(issue.row_number, 4)
        
    
    def test_sales_api_orders(self):

        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_orders.csv')

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


class AnalyticsFuncTest(TestCase):
    
    def setUp(self):
        self.company = Company.objects.create(name="TestCompany")
        self.store = Store.objects.create(company=self.company, name="TestStore0")
        self.upload_url_catalog = reverse('store-data-upload')
        self.upload_url_sales = reverse('sales-data-upload')


    def test_formulating_revenue(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_revenue.csv')
        self.assertEqual(response.status_code, 202)
        
        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_revenue.csv')
        self.assertEqual(response.status_code, 202)

        rev = Revenue(store_id=[self.store.id])
        rev.func()
        #breakpoint()
        result = rev.formulating()
        print(f'\n\n\n\nRevenue list {result}\n\n\n\n')

    def test_formulating_ltv(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_ltv.csv')
        self.assertEqual(response.status_code, 202)
        
        
        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_ltv.csv')
        self.assertEqual(response.status_code, 202)

        rev = LTV(store_id=[self.store.id])
        rev.func()
        #breakpoint()
        result = rev.formulating()
        print(f'\n\n\n\nLTV list: {result}\n\n\n\n')
                

    def test_revenue(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_revenue.csv')
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_revenue.csv')
        self.assertEqual(response.status_code, 202)

        rev = Revenue(store_id=[self.store.id])
        result = rev.func()
        #print(f'Revenue: {result}')
        #result = rev.formulating()

        self.assertEqual(result.count(), 7)
        self.assertEqual(result.get(days=datetime(2026,7,13, tzinfo=timezone.utc)).get('revenue'), Decimal('300'))
        self.assertEqual(result.get(days=datetime(2026,7,14, tzinfo=timezone.utc)).get('revenue'), Decimal('200'))
        self.assertEqual(result.get(days=datetime(2026,7,15, tzinfo=timezone.utc)).get('revenue'), Decimal('100'))
        self.assertNotIn(datetime(2026,7,16, tzinfo=timezone.utc), result)
        self.assertNotIn(datetime(2026,7,17, tzinfo=timezone.utc), result)
        self.assertEqual(result.get(days=datetime(2026,7,18, tzinfo=timezone.utc)).get('revenue'), Decimal('200'))
        self.assertEqual(result.get(days=datetime(2026,7,19, tzinfo=timezone.utc)).get('revenue'), Decimal('300'))
        self.assertEqual(result.get(days=datetime(2026,7,20, tzinfo=timezone.utc)).get('revenue'), Decimal('300'))
        self.assertEqual(result.get(days=datetime(2026,7,21, tzinfo=timezone.utc)).get('revenue'), Decimal('600'))
    

    def test_ltv(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_ltv.csv')
        self.assertEqual(response.status_code, 202)

        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_ltv.csv')
        self.assertEqual(response.status_code, 202)

        ltv = LTV(stores_id=[self.store.id])
        result = ltv.func()
        #print(f'LTV: {result}')
        #result = ltv.formulating()
        
        self.assertEqual(result.count(), 13)
        customer = result.filter(customer=Customer.objects.get(email='customer0@test.com'))
        self.assertEqual(customer.count(), 3)
        revenues = [cust['cumulative_revenue'] for cust in customer]
        self.assertEqual(revenues[0], Decimal('100'))
        self.assertEqual(revenues[1], Decimal('200'))
        self.assertEqual(revenues[2], Decimal('300'))


        customer = result.filter(customer=Customer.objects.get(email='customer1@test.com'))
        self.assertEqual(customer.count(), 3)
        revenues = [cust['cumulative_revenue'] for cust in customer]
        self.assertEqual(revenues[0], Decimal('100'))
        self.assertEqual(revenues[1], Decimal('300'))
        self.assertEqual(revenues[2], Decimal('600'))

        customer = result.filter(customer=Customer.objects.get(email='customer2@test.com'))
        self.assertEqual(customer.count(), 2)
        revenues = [cust['cumulative_revenue'] for cust in customer]
        self.assertEqual(revenues[0], Decimal('100'))
        self.assertEqual(revenues[1], Decimal('200'))

        customer = result.filter(customer=Customer.objects.get(email='customer3@test.com'))
        self.assertEqual(customer.count(), 0)

        customer = result.filter(customer=Customer.objects.get(email='customer4@test.com'))
        self.assertEqual(customer.count(), 2)
        revenues = [cust['cumulative_revenue'] for cust in customer]
        self.assertEqual(revenues[0], Decimal('100'))
        self.assertEqual(revenues[1], Decimal('200'))
        
        customer = result.filter(customer=Customer.objects.get(email='customer5@test.com'))
        self.assertEqual(customer.count(), 3)
        revenues = [cust['cumulative_revenue'] for cust in customer]
        self.assertEqual(revenues[0], Decimal('300'))
        self.assertEqual(revenues[1], Decimal('400'))
        self.assertEqual(revenues[2], Decimal('500'))

        


    def test_analyze_sales(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_analyze_sales.csv')
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_analyze_sales.csv')
        self.assertEqual(response.status_code, 202)
        
        #product = analyze_sales(self.store.id, Product.objects.get(sku='SKU-000').id)
        Analyzer = AnalyzeSales(stores_id=[self.store.id])
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-000').id,))
        print(f'\n\n\nProductAnalyzer: {product}\n\n\n')
        self.assertEqual(product.count(), 3)
        products = [prod for prod in product]

        self.assertEqual(products[2]['price_at_purchase'], Decimal('100.00'))
        self.assertEqual(products[2]['total_units_sold'], 6)
        self.assertEqual(products[2]['total_orders'], 3)

        self.assertEqual(products[1]['price_at_purchase'], Decimal('200.00'))
        self.assertEqual(products[1]['total_units_sold'], 3)
        self.assertEqual(products[1]['total_orders'], 2)

        self.assertEqual(products[0]['price_at_purchase'], Decimal('300.00'))
        self.assertEqual(products[0]['total_units_sold'], 1)
        self.assertEqual(products[0]['total_orders'], 1)

        #product = analyze_sales(self.store.id, Product.objects.get(sku='SKU-001').id)
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-001').id,))
        self.assertEqual(product.count(), 3)
        products = [prod for prod in product]

        self.assertEqual(products[2]['price_at_purchase'], Decimal('100.00'))
        self.assertEqual(products[2]['total_units_sold'], 7)
        self.assertEqual(products[2]['total_orders'], 4) 

        self.assertEqual(products[1]['price_at_purchase'], Decimal('150.00'))
        self.assertEqual(products[1]['total_units_sold'], 7) #3+2+1+1
        self.assertEqual(products[1]['total_orders'], 4)

        self.assertEqual(products[0]['price_at_purchase'], Decimal('200.00'))
        self.assertEqual(products[0]['total_units_sold'], 7)
        self.assertEqual(products[0]['total_orders'], 4)




        #product = analyze_sales(self.store.id, Product.objects.get(sku='SKU-002').id)
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-002').id,))
        self.assertEqual(product.count(), 3)
        products = [prod for prod in product]

        self.assertEqual(products[2]['price_at_purchase'], Decimal('100.00'))
        self.assertEqual(products[2]['total_units_sold'], 7)
        self.assertEqual(products[2]['total_orders'], 3)

        self.assertEqual(products[1]['price_at_purchase'], Decimal('150.00'))
        self.assertEqual(products[1]['total_units_sold'], 7)
        self.assertEqual(products[1]['total_orders'], 3)

        self.assertEqual(products[0]['price_at_purchase'], Decimal('200.00'))
        self.assertEqual(products[0]['total_units_sold'], 7)
        self.assertEqual(products[0]['total_orders'], 3)




        #product = analyze_sales(self.store.id, Product.objects.get(sku='SKU-003').id)
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-003').id,))
        self.assertEqual(product.count(), 4)
        products = [prod for prod in product]

        self.assertEqual(products[3]['price_at_purchase'], Decimal('100.00'))
        self.assertEqual(products[3]['total_units_sold'], 5)
        self.assertEqual(products[3]['total_orders'], 2)

        self.assertEqual(products[2]['price_at_purchase'], Decimal('150.00'))
        self.assertEqual(products[2]['total_units_sold'], 5)
        self.assertEqual(products[2]['total_orders'], 2)

        self.assertEqual(products[1]['price_at_purchase'], Decimal('200.00'))
        self.assertEqual(products[1]['total_units_sold'], 5)
        self.assertEqual(products[1]['total_orders'], 2)

        self.assertEqual(products[0]['price_at_purchase'], Decimal('250.00'))
        self.assertEqual(products[0]['total_units_sold'], 5)
        self.assertEqual(products[0]['total_orders'], 2)



        #product = analyze_sales(self.store.id, Product.objects.get(sku='SKU-004').id)
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-004').id,))
        self.assertEqual(product.count(), 0)


        products = Analyzer.func(products_id=(Product.objects.get(sku='SKU-002').id,
                                              Product.objects.get(sku='SKU-003').id,
                                              Product.objects.get(sku='SKU-004').id))
        products = Analyzer.formulating()
        print(f"\n\n\nProducts: {products}\n\n\n")
        
        



    def test_cohort_analyze(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_cohort_0.csv')
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_cohort_0.csv')
        self.assertEqual(response.status_code, 202)
        
        another_store = Store.objects.create(company=self.company, name="TestStore1")

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_cohort_1.csv', store=another_store)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_cohort_1.csv', store=another_store)
        self.assertEqual(response.status_code, 202)

        CohortAnalyzer = CohortAnalyze(stores_id=[self.store.id])
        CohortAnalyzer.func()
        res = CohortAnalyzer.formulating()

        self.assertEqual(len(res), 4)
        self.assertEqual(res[0]['cohort'], 'Nov 2025')
        self.assertEqual(res[0]['cohort_size'], 10)
        self.assertEqual(res[0]['retention'], [100.0, 80.0, 50.0, 20.0])

        self.assertEqual(res[1]['cohort'], 'Mar 2026')
        self.assertEqual(res[1]['cohort_size'], 3)
        self.assertEqual(res[1]['retention'], [100.0, 100.0])

        self.assertEqual(res[2]['cohort'], 'Apr 2026')
        self.assertEqual(res[2]['cohort_size'], 1)
        self.assertEqual(res[2]['retention'], [100.0])

        self.assertEqual(res[3]['cohort'], 'Jun 2026')
        self.assertEqual(res[3]['cohort_size'], 1)
        self.assertEqual(res[3]['retention'], [100.0, 100.00])
        
        

        


        

        
        

        



        

        
        
        
        
        