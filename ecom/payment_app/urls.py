from django.urls import path
from .views import *

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('payment/', payment, name='payment'),
    path('payment-success/', payment_success, name='payment_success'),
    ]
