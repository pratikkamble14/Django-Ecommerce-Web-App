from django.contrib import admin

# Register your models here.
# product_app/admin.py

from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'price', 'stock', 'available']
    list_filter = ['category', 'available', 'created']
    search_fields = ['name', 'description']
