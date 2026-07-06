from django.contrib import admin

from .models import Product, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("nom", "localisation", "capacite")
    search_fields = ("nom", "localisation")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("nom", "quantite", "date_expiration", "state", "warehouse")
    list_filter = ("state", "warehouse")
    search_fields = ("nom",)
