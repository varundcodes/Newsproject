from django.contrib import admin
from .models import (
    Area,
    Newspaper,
    AdditionalPaper,
    WeeklyMagazine,
    MonthlyMagazine,
    Customer,
    Bill,
    Payment,
)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']
    search_fields = ['name']


@admin.register(AdditionalPaper)
class AdditionalPaperAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']
    search_fields = ['name']


@admin.register(WeeklyMagazine)
class WeeklyMagazineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']
    search_fields = ['name']


@admin.register(MonthlyMagazine)
class MonthlyMagazineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'phone',
        'area',
        'newspaper',
        'status',
        'stop_start_date',
        'stop_end_date',
    ]
    list_filter = ['status', 'area']
    search_fields = ['name', 'phone', 'address']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'month', 'year', 'total_amount', 'is_paid', 'created_at']
    list_filter = ['month', 'year', 'is_paid']
    search_fields = ['customer__name', 'customer__phone']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'bill', 'amount', 'status', 'date']
    list_filter = ['status', 'date']
    search_fields = ['customer__name', 'customer__phone']
    