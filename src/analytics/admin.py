from django.contrib import admin


from .models import Company, Store, Category, Product, Customer, Order, OrderItem, PriceHistory

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass
@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    pass


