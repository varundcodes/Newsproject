from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('add-area/', views.add_area, name='add_area'),
    path('add-newspaper/', views.add_newspaper, name='add_newspaper'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('customer-list/', views.customer_list, name='customer_list'),

    path('area-customers/', views.area_customer_list, name='area_customer_list'),
    path('area-bills/', views.area_bill_generate, name='area_bill_generate'),
    path('area-payments/', views.area_payment_history, name='area_payment_history'),

    path('generate-bill/', views.generate_bill, name='generate_bill'),

    path('customer-login/', views.customer_login, name='customer_login'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer-logout/', views.customer_logout, name='customer_logout'),
    path('upload-payment/<int:bill_id>/', views.upload_payment, name='upload_payment'),
]