from django.urls import path
from .views import *

urlpatterns = [
    path('create/',create_order, name='create_order'),
    path('summary/<int:order_id>/',order_summary, name='order_summary'),
    path('my-orders/', my_orders, name='my_orders'),
    path('delete/<int:order_id>/',delete_order, name='delete_order'),



]
