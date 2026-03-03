from django.contrib import admin
from .models import Product, ProductImage
from .models import Payment


# Inline for ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # number of extra image fields

# Admin for Product
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('name', 'price', 'stock', 'created_at')  # fields to show in admin list

# Register Product with ProductAdmin
admin.site.register(Product, ProductAdmin)


admin.site.register(Payment)