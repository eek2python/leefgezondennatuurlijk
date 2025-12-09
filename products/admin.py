from django.contrib import admin
from .models import Product, Category, Click

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
   prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
   list_display = ("title", "category", "is_active")
   prepopulated_fields = {"slug": ("title",)}

@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
   list_display = ("product", "timestamp", "ip")
   readonly_fields = ("timestamp",)
