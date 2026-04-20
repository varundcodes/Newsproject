from django import forms
from .models import (
    Area,
    Newspaper,
    AdditionalPaper,
    WeeklyMagazine,
    MonthlyMagazine,
    Customer,
    Bill,
    Payment
)


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['name']


class NewspaperForm(forms.ModelForm):
    class Meta:
        model = Newspaper
        fields = ['name', 'monthly_price']


class AdditionalPaperForm(forms.ModelForm):
    class Meta:
        model = AdditionalPaper
        fields = ['name', 'monthly_price']


class WeeklyMagazineForm(forms.ModelForm):
    class Meta:
        model = WeeklyMagazine
        fields = ['name', 'monthly_price']


class MonthlyMagazineForm(forms.ModelForm):
    class Meta:
        model = MonthlyMagazine
        fields = ['name', 'monthly_price']


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'area',
            'address',
            'newspaper',
            'custom_newspaper_price',
            'additional_paper',
            'custom_additional_price',
            'weekly_magazine',
            'custom_weekly_price',
            'monthly_magazine',
            'custom_monthly_price',
            'active',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer', 'month', 'year']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['bill', 'amount', 'screenshot']