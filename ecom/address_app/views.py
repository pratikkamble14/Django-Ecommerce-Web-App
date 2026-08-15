from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Address
from .forms import AddressForm
from django.contrib import messages


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address added successfully.")
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'address_form.html', {'form': form})

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'address_list.html', {'addresses': addresses})

@login_required
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'address_form.html', {'form': form})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted.")
        return redirect('address_list')
    return render(request, 'address_confirm_delete.html', {'address': address})
