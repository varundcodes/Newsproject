from django.db import models
from django.contrib.auth.models import User


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Newspaper(models.Model):
    name = models.CharField(max_length=100, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_price}"


class AdditionalPaper(models.Model):
    name = models.CharField(max_length=100, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_price}"


class WeeklyMagazine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_price}"


class MonthlyMagazine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} - ₹{self.monthly_price}"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10, unique=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    address = models.TextField(blank=True)

    newspaper = models.ForeignKey(Newspaper, on_delete=models.SET_NULL, null=True, blank=True)
    additional_paper = models.ForeignKey(AdditionalPaper, on_delete=models.SET_NULL, null=True, blank=True)
    weekly_magazine = models.ForeignKey(WeeklyMagazine, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_magazine = models.ForeignKey(MonthlyMagazine, on_delete=models.SET_NULL, null=True, blank=True)

    custom_newspaper_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_additional_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_weekly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.user:
            user, created = User.objects.get_or_create(username=self.phone)
            if created:
                user.set_password(self.phone)
                user.save()
            self.user = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.phone}"


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


class Bill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    month = models.CharField(max_length=3, choices=MONTH_CHOICES)
    year = models.IntegerField(default=2026)

    newspaper_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_paper_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weekly_magazine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_magazine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'month', 'year')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.month} {self.year}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    screenshot = models.ImageField(upload_to='payments/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.status}"