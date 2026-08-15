from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.address_list, name='address_list'),
    path('create/', views.address_create, name='address_create'),
    path('update/<int:pk>/', views.address_update, name='address_update'),
    path('delete/<int:pk>/', views.address_delete, name='address_delete'),
]
