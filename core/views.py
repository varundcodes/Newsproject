from decimal import Decimal
import urllib.parse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AreaForm,
    NewspaperForm,
    CustomerForm,
    BillForm,
    PaymentForm,
)
from .models import (
    Area,
    Newspaper,
    Customer,
    Bill,
    Payment,
    MONTH_CHOICES,
)


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')

    return render(request, 'core/admin_login.html')


@login_required(login_url='/')
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required(login_url='/')
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    total_customers = Customer.objects.count()
    total_areas = Area.objects.count()
    total_bills = Bill.objects.count()
    pending_payments = Payment.objects.filter(status='Pending').count()
    total_collection = Bill.objects.filter(is_paid=True).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    area_data = Customer.objects.values('area__name').annotate(
        count=Count('id')
    ).order_by('area__name')

    context = {
        'total_customers': total_customers,
        'total_areas': total_areas,
        'total_bills': total_bills,
        'pending_payments': pending_payments,
        'total_collection': total_collection,
        'area_data': area_data,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required(login_url='/')
def add_area(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = AreaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Area added successfully')
        return redirect('admin_dashboard')

    return render(request, 'core/add_area.html', {'form': form})


@login_required(login_url='/')
def add_newspaper(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = NewspaperForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Newspaper added successfully')
        return redirect('admin_dashboard')

    return render(request, 'core/add_newspaper.html', {'form': form})


@login_required(login_url='/')
def add_customer(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            'Customer added successfully. Default password is phone number.'
        )
        return redirect('customer_list')

    return render(request, 'core/add_customer.html', {'form': form})


@login_required(login_url='/')
def customer_list(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customers = Customer.objects.select_related(
        'area',
        'newspaper',
        'additional_paper',
        'weekly_magazine',
        'monthly_magazine',
    ).all().order_by('name')

    return render(request, 'core/customer_list.html', {
        'customers': customers
    })


@login_required(login_url='/')
def area_customer_list(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area')

    customers = Customer.objects.select_related(
        'area',
        'newspaper',
        'additional_paper',
        'weekly_magazine',
        'monthly_magazine',
    ).all().order_by('name')

    if selected_area_id:
        customers = customers.filter(area_id=selected_area_id)

    return render(request, 'core/area_customer_list.html', {
        'areas': areas,
        'customers': customers,
        'selected_area_id': selected_area_id,
    })


@login_required(login_url='/')
def generate_bill(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = BillForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bill created successfully')
        return redirect('admin_dashboard')

    return render(request, 'core/generate_bill.html', {'form': form})


@login_required(login_url='/')
@login_required(login_url='/')
def area_bill_generate(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area') or request.POST.get('area')
    month = request.GET.get('month') or request.POST.get('month')
    year = request.GET.get('year') or request.POST.get('year')

    customers = Customer.objects.none()
    created_count = 0
    skipped_count = 0

    if selected_area_id:
        customers = Customer.objects.filter(
            area_id=selected_area_id,
            active=True
        ).select_related(
            'newspaper',
            'additional_paper',
            'weekly_magazine',
            'monthly_magazine'
        ).order_by('name')

        # WhatsApp link preview for loaded customers
        for customer in customers:
            if customer.custom_newspaper_price is not None:
                newspaper_amount = customer.custom_newspaper_price
            elif customer.newspaper:
                newspaper_amount = customer.newspaper.monthly_price
            else:
                newspaper_amount = Decimal('0')

            if customer.custom_additional_price is not None:
                additional_paper_amount = customer.custom_additional_price
            elif customer.additional_paper:
                additional_paper_amount = customer.additional_paper.monthly_price
            else:
                additional_paper_amount = Decimal('0')

            if customer.custom_weekly_price is not None:
                weekly_magazine_amount = customer.custom_weekly_price
            elif customer.weekly_magazine:
                weekly_magazine_amount = customer.weekly_magazine.monthly_price
            else:
                weekly_magazine_amount = Decimal('0')

            if customer.custom_monthly_price is not None:
                monthly_magazine_amount = customer.custom_monthly_price
            elif customer.monthly_magazine:
                monthly_magazine_amount = customer.monthly_magazine.monthly_price
            else:
                monthly_magazine_amount = Decimal('0')

            total_amount = (
                newspaper_amount +
                additional_paper_amount +
                weekly_magazine_amount +
                monthly_magazine_amount
            )

            message = f"""
Hello {customer.name},

Your Newspaper Bill for {month} {year} is ready.

📰 Newspaper: ₹{newspaper_amount}
➕ Additional: ₹{additional_paper_amount}
📘 Weekly: ₹{weekly_magazine_amount}
📗 Monthly: ₹{monthly_magazine_amount}

💰 Total: ₹{total_amount}

Pay using UPI:
{settings.OWNER_UPI_ID}

Thank you 🙏
"""
            encoded_message = urllib.parse.quote(message)
            customer.whatsapp_link = f"https://wa.me/91{customer.phone}?text={encoded_message}"

    if request.method == 'POST' and selected_area_id and month and year:
        for customer in customers:
            if customer.custom_newspaper_price is not None:
                newspaper_amount = customer.custom_newspaper_price
            elif customer.newspaper:
                newspaper_amount = customer.newspaper.monthly_price
            else:
                newspaper_amount = Decimal('0')

            if customer.custom_additional_price is not None:
                additional_paper_amount = customer.custom_additional_price
            elif customer.additional_paper:
                additional_paper_amount = customer.additional_paper.monthly_price
            else:
                additional_paper_amount = Decimal('0')

            if customer.custom_weekly_price is not None:
                weekly_magazine_amount = customer.custom_weekly_price
            elif customer.weekly_magazine:
                weekly_magazine_amount = customer.weekly_magazine.monthly_price
            else:
                weekly_magazine_amount = Decimal('0')

            if customer.custom_monthly_price is not None:
                monthly_magazine_amount = customer.custom_monthly_price
            elif customer.monthly_magazine:
                monthly_magazine_amount = customer.monthly_magazine.monthly_price
            else:
                monthly_magazine_amount = Decimal('0')

            total_amount = (
                newspaper_amount +
                additional_paper_amount +
                weekly_magazine_amount +
                monthly_magazine_amount
            )

            bill, created = Bill.objects.get_or_create(
                customer=customer,
                month=month,
                year=year,
                defaults={
                    'newspaper_amount': newspaper_amount,
                    'additional_paper_amount': additional_paper_amount,
                    'weekly_magazine_amount': weekly_magazine_amount,
                    'monthly_magazine_amount': monthly_magazine_amount,
                    'total_amount': total_amount,
                    'is_paid': False,
                }
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        if created_count:
            messages.success(request, f'{created_count} bills created successfully.')
        if skipped_count:
            messages.warning(request, f'{skipped_count} bills already existed and were skipped.')

        return redirect(f'/area-bills/?area={selected_area_id}&month={month}&year={year}')

    return render(request, 'core/area_bill_generate.html', {
        'areas': areas,
        'customers': customers,
        'selected_area_id': selected_area_id,
        'month': month,
        'year': year,
        'month_choices': MONTH_CHOICES,
    })

@login_required(login_url='/')
def area_payment_history(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area')

    payments = Payment.objects.select_related(
        'customer',
        'bill',
        'customer__area'
    ).order_by('-date')

    if selected_area_id:
        payments = payments.filter(customer__area_id=selected_area_id)

    return render(request, 'core/area_payment_history.html', {
        'areas': areas,
        'payments': payments,
        'selected_area_id': selected_area_id,
    })


def customer_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            customer = Customer.objects.get(phone=phone)
            if customer.user:
                user = authenticate(
                    request,
                    username=customer.user.username,
                    password=password
                )
                if user is not None:
                    login(request, user)
                    return redirect('customer_dashboard')
                else:
                    messages.error(request, 'Invalid phone number or password')
            else:
                messages.error(request, 'Customer account not linked')
        except Customer.DoesNotExist:
            messages.error(request, 'Customer not found')

    return render(request, 'core/customer_login.html')


@login_required(login_url='/customer-login/')
def customer_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    customer = get_object_or_404(Customer, user=request.user)
    bills = Bill.objects.filter(customer=customer).order_by('-created_at')
    latest_bill = bills.first()
    payments = Payment.objects.filter(customer=customer).order_by('-date')

    upi_link = ''
    if latest_bill:
        upi_link = (
            f"upi://pay?pa={settings.OWNER_UPI_ID}"
            f"&pn={settings.OWNER_NAME}"
            f"&am={latest_bill.total_amount}"
            f"&cu=INR"
        )

    return render(request, 'core/customer_dashboard.html', {
        'customer': customer,
        'latest_bill': latest_bill,
        'payments': payments,
        'upi_link': upi_link,
        'owner_upi_id': settings.OWNER_UPI_ID,
        'owner_name': settings.OWNER_NAME,
        'owner_phonepe_number': settings.OWNER_PHONEPE_NUMBER,
        'owner_paytm_number': settings.OWNER_PAYTM_NUMBER,
        'owner_gpay_number': settings.OWNER_GPAY_NUMBER,
        'owner_qr_image': settings.OWNER_QR_IMAGE,
    })


@login_required(login_url='/customer-login/')
def upload_payment(request, bill_id):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    customer = get_object_or_404(Customer, user=request.user)
    bill = get_object_or_404(Bill, id=bill_id, customer=customer)

    form = PaymentForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.customer = customer
        payment.bill = bill
        payment.save()
        messages.success(request, 'Payment uploaded successfully')
        return redirect('customer_dashboard')

    return render(request, 'core/upload_payment.html', {
        'form': form,
        'bill': bill,
    })


@login_required(login_url='/customer-login/')
def customer_logout(request):
    logout(request)
    return redirect('customer_login')