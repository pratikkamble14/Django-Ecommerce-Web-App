from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart_app.models import Cart, CartItem
from order_app.models import Order, OrderItem
from order_app.forms import OrderForm
from django.contrib import messages

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart)
    total = 0

    for item in cart_items:
        item.subtotal = item.quantity * item.product.price
        total += item.subtotal

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Check stock before processing order
            for item in cart_items:
                if item.quantity > item.product.stock:
                    messages.error(request, f"Not enough stock for {item.product.name}. Available: {item.product.stock}")
                    return redirect('view_cart')

            order = form.save(commit=False)
            order.user = request.user
            order.paid = False
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
                item.product.stock -= item.quantity
                item.product.save()

            cart_items.delete()

            request.session['order_id'] = order.id
            return redirect('payment')

    else:
        form = OrderForm()

    return render(request, 'checkout.html', {
        'form': form,
        'items': cart_items,
        'total': total
    })


@login_required
def payment(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('checkout')

    order = get_object_or_404(Order, id=order_id, user=request.user)
    total = sum(item.price * item.quantity for item in order.items.all())

    if request.method == 'POST':
        order.paid = True
        order.save()
        del request.session['order_id']
        return redirect('payment_success')

    return render(request, 'payment.html', {'order': order, 'total': total})


@login_required
def payment_success(request):
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.paid = True
        order.save()
        del request.session['order_id']
    return render(request, 'payment_success.html')

