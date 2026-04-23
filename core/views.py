from decimal import Decimal
from datetime import date
import calendar
import urllib.parse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AreaForm, NewspaperForm, CustomerForm, StopCustomerForm
from .models import Customer, Area, Bill, Payment, MONTH_CHOICES


def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
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
    total_collection = Payment.objects.filter(status='Verified').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    area_data = Customer.objects.values('area__name').annotate(
        count=Count('id')
    ).order_by('area__name')

    return render(request, 'core/dashboard.html', {
        'total_customers': total_customers,
        'total_areas': total_areas,
        'total_bills': total_bills,
        'pending_payments': pending_payments,
        'total_collection': total_collection,
        'area_data': area_data,
    })


@login_required(login_url='/')
def add_area(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = AreaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Area added successfully')
        return redirect('add_area')

    return render(request, 'core/add_area.html', {'form': form})


@login_required(login_url='/')
def add_newspaper(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = NewspaperForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Newspaper added successfully')
        return redirect('add_newspaper')

    return render(request, 'core/add_newspaper.html', {'form': form})


@login_required(login_url='/')
def add_customer(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Customer added successfully')
        return redirect('add_customer')

    return render(request, 'core/add_customer.html', {'form': form})


@login_required(login_url='/')
def customer_list(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    search = request.GET.get('search', '').strip()
    customers = None

    if search:
        customers = Customer.objects.filter(
            Q(name__icontains=search) | Q(phone__icontains=search)
        ).select_related('area', 'newspaper').order_by('name')

    return render(request, 'core/customer_list.html', {
        'customers': customers,
        'search': search
    })


@login_required(login_url='/')
def area_customer_list(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area')
    search = request.GET.get('search', '').strip()

    customers = None

    if selected_area_id:
        customers = Customer.objects.filter(area_id=selected_area_id)

        if search:
            customers = customers.filter(
                Q(name__icontains=search) | Q(phone__icontains=search)
            )

        customers = customers.select_related('area', 'newspaper').order_by('name')

    return render(request, 'core/area_customer_list.html', {
        'areas': areas,
        'customers': customers,
        'selected_area_id': selected_area_id,
        'search': search
    })


@login_required(login_url='/')
def activate_customer(request, customer_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customer = get_object_or_404(Customer, id=customer_id)
    customer.status = 'Active'
    customer.stop_start_date = None
    customer.stop_end_date = None
    customer.stop_reason = ''
    customer.save()

    messages.success(request, f'{customer.name} is now Active.')

    selected_area_id = request.GET.get('area')
    search = request.GET.get('search', '')
    if selected_area_id:
        url = f'/area-customers/?area={selected_area_id}'
        if search:
            url += f'&search={search}'
        return redirect(url)

    return redirect('customer_list')


@login_required(login_url='/')
def stop_customer(request, customer_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customer = get_object_or_404(Customer, id=customer_id)
    selected_area_id = request.GET.get('area')
    search = request.GET.get('search', '')

    if request.method == 'POST':
        form = StopCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.status = 'Stopped'
            customer.save()
            messages.warning(request, f'{customer.name} is stopped for selected dates.')

            if selected_area_id:
                url = f'/area-customers/?area={selected_area_id}'
                if search:
                    url += f'&search={search}'
                return redirect(url)

            return redirect('customer_list')
    else:
        form = StopCustomerForm(instance=customer)

    return render(request, 'core/stop_customer.html', {
        'form': form,
        'customer': customer,
        'selected_area_id': selected_area_id,
        'search': search,
    })


@login_required(login_url='/')
def deactivate_customer(request, customer_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customer = get_object_or_404(Customer, id=customer_id)
    customer.status = 'Inactive'
    customer.stop_start_date = None
    customer.stop_end_date = None
    customer.stop_reason = ''
    customer.save()

    messages.error(request, f'{customer.name} is now Inactive.')

    selected_area_id = request.GET.get('area')
    search = request.GET.get('search', '')
    if selected_area_id:
        url = f'/area-customers/?area={selected_area_id}'
        if search:
            url += f'&search={search}'
        return redirect(url)

    return redirect('customer_list')


def _month_index(month_code):
    return [m[0] for m in MONTH_CHOICES].index(month_code) + 1


def _calculate_amount(customer, month, year):
    year = int(year)
    month_no = _month_index(month)
    total_days = calendar.monthrange(year, month_no)[1]

    newspaper_amount = Decimal(str(
        customer.custom_newspaper_price
        if customer.custom_newspaper_price is not None
        else (customer.newspaper.monthly_price if customer.newspaper else 0)
    ))

    additional_paper_amount = Decimal(str(
        customer.custom_additional_price
        if customer.custom_additional_price is not None
        else (customer.additional_paper.monthly_price if customer.additional_paper else 0)
    ))

    weekly_magazine_amount = Decimal(str(
        customer.custom_weekly_price
        if customer.custom_weekly_price is not None
        else (customer.weekly_magazine.monthly_price if customer.weekly_magazine else 0)
    ))

    monthly_magazine_amount = Decimal(str(
        customer.custom_monthly_price
        if customer.custom_monthly_price is not None
        else (customer.monthly_magazine.monthly_price if customer.monthly_magazine else 0)
    ))

    base_total = (
        newspaper_amount +
        additional_paper_amount +
        weekly_magazine_amount +
        monthly_magazine_amount
    )

    stop_days = 0
    if customer.status == 'Stopped' and customer.stop_start_date and customer.stop_end_date:
        month_start = date(year, month_no, 1)
        month_end = date(year, month_no, total_days)

        overlap_start = max(customer.stop_start_date, month_start)
        overlap_end = min(customer.stop_end_date, month_end)

        if overlap_start <= overlap_end:
            stop_days = (overlap_end - overlap_start).days + 1

    active_days = max(total_days - stop_days, 0)
    factor = Decimal(active_days) / Decimal(total_days) if total_days else Decimal('1')
    total_amount = (base_total * factor).quantize(Decimal('0.01'))

    return {
        'newspaper_amount': float(newspaper_amount),
        'additional_paper_amount': float(additional_paper_amount),
        'weekly_magazine_amount': float(weekly_magazine_amount),
        'monthly_magazine_amount': float(monthly_magazine_amount),
        'total_amount': float(total_amount),
    }


@login_required(login_url='/')
def area_customer_list(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area')
    search = request.GET.get('search', '').strip()

    customers = None

    if selected_area_id:
        customers = Customer.objects.filter(area_id=selected_area_id)

        if search:
            customers = customers.filter(
                Q(name__icontains=search) | Q(phone__icontains=search)
            )

        customers = customers.select_related(
            'area',
            'newspaper',
            'additional_paper',
            'weekly_magazine',
            'monthly_magazine',
        ).order_by('name')

    return render(request, 'core/area_customer_list.html', {
        'areas': areas,
        'customers': customers,
        'selected_area_id': selected_area_id,
        'search': search,
    })


@login_required(login_url='/')
def area_bill_generate(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area_id = request.GET.get('area') or request.POST.get('area')
    month = request.GET.get('month') or request.POST.get('month')
    year = request.GET.get('year') or request.POST.get('year')

    customers = None

    if selected_area_id and month and year:
        customers = Customer.objects.filter(
            area_id=selected_area_id,
            status__in=['Active', 'Stopped']
        ).select_related(
            'newspaper',
            'additional_paper',
            'weekly_magazine',
            'monthly_magazine'
        ).order_by('name')

        for c in customers:
            amounts = _calculate_amount(c, month, year)
            c.total_preview = amounts['total_amount']

            message = f"Hello {c.name}, Your bill for {month} {year} is ₹{c.total_preview}"
            encoded = urllib.parse.quote(message)
            c.whatsapp_link = f"https://wa.me/91{c.phone}?text={encoded}"

    if request.method == 'POST' and customers:
        for c in customers:
            amounts = _calculate_amount(c, month, year)
            Bill.objects.get_or_create(
                customer=c,
                month=month,
                year=year,
                defaults={
                    'newspaper_amount': amounts['newspaper_amount'],
                    'additional_paper_amount': amounts['additional_paper_amount'],
                    'weekly_magazine_amount': amounts['weekly_magazine_amount'],
                    'monthly_magazine_amount': amounts['monthly_magazine_amount'],
                    'total_amount': amounts['total_amount'],
                    'is_paid': False,
                }
            )

        messages.success(request, "Area bills generated")
        return redirect(f'/area-billing/?area={selected_area_id}&month={month}&year={year}')

    return render(request, 'core/area_bill_generate.html', {
        'areas': areas,
        'customers': customers,
        'selected_area_id': selected_area_id,
        'month': month,
        'year': year,
        'month_choices': MONTH_CHOICES
    })


@login_required(login_url='/')
def area_payment_history(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')
    selected_area = request.GET.get('area')
    search = request.GET.get('search', '').strip()

    payments = None

    if selected_area or search:
        payments = Payment.objects.select_related('customer', 'bill', 'customer__area').all()

        if selected_area:
            payments = payments.filter(customer__area_id=selected_area)

        if search:
            payments = payments.filter(
                Q(customer__name__icontains=search) |
                Q(customer__phone__icontains=search)
            )

        payments = payments.order_by('-date')

    return render(request, 'core/area_payment_history.html', {
        'areas': areas,
        'payments': payments
    })


@login_required(login_url='/')
def verify_payment(request, payment_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'Verified'
    payment.save()
    payment.bill.is_paid = True
    payment.bill.save()
    return redirect('payment_history')


@login_required(login_url='/')
def reject_payment(request, payment_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'Rejected'
    payment.save()
    payment.bill.is_paid = False
    payment.bill.save()
    return redirect('payment_history')


def customer_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            customer = Customer.objects.get(phone=phone)

            if not customer.user:
                messages.error(request, "Customer account not linked.")
                return redirect('customer_login')

            user = authenticate(
                request,
                username=customer.user.username,
                password=password
            )

            if user is not None:
                login(request, user)
                return redirect('customer_dashboard')
            else:
                messages.error(request, "Invalid phone or password.")

        except Customer.DoesNotExist:
            messages.error(request, "Customer not found.")

    return render(request, 'core/customer_login.html')

@login_required(login_url='/customer-login/')
def customer_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    customer = get_object_or_404(Customer, user=request.user)
    latest_bill = Bill.objects.filter(customer=customer).order_by('-created_at').first()
    payments = Payment.objects.filter(customer=customer).order_by('-date')

    upi_link = ""
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
    })



@login_required(login_url='/customer-login/')
def customer_logout(request):
    logout(request)
    return redirect('customer_login')



@login_required(login_url='/customer-login/')
def upload_payment(request, bill_id):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    bill = get_object_or_404(Bill, id=bill_id)
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        screenshot = request.FILES.get('screenshot')

        Payment.objects.create(
            bill=bill,
            customer=customer,
            amount=amount,
            screenshot=screenshot
        )

        messages.success(request, "Payment uploaded successfully")
        return redirect('customer_dashboard')

    return render(request, 'core/upload_payment.html', {
        'bill': bill
    })

@login_required(login_url='/')
def delete_customer(request, customer_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Customer deleted successfully")
        return redirect('customer_list')

    return render(request, 'core/delete_customer.html', {
        'customer': customer
    })

@login_required(login_url='/')
def generate_bill(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customers = Customer.objects.all().order_by('name')

    month_choices = [
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

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        month = request.POST.get('month')
        year = request.POST.get('year')

        customer = Customer.objects.get(id=customer_id)

        # Simple calculation (you can improve later)
        total = 0

        if customer.custom_newspaper_price:
            total += customer.custom_newspaper_price
        elif customer.newspaper:
            total += customer.newspaper.monthly_price

        if customer.custom_additional_price:
            total += customer.custom_additional_price
        elif customer.additional_paper:
            total += customer.additional_paper.monthly_price

        if customer.custom_weekly_price:
            total += customer.custom_weekly_price
        elif customer.weekly_magazine:
            total += customer.weekly_magazine.monthly_price

        if customer.custom_monthly_price:
            total += customer.custom_monthly_price
        elif customer.monthly_magazine:
            total += customer.monthly_magazine.monthly_price

        Bill.objects.create(
            customer=customer,
            month=month,
            year=year,
            newspaper_amount=customer.custom_newspaper_price or (customer.newspaper.monthly_price if customer.newspaper else 0),
            additional_paper_amount=customer.custom_additional_price or (customer.additional_paper.monthly_price if customer.additional_paper else 0),
            weekly_magazine_amount=customer.custom_weekly_price or (customer.weekly_magazine.monthly_price if customer.weekly_magazine else 0),
            monthly_magazine_amount=customer.custom_monthly_price or (customer.monthly_magazine.monthly_price if customer.monthly_magazine else 0),
            total_amount=total
        )

        messages.success(request, "Bill generated successfully")
        return redirect('generate_bill')

    return render(request, 'core/generate_bill.html', {
        'customers': customers,
        'month_choices': month_choices
    })