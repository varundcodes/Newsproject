from django.db import models
from django.contrib.auth.models import User
from datetime import date


MONTH_CHOICES = [
    ('Jan', 'January'), ('Feb', 'February'), ('Mar', 'March'),
    ('Apr', 'April'), ('May', 'May'), ('Jun', 'June'),
    ('Jul', 'July'), ('Aug', 'August'), ('Sep', 'September'),
    ('Oct', 'October'), ('Nov', 'November'), ('Dec', 'December'),
]


# ---------------- AREA ----------------
class Area(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ---------------- NEWSPAPER ----------------
class Newspaper(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


# ---------------- ADDITIONAL PAPER ----------------
class AdditionalPaper(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


# ---------------- WEEKLY MAGAZINE ----------------
class WeeklyMagazine(models.Model):
    name = models.CharField(max_length=100)
    weekly_price = models.FloatField()  # ✅ changed

    def __str__(self):
        return self.name


# ---------------- MONTHLY MAGAZINE ----------------
class MonthlyMagazine(models.Model):
    name = models.CharField(max_length=100)
    monthly_price = models.FloatField()

    def __str__(self):
        return self.name


# ---------------- CUSTOMER ----------------
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

    # ✅ FIXED SAVE METHOD (NO DUPLICATE USER ERROR)
    def save(self, *args, **kwargs):
        if not self.user:
            user, created = User.objects.get_or_create(
                username=self.phone,
                defaults={"email": ""}
            )

            if created:
                user.set_password("custo@12345")
                user.save()

            self.user = user

        super().save(*args, **kwargs)

    def is_stopped_today(self):
        today = date.today()
        if self.stop_start_date and self.stop_end_date:
            return self.stop_start_date <= today <= self.stop_end_date
        return False


# ---------------- BILL ----------------
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
            self.total_amount = 0
            return

        newspaper = (
            customer.custom_newspaper_price
            if customer.custom_newspaper_price is not None
            else (customer.newspaper.monthly_price if customer.newspaper else 0)
        )

        additional = (
            customer.custom_additional_price
            if customer.custom_additional_price is not None
            else (customer.additional_paper.monthly_price if customer.additional_paper else 0)
        )

        # ✅ WEEKLY LOGIC
        weeks = 4
        weekly = (
            customer.custom_weekly_price
            if customer.custom_weekly_price is not None
            else (customer.weekly_magazine.weekly_price * weeks if customer.weekly_magazine else 0)
        )

        monthly = (
            customer.custom_monthly_price
            if customer.custom_monthly_price is not None
            else (customer.monthly_magazine.monthly_price if customer.monthly_magazine else 0)
        )

        self.newspaper_amount = newspaper
        self.additional_paper_amount = additional
        self.weekly_magazine_amount = weekly
        self.monthly_magazine_amount = monthly
        self.total_amount = newspaper + additional + weekly + monthly

    def save(self, *args, **kwargs):
        self.calculate_amount()
        super().save(*args, **kwargs)


# ---------------- PAYMENT ----------------
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