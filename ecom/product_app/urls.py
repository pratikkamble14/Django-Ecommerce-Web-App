from django.urls import path
from .views import *

urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('categories/', category_list, name='category_list'),
    path('search/', search_view, name='search'),  

    
]
