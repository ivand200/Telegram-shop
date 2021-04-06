from django.contrib import admin

from .models import Customer, Product, Cart, Order

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "name")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "quantity")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("customer", "product", "quantity", "total", "created_at")
