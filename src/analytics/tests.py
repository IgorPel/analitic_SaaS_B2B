import uuid
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
from django.contrib.auth.models import User


import os

def upload_data(self, url, path, store=None, user=None):
    if not store:
        store = self.store

    if user:

        if hasattr(self.client, 'force_authenticate'):
            self.client.force_authenticate(user=user)
        else:
            self.client.force_login(user=user)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, path)

    with open(file_path, 'rb') as csv_file:
        response = self.client.post(url, {
            'file': csv_file,
            'store_name': store.name,
        }, format='multipart')

    if user:

        if hasattr(self.client, 'force_authenticate'):
            self.client.force_authenticate(user=None)
        else:
            self.client.logout()

    return response

@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class CatalogUploadIntegrationTest(APITestCase):

    def setUp(self):
        test_user = User.objects.create_user("TEST", "test@gmail.com", "testtest")
        self.client.force_authenticate(user=test_user)
        self.company = Company.objects.create(name="Test Company", owner=test_user)
        self.store = Store.objects.create(name="Test Store", company=self.company)
        self.upload_url = reverse('store-data-upload')

    def test_api_upload_creates_categories_and_products(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'test_data', 'test_upload_catalog.csv')

        with open(file_path, 'rb') as csv_file:
            response = self.client.post(self.upload_url, {
                'file': csv_file,
                'store_name': self.store.name
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

        self.test_user = User.objects.create_user("TEST", "test@gmail.com", "testtest")
        self.client.force_authenticate(user=self.test_user)
        self.company = Company.objects.create(name="Test Company", owner=self.test_user)

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
        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_customers.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Customer.objects.count(), 3)
        self.assertTrue(Customer.objects.filter(email='client0@test.com').exists())
        self.assertTrue(Customer.objects.filter(email='client1@test.com').exists())
        self.assertTrue(Customer.objects.filter(email='client2@test.com').exists())


    def test_sales_api_products(self):

        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_product.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Product.objects.count(), 3)
        self.assertEqual(ImportIssue.objects.count(), 1)
        issue = ImportIssue.objects.first()
        self.assertEqual(issue.type, 'MISSING_SKU')
        self.assertEqual(issue.description, 'SKU \'SKU-1003\' created as draft.')
        self.assertEqual(issue.row_number, 4)


    def test_sales_api_orders(self):

        response = upload_data(self, self.upload_url, 'test_data/test_upload_sales/test_orders.csv', user=self.test_user)

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


