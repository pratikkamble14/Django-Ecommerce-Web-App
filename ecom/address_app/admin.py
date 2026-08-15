from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'state', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country', 'state', 'city')
    search_fields = ('full_name', 'user__username', 'phone', 'address_line1', 'city', 'postal_code')
    ordering = ('-created_at',)
