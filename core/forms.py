from django import forms
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


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter area name"
            }),
        }


class NewspaperForm(forms.ModelForm):
    class Meta:
        model = Newspaper
        fields = ["name", "monthly_price"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter newspaper name"
            }),
            "monthly_price": forms.NumberInput(attrs={
                "placeholder": "Enter monthly price"
            }),
        }


class AdditionalPaperForm(forms.ModelForm):
    class Meta:
        model = AdditionalPaper
        fields = ["name", "monthly_price"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter additional paper name"
            }),
            "monthly_price": forms.NumberInput(attrs={
                "placeholder": "Enter monthly price"
            }),
        }


class WeeklyMagazineForm(forms.ModelForm):
    class Meta:
        model = WeeklyMagazine
        fields = ['name', 'weekly_price']


class MonthlyMagazineForm(forms.ModelForm):
    class Meta:
        model = MonthlyMagazine
        fields = ["name", "monthly_price"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter monthly magazine name"
            }),
            "monthly_price": forms.NumberInput(attrs={
                "placeholder": "Enter monthly price"
            }),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "name",
            "phone",
            "area",
            "address",
            "newspaper",
            "custom_newspaper_price",
            "additional_paper",
            "custom_additional_price",
            "weekly_magazine",
            "custom_weekly_price",
            "monthly_magazine",
            "custom_monthly_price",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter customer name"
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "Enter 10-digit phone number"
            }),
            "address": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Enter address"
            }),
            "custom_newspaper_price": forms.NumberInput(attrs={
                "placeholder": "Optional custom newspaper price"
            }),
            "custom_additional_price": forms.NumberInput(attrs={
                "placeholder": "Optional custom additional paper price"
            }),
            "custom_weekly_price": forms.NumberInput(attrs={
                "placeholder": "Optional custom weekly magazine price"
            }),
            "custom_monthly_price": forms.NumberInput(attrs={
                "placeholder": "Optional custom monthly magazine price"
            }),
        }


class StopCustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["stop_start_date", "stop_end_date", "stop_reason"]
        widgets = {
            "stop_start_date": forms.DateInput(attrs={"type": "date"}),
            "stop_end_date": forms.DateInput(attrs={"type": "date"}),
            "stop_reason": forms.TextInput(attrs={
                "placeholder": "Vacation / Out of station / Temporary stop"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("stop_start_date")
        end_date = cleaned_data.get("stop_end_date")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(
                "Stop end date cannot be before stop start date."
            )

        return cleaned_data


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ["customer", "month", "year"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "screenshot"]