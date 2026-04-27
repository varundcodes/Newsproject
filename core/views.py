from decimal import Decimal
from datetime import date
import calendar
import base64
import urllib.parse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
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

    return render(request, 'core/admin_dashboard.html', {
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
        else (customer.weekly_magazine.weekly_price * 4 if customer.weekly_magazine else 0)
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
    year = request.GET.get('year') or request.POST.get('year') or date.today().year

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

            bill, created = Bill.objects.update_or_create(
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

            message = f"""
Hello {c.name},

Your Newspaper Bill for {month} {year} is ₹{bill.total_amount}

Pay using UPI:
upi://pay?pa={settings.OWNER_UPI_ID}&pn={settings.OWNER_NAME}&am={bill.total_amount}

Thank you 🙏
"""

            encoded = urllib.parse.quote(message)
            c.whatsapp_link = f"https://wa.me/91{c.phone}?text={encoded}"
            c.bill_amount = bill.total_amount

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
    if request.method == "POST":
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        try:
            customer = Customer.objects.get(phone=phone)
            user = customer.user
        except Customer.DoesNotExist:
            user = None

        if user:
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                return redirect("customer_dashboard")

        return render(request, "core/customer_login.html", {
            "error": "Invalid phone or password"
        })

    return render(request, "core/customer_login.html")


def customer_logout(request):
    logout(request)
    return redirect("customer_login")



@login_required(login_url='/customer-login/')
def customer_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    customer = get_object_or_404(Customer, user=request.user)
    latest_bill = Bill.objects.filter(customer=customer).order_by('-created_at').first()
    payments = Payment.objects.filter(customer=customer).order_by('-date')

    upi_link = ""
    qr_base64 = None

    if latest_bill:
        upi_link = (
            f"upi://pay?pa={settings.OWNER_UPI_ID}"
            f"&pn={settings.OWNER_NAME}"
            f"&am={latest_bill.total_amount}"
            f"&cu=INR"
        )

        qr_image = generate_qr(
            settings.OWNER_UPI_ID,
            settings.OWNER_NAME,
            latest_bill.total_amount
        )

        import base64
        qr_base64 = base64.b64encode(qr_image).decode()

    # ✅ ALWAYS RETURN (outside if)
    return render(request, 'core/customer_dashboard.html', {
        'customer': customer,
        'latest_bill': latest_bill,
        'payments': payments,
        'upi_link': upi_link,
        'owner_upi': settings.OWNER_UPI_ID,
        'owner_name': settings.OWNER_NAME,
        'qr_code': qr_base64,
    })


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

    customers = Customer.objects.all()
    generated_bill = None
    whatsapp_link = None

    if request.method == "POST":
        customer_id = request.POST.get('customer')
        month = request.POST.get('month')
        year = request.POST.get('year')

        customer = Customer.objects.get(id=customer_id)

        # 🔥 Calculate amounts
        amounts = _calculate_amount(customer, month, year)

        # 🔥 Save or update bill
        bill, created = Bill.objects.update_or_create(
            customer=customer,
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

        generated_bill = bill

        # 🔥 FINAL WHATSAPP MESSAGE
        message = f"""
Hello {customer.name},

📰 Your Newspaper Bill for {month} {year}

💰 Amount: ₹{bill.total_amount}

👉 View & Pay Here:
http://127.0.0.1:8000/customer-login/

🔐 Login Details:
Username: {customer.phone}
Password: custo@12345

Thank you 🙏
"""

        encoded_message = urllib.parse.quote(message)

        whatsapp_link = f"https://wa.me/91{customer.phone}?text={encoded_message}"

    return render(request, 'core/generate_bill.html', {
        'customers': customers,
        'generated_bill': generated_bill,
        'whatsapp_link': whatsapp_link,
        'month_choices': MONTH_CHOICES
    })

    encoded_message = urllib.parse.quote(message)
    whatsapp_link = f"https://wa.me/91{customer.phone}?text={encoded_message}"

    messages.success(request, "Bill generated successfully")

    return render(request, 'core/generate_bill.html', {
        'customers': customers,
        'month_choices': MONTH_CHOICES,
        'generated_bill': generated_bill,
        'whatsapp_link': whatsapp_link,
    })

def generate_qr(upi_id, name, amount):
    upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}"
    
    qr = qrcode.make(upi_url)
    
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    
    return buffer.getvalue()