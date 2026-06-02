from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from analytics.models import Order, PriceHistory, Product


@receiver(pre_save, sender=Product)
def report_uploaded(sender, instance, **kwargs):
    if instance.pk is None:
        return

    try:
        old_instance = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return

    PriceHistory.objects.create(
        product=instance,
        price=old_instance.current_price
    )

