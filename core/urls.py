from django.urls import path
from . import views

urlpatterns = [
    # Admin
    path("", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="logout"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # Setup
    path("add-area/", views.add_area, name="add_area"),
    path("add-newspaper/", views.add_newspaper, name="add_newspaper"),
    path("add-customer/", views.add_customer, name="add_customer"),

    # Customers
    path('customer-login/', views.customer_login, name='customer_login'),
    path("customer-logout/", views.customer_logout, name="customer_logout"),

    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),


    path("customers/", views.customer_list, name="customer_list"),
    path("area-customers/", views.area_customer_list, name="area_customer_list"),
    path("customers/activate/<int:customer_id>/", views.activate_customer, name="activate_customer"),
    path("customers/stop/<int:customer_id>/", views.stop_customer, name="stop_customer"),
    path("customers/deactivate/<int:customer_id>/", views.deactivate_customer, name="deactivate_customer"),
    path("customer-delete/<int:customer_id>/", views.delete_customer, name="delete_customer"),

    # Billing
    path("generate-bill/", views.generate_bill, name="generate_bill"),
    path("area-billing/", views.area_bill_generate, name="area_bill"),

    # Payments
    path("payment-history/", views.area_payment_history, name="payment_history"),
    path('verify-payment/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path("payments/reject/<int:payment_id>/", views.reject_payment, name="reject_payment"),
    path("upload-payment/<int:bill_id>/", views.upload_payment, name='upload_payment'),

]