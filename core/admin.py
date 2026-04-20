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


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']


@admin.register(AdditionalPaper)
class AdditionalPaperAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']


@admin.register(WeeklyMagazine)
class WeeklyMagazineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']


@admin.register(MonthlyMagazine)
class MonthlyMagazineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'monthly_price']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'phone',
        'area',
        'newspaper',
        'additional_paper',
        'weekly_magazine',
        'monthly_magazine',
        'active'
    ]
    search_fields = ['name', 'phone']
    list_filter = ['area', 'active']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer',
        'month',
        'year',
        'newspaper_amount',
        'additional_paper_amount',
        'weekly_magazine_amount',
        'monthly_magazine_amount',
        'total_amount',
        'is_paid'
    ]
    list_filter = ['month', 'year', 'is_paid']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'bill', 'amount', 'status', 'date']
    list_filter = ['status']