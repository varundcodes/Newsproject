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
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monthly_price')
    search_fields = ('name',)


@admin.register(AdditionalPaper)
class AdditionalPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monthly_price')
    search_fields = ('name',)


@admin.register(WeeklyMagazine)
class WeeklyMagazineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'weekly_price')
    search_fields = ('name',)


@admin.register(MonthlyMagazine)
class MonthlyMagazineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monthly_price')
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'phone',
        'area',
        'newspaper',
        'status',
        'created_at',
    )
    list_filter = ('area', 'status', 'newspaper')
    search_fields = ('name', 'phone')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'month',
        'year',
        'total_amount',
        'payment_status',
        'created_at',
    )
    list_filter = ('month', 'year', 'payment_status')
    search_fields = ('customer__name', 'customer__phone')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
    'id',
    'customer',
    'bill',
    'amount',
    'payment_method',
    'status',
    'date',
)

    list_filter = ('status', 'payment_method', 'date')
    search_fields = ('customer__name', 'customer__phone')