from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Order, OrderItem
from .forms import OrderForm
from product_app.models import Product
from cart_app.models import Cart, CartItem


def get_cart_items(user):
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return []
    return CartItem.objects.filter(cart=cart)


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'my_orders.html', {'orders': orders})


@login_required
def create_order(request):
    cart_items = get_cart_items(request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            return redirect('order_summary', order_id=order.id)
    else:
        form = OrderForm()

    for item in cart_items:
        item.subtotal = item.product.price * item.quantity

    return render(request, 'order_form.html', {
        'form': form,
        'cart_items': cart_items,
        'total': sum(item.product.price * item.quantity for item in cart_items)
    })


@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    for item in items:
        item.subtotal = item.price * item.quantity
    total = sum(item.price * item.quantity for item in items)
    return render(request, 'order_summary.html', {
        'order': order,
        'items': items,
        'total': total
    })


###############################






@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('my_orders')
    return HttpResponseForbidden("Invalid request method.")
