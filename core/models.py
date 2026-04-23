from django.db import models
from django.contrib.auth.models import User
from datetime import date


MONTH_CHOICES = [
    ('Jan', 'January'),
    ('Feb', 'February'),
    ('Mar', 'March'),
    ('Apr', 'April'),
    ('May', 'May'),
    ('Jun', 'June'),
    ('Jul', 'July'),
    ('Aug', 'August'),
    ('Sep', 'September'),
    ('Oct', 'October'),
    ('Nov', 'November'),
    ('Dec', 'December'),
]


class Area(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Newspaper(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


class AdditionalPaper(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


class WeeklyMagazine(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


class MonthlyMagazine(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


class Customer(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Stopped', 'Stopped'),
        ('Inactive', 'Inactive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()

    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    newspaper = models.ForeignKey(Newspaper, on_delete=models.SET_NULL, null=True, blank=True)
    additional_paper = models.ForeignKey(AdditionalPaper, on_delete=models.SET_NULL, null=True, blank=True)
    weekly_magazine = models.ForeignKey(WeeklyMagazine, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_magazine = models.ForeignKey(MonthlyMagazine, on_delete=models.SET_NULL, null=True, blank=True)

    custom_newspaper_price = models.FloatField(null=True, blank=True)
    custom_additional_price = models.FloatField(null=True, blank=True)
    custom_weekly_price = models.FloatField(null=True, blank=True)
    custom_monthly_price = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    stop_start_date = models.DateField(null=True, blank=True)
    stop_end_date = models.DateField(null=True, blank=True)
    stop_reason = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.user:
            user, created = User.objects.get_or_create(username=self.phone)
            if created:
                user.set_password(self.phone)
                user.save()
            self.user = user
        super().save(*args, **kwargs)

    def is_stopped_today(self):
        today = date.today()
        if self.stop_start_date and self.stop_end_date:
            return self.stop_start_date <= today <= self.stop_end_date
        return False


class Bill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    month = models.CharField(max_length=3, choices=MONTH_CHOICES)
    year = models.IntegerField()

    newspaper_amount = models.FloatField(default=0)
    additional_paper_amount = models.FloatField(default=0)
    weekly_magazine_amount = models.FloatField(default=0)
    monthly_magazine_amount = models.FloatField(default=0)

    total_amount = models.FloatField(default=0)

    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.month} {self.year}"

    def calculate_amount(self):
        customer = self.customer

        if customer.is_stopped_today():
            self.newspaper_amount = 0
            self.additional_paper_amount = 0
            self.weekly_magazine_amount = 0
            self.monthly_magazine_amount = 0
            self.total_amount = 0
            return

        newspaper_amount = 0
        additional_amount = 0
        weekly_amount = 0
        monthly_amount = 0

        if customer.newspaper:
            newspaper_amount = customer.custom_newspaper_price or customer.newspaper.monthly_price

        if customer.additional_paper:
            additional_amount = customer.custom_additional_price or customer.additional_paper.monthly_price

        if customer.weekly_magazine:
            weekly_amount = customer.custom_weekly_price or customer.weekly_magazine.monthly_price

        if customer.monthly_magazine:
            monthly_amount = customer.custom_monthly_price or customer.monthly_magazine.monthly_price

        total = newspaper_amount + additional_amount + weekly_amount + monthly_amount

        self.newspaper_amount = newspaper_amount
        self.additional_paper_amount = additional_amount
        self.weekly_magazine_amount = weekly_amount
        self.monthly_magazine_amount = monthly_amount
        self.total_amount = total

    def save(self, *args, **kwargs):
        self.calculate_amount()
        super().save(*args, **kwargs)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    amount = models.FloatField()
    screenshot = models.ImageField(upload_to='payments/', null=True, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status == 'Verified':
            self.bill.is_paid = True
            self.bill.save()