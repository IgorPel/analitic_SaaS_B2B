from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)

class Store(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, related_name="stores", on_delete=models.CASCADE)

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='children')

class Product(models.Model):
    store = models.ForeignKey(Store, related_name="products", on_delete=models.CASCADE)
    category = models.ManyToManyField(Category, related_name="products", on_delete=models.CASCADE)

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()

class order(models.Model):
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    store = models.ForeignKey(Store, related_name="orders", on_delete=models.CASCADE)

class OrderItem(models.Model):
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.CASCADE)
    order = models.ForeignKey(order, related_name="order_items", on_delete=models.CASCADE)

class PriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name="price_history", on_delete=models.CASCADE)
# Create your models here.
