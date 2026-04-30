from decimal import Decimal
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
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
import base64 
from twilio.rest import Client
import os

def generate_qr(upi_id, name, amount):
    upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}"
    
    qr = qrcode.make(upi_url)
    
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    
    return buffer.getvalue()

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

            bill = Bill.objects.filter(
                customer=c,
                month=month,
                year=year
            ).order_by('-id').first()

            if bill:
                bill.newspaper_amount = amounts['newspaper_amount']
                bill.additional_paper_amount = amounts['additional_paper_amount']
                bill.weekly_magazine_amount = amounts['weekly_magazine_amount']
                bill.monthly_magazine_amount = amounts['monthly_magazine_amount']
                bill.total_amount = amounts['total_amount']
                bill.payment_status = 'Pending'
                bill.save()
            else:
                bill = Bill.objects.create(
                    customer=c,
                    month=month,
                    year=year,
                    newspaper_amount=amounts['newspaper_amount'],
                    additional_paper_amount=amounts['additional_paper_amount'],
                    weekly_magazine_amount=amounts['weekly_magazine_amount'],
                    monthly_magazine_amount=amounts['monthly_magazine_amount'],
                    total_amount=amounts['total_amount'],
                    payment_status='Pending',
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
    print("VERIFY VIEW HIT")  
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
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        customer = Customer.objects.filter(phone=phone).first()

        if customer and password == "custo@12345":
            request.session['customer_id'] = customer.id
            return redirect('/customer-dashboard/')

    return render(request, 'core/customer_login.html')

def customer_logout(request):
    logout(request)
    return redirect('/customer-login/')



def customer_dashboard(request):
    customer_id = request.session.get('customer_id')

    if not customer_id:
        return redirect('/customer-login/')

    customer = get_object_or_404(Customer, id=customer_id)

    bills = Bill.objects.filter(customer=customer).order_by('-id')

    for bill in bills:

      upi_link = f"upi://pay?pa={settings.OWNER_UPI_ID}&pn={settings.OWNER_NAME}&am={bill.total_amount}"

    # Generate QR
    qr = qrcode.make(upi_link)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    bill.qr_code = qr_base64
    bill.upi_link = upi_link



def upload_payment(request, bill_id):
    customer_id = request.session.get('customer_id')

    if not customer_id:
        return redirect('/customer-login/')

    customer = get_object_or_404(Customer, id=customer_id)
    bill = get_object_or_404(Bill, id=bill_id, customer=customer)

    if request.method == 'POST':
        Payment.objects.create(
            bill=bill,
            customer=customer,
            amount=bill.total_amount,
            payment_method='UPI',
            screenshot=request.FILES.get('proof'),
            status='Pending'
        )

        messages.success(request, "Payment proof uploaded successfully. Waiting for admin verification.")
        return redirect('/customer-dashboard/')

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

@login_required(login_url='/')
def payment_history(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    areas = Area.objects.all().order_by('name')

    selected_area = request.GET.get('area')
    selected_method = request.GET.get('method')

    payments = Payment.objects.select_related(
        'customer',
        'bill',
        'customer__area'
    ).all().order_by('-date')

    if selected_area:
        payments = payments.filter(customer__area_id=selected_area)

    if selected_method:
        payments = payments.filter(payment_method=selected_method)

    return render(request, 'core/area_payment_history.html', {
        'areas': areas,
        'payments': payments,
        'selected_area': selected_area,
        'selected_method': selected_method,
    })



@login_required(login_url='/')
def verify_payment(request, payment_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'Verified'
    payment.save()

    messages.success(request, 'Payment verified successfully.')
    return redirect('payment_history')


@login_required(login_url='/')
def reject_payment(request, payment_id):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'Rejected'
    payment.save()

    messages.error(request, 'Payment rejected.')
    return redirect('payment_history')



@login_required(login_url='/')
def add_manual_payment(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    customers = Customer.objects.all().order_by('name')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        month = request.POST.get('month')
        year = request.POST.get('year')
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('amount')

        customer = get_object_or_404(Customer, id=customer_id)

        # 🔥 Find bill
        bill = Bill.objects.filter(
            customer=customer,
            month=month,
            year=year
        ).first()

        if not bill:
            messages.error(request, "Bill not found for selected month")
            return redirect('add_manual_payment')

        # 🔥 Create payment
        Payment.objects.create(
            bill=bill,
            customer=customer,
            amount=amount,
            payment_method=payment_method,
            status='Verified'
        )

        messages.success(request, "Payment added successfully")
        return redirect('payment_history')

    return render(request, 'core/add_manual_payment.html', {
        'customers': customers,
        'month_choices': MONTH_CHOICES
    })

def send_whatsapp_message(phone, message):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=f"whatsapp:+91{phone}"
    )


def test_whatsapp(request):
    send_whatsapp_message(
        "9483476931",
        "Hello Varun 👋 NewsHub WhatsApp is working 🚀"
    )
    return HttpResponse("Message Sent")


def send_whatsapp_invoice(phone, message, image_url):
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        body=message,
        media_url=[image_url],
        to=f"whatsapp:+91{phone}"
    )

@login_required(login_url='/')
def bulk_send_invoice(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    if request.method == "POST":
        area_id = request.POST.get("area")
        month = request.POST.get("month")
        year = request.POST.get("year")

        customers = Customer.objects.filter(area_id=area_id, status="Active")

        for customer in customers:
            bill = Bill.objects.filter(
                customer=customer,
                month=month,
                year=year
            ).order_by('-id').first()

            if bill:
                image_url = generate_invoice_image(bill)

                message = f"""
Hello {customer.name},

Your Newspaper Bill for {month} {year} is ₹{bill.total_amount}

Please check your invoice attached.

Thank you 🙏
"""
                send_whatsapp_invoice(customer.phone, message, image_url)

        messages.success(request, "Invoices sent successfully.")
        return redirect('area_bill')

    return redirect('area_bill')


def generate_invoice_image(bill):
    customer = bill.customer

    width, height = 900, 1250
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 42)
        heading_font = ImageFont.truetype("arial.ttf", 28)
        normal_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
        big_font = ImageFont.truetype("arial.ttf", 34)
    except:
        title_font = ImageFont.load_default()
        heading_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        big_font = ImageFont.load_default()

    # Border
    draw.rectangle((20, 20, width - 20, height - 20), outline="blue", width=3)

    # Header
    draw.text((230, 40), "PRADEEP NEWS AGENCY", fill="navy", font=title_font)
    draw.text((270, 95), "Newspaper Distribution Service", fill="black", font=normal_font)
    draw.text((220, 130), "Kumaraswamy Layout 2nd Stage, Bangalore", fill="black", font=small_font)
    draw.text((650, 50), "Mob: 99645 21822", fill="black", font=small_font)

    draw.line((40, 175, width - 40, 175), fill="blue", width=2)

    # Bill heading
    draw.text((385, 190), "CASH BILL", fill="navy", font=heading_font)

    # Customer details
    draw.text((50, 250), f"No: {bill.id}", fill="red", font=normal_font)
    draw.text((620, 250), f"Date: {date.today().strftime('%d/%m/%Y')}", fill="black", font=normal_font)

    draw.text((50, 300), f"Name: {customer.name}", fill="black", font=normal_font)
    draw.text((620, 300), f"Phone: {customer.phone}", fill="black", font=normal_font)

    draw.text((50, 350), f"Area: {customer.area.name}", fill="black", font=normal_font)
    draw.text((50, 395), f"Address: {customer.address[:55]}", fill="black", font=small_font)

    draw.line((40, 440, width - 40, 440), fill="blue", width=2)

    # Table
    draw.rectangle((50, 470, 850, 790), outline="blue", width=2)
    draw.line((650, 470, 650, 790), fill="blue", width=2)
    draw.line((50, 520, 850, 520), fill="blue", width=2)

    draw.text((80, 485), "Particulars", fill="black", font=normal_font)
    draw.text((700, 485), "Amount", fill="black", font=normal_font)

    y = 540

    items = [
        ("Newspaper", bill.newspaper_amount),
        ("Additional Paper", bill.additional_paper_amount),
        ("Weekly Magazine", bill.weekly_magazine_amount),
        ("Monthly Magazine", bill.monthly_magazine_amount),
    ]

    for name, amount in items:
        if amount and amount > 0:
            draw.text((80, y), name, fill="black", font=normal_font)
            draw.text((700, y), f"Rs. {amount}", fill="black", font=normal_font)
            y += 50

    draw.line((50, 800, 850, 800), fill="blue", width=2)

    # Month + Total
    draw.text((60, 830), f"For the Month of: {bill.month} {bill.year}", fill="black", font=normal_font)
    draw.text((610, 830), "Total", fill="black", font=big_font)
    draw.text((720, 830), f"Rs. {bill.total_amount}", fill="red", font=big_font)

    # QR Code
    upi_url = f"upi://pay?pa={settings.OWNER_UPI_ID}&pn={settings.OWNER_NAME}&am={bill.total_amount}"

    qr = qrcode.make(upi_url)
    qr = qr.resize((170, 170))

    img.paste(qr, (60, 900))

    draw.text((250, 920), "SCAN & PAY", fill="navy", font=heading_font)
    draw.text((250, 965), f"UPI ID: {settings.OWNER_UPI_ID}", fill="black", font=normal_font)
    draw.text((250, 1010), "Pay using GPay / PhonePe / Paytm", fill="black", font=normal_font)

    draw.text((600, 1120), "Signature", fill="black", font=normal_font)

    # Save
    invoice_dir = os.path.join(settings.MEDIA_ROOT, "invoices")
    os.makedirs(invoice_dir, exist_ok=True)

    file_path = os.path.join(invoice_dir, f"invoice_{bill.id}.png")
    img.save(file_path)

    return f"{settings.SITE_URL}/media/invoices/invoice_{bill.id}.png"


def test_invoice(request):
    bill = Bill.objects.latest('id')
    image_url = generate_invoice_image(bill)
    return HttpResponse(f"Invoice created: <a href='{image_url}'>{image_url}</a>")


@login_required(login_url='/')
def uploaded_payments(request):
    if not request.user.is_staff:
        return redirect('customer_dashboard')

    payments = Payment.objects.select_related(
        'customer', 'bill', 'customer__area'
    ).filter(status='Pending').order_by('-date')

    return render(request, 'core/uploaded_payments.html', {
        'payments': payments
    })


def home(request):
    return render(request, "core/home.html")