from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel


# Create your models here.

class Company(TimeStampedModel):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')

    def __str__(self):
        return self.name

    name = models.CharField(max_length=100)
 

class Store(models.Model):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    class Meta:
        verbose_name = _('Store')
        verbose_name_plural = _('Stores')

    def __str__(self):
        return self.name

    company = models.ForeignKey(Company, related_name="stores", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='USD')

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               null=True,
                               blank=True,
                               related_name='children')

    company = models.ForeignKey(Company, related_name="categories", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

class Product(models.Model):
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, db_index=True)
    category = models.ManyToManyField(Category, related_name="products")
    store = models.ForeignKey(Store, related_name="products", on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')



class Customer(TimeStampedModel):
    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')

    email = models.EmailField()
    company = models.ForeignKey(Company, related_name="customers", on_delete=models.CASCADE)

class Order(TimeStampedModel):
    order_id = models.CharField(max_length=255, db_index=True)
    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    store = models.ForeignKey(Store, related_name="orders", on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateTimeField()


    def __str__(self):
        return f'{self.customer.name} - {self.store.name}'

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        constraints = [
            models.UniqueConstraint(
                fields=['store', 'order_id'], 
                name='unique_order_per_store'
            )
        ]

    class Status(models.TextChoices):
        COMPLETED = 'CM', _('Completed')
        CANCELED = 'CN', _("Canceled")
        RETURNED = 'RT', _("Returned")

    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.COMPLETED
    )
   

class OrderItem(models.Model):
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.PROTECT)
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.order.name} - {self.product.name}'

class PriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name="price_history", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_at = models.DateTimeField(auto_now=None)

    def __str__(self):
        return f'{self.product.name} - {self.price}'

    class Meta:
        verbose_name = _('PriceHistory')
        verbose_name_plural = _('PriceHistory')


class ImportIssue(TimeStampedModel):
    company = models.ForeignKey(Company, related_name="import_issues", on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=50)
    description = models.TextField()
    row_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"[{self.issue_type}] {self.company.name} - Task: {self.task_id}"

    class Meta:
        verbose_name = _('ImportIssue')
        verbose_name_plural = _('ImportIssues')