class AnalyticsFuncTest(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user("TEST", "test@gmail.com", "testtest")

        self.company = Company.objects.create(name="TestCompany", owner=self.test_user)
        self.store = Store.objects.create(company=self.company, name="TestStore0")
        self.upload_url_catalog = reverse('store-data-upload')
        self.upload_url_sales = reverse('sales-data-upload')


    def est_formulating_revenue(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_revenue.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_revenue.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        rev = Revenue(stores_id=[self.store.id])
        rev.func()

        result = rev.formulating()


    def est_formulating_ltv(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_ltv.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_ltv.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        rev = LTV(stores_id=[self.store.id])
        rev.func()

        result = rev.formulating()


    def est_revenue(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_revenue.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_revenue.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        rev = Revenue(stores_id=[self.store.id])
        result = rev.func()


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


    def test_fill_gaps(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/products.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        response = upload_data(self, self.upload_url_sales, 'test_data/sales_data.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        ltv = LTV(stores_id=[self.store.id], start_date=datetime(2026, 7, 1, tzinfo=timezone.utc), end_date=datetime(2026, 7, 8, tzinfo=timezone.utc),
                  group_and_limit={
                      'group_by': {
                          'customer': 'F',
                          'total_price': 'Sum'
                          },
                    'limit': 5,
                    'order_by': ['-total_price_sum']
                    },
                  fill_blank={
                      'method': 'AtoZ',
                      'start': '2026-07-01',
                      'end': '2026-07-08',
                      'delta': {
                              'func': 'timedelta',
                              'per': 'days',
                              'value': 1
                          },
                      'data_type': 'date', 'key': 'days', 'uniques': 'customer',
                      'to_fill': {
                              'total_prices': ['DefaultValue', 0.0],
                              'cumulative_revenue': ['DefaultValueLeft', 0.0]
                       }
                    },
                    unique_dates=True
        )

        result = ltv.func()
        res = ltv.formulating()

    def est_ltv(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_ltv.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_ltv.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        ltv = LTV(stores_id=[self.store.id])
        result = ltv.func()


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


    def est_quick(self):
        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_ltv.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)
        response = upload_data(self, self.upload_url_sales, 'test_data/sales_data.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(ImportIssue.objects.count(), 0)


    def est_analyze_sales(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_analyze_sales.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_analyze_sales.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)


        Analyzer = AnalyzeSales(stores_id=[self.store.id])
        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-000').id,))

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


        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-001').id,))
        self.assertEqual(product.count(), 3)
        products = [prod for prod in product]

        self.assertEqual(products[2]['price_at_purchase'], Decimal('100.00'))
        self.assertEqual(products[2]['total_units_sold'], 7)
        self.assertEqual(products[2]['total_orders'], 4)

        self.assertEqual(products[1]['price_at_purchase'], Decimal('150.00'))
        self.assertEqual(products[1]['total_units_sold'], 7)
        self.assertEqual(products[1]['total_orders'], 4)

        self.assertEqual(products[0]['price_at_purchase'], Decimal('200.00'))
        self.assertEqual(products[0]['total_units_sold'], 7)
        self.assertEqual(products[0]['total_orders'], 4)


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


        product = Analyzer.func(products_id=(Product.objects.get(sku='SKU-004').id,))
        self.assertEqual(product.count(), 0)


        products = Analyzer.func(products_id=(Product.objects.get(sku='SKU-002').id,
                                              Product.objects.get(sku='SKU-003').id,
                                              Product.objects.get(sku='SKU-004').id))
        products = Analyzer.formulating()


    def est_cohort_analyze(self):

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_cohort_0.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_cohort_0.csv', user=self.test_user)
        self.assertEqual(response.status_code, 202)

        another_store = Store.objects.create(company=self.company, name="TestStore1")

        response = upload_data(self, self.upload_url_catalog, 'test_data/test_analytics/catalogs/catalog_cohort_1.csv', store=another_store, user=self.test_user)
        self.assertEqual(response.status_code, 202)


        response = upload_data(self, self.upload_url_sales, 'test_data/test_analytics/func/test_cohort_1.csv', store=another_store, user=self.test_user)
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


class DashboardPreferencesAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@test.com", "password123")
        self.client.force_authenticate(user=self.user)
        self.widget_1 = {"id": str(uuid.uuid4()), "func": "revenue", "chart": {"type": "Line"}}
        self.widget_2 = {"id": str(uuid.uuid4()), "func": "ltv", "chart": {"type": "Line"}}
        self.company = Company.objects.create(
            name="Prefs Company",
            owner=self.user,
            dashboard_preferences=[self.widget_1, self.widget_2]
        )

    def test_get_preferences(self):
        url = reverse('dashboard-preferences')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_delete_widget_by_url_param(self):
        url = reverse('dashboard-preferences-detail', kwargs={'widget_id': self.widget_1["id"]})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "deleted")
        self.company.refresh_from_db()
        self.assertEqual(len(self.company.dashboard_preferences), 1)
        self.assertEqual(self.company.dashboard_preferences[0]["id"], self.widget_2["id"])

    def test_delete_widget_by_query_param(self):
        url = f"{reverse('dashboard-preferences')}?id={self.widget_2['id']}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "deleted")
        self.company.refresh_from_db()
        self.assertEqual(len(self.company.dashboard_preferences), 1)
        self.assertEqual(self.company.dashboard_preferences[0]["id"], self.widget_1["id"])

    def test_delete_non_existent_widget(self):
        url = reverse('dashboard-preferences-detail', kwargs={'widget_id': "non-existent-id"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
