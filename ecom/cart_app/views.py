from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from product_app.models import Product
from django.contrib.auth.decorators import login_required

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

def add_to_cart(request, product_id):
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('view_cart')

# cart_app/views.py
def view_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()

    # in views.py
    cart_items = []
    total_price = 0

    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
        for item in cart_items:
            item.subtotal = item.quantity * item.product.price
        total_price = sum(item.subtotal for item in cart_items)


    return render(request, 'view_cart.html', {'cart_items': cart_items,'total_price': total_price,})

from django.shortcuts import redirect
from .models import CartItem
from product_app.models import Product
from django.contrib import messages

def update_cart(request):
    if request.method == "POST":
        for item in CartItem.objects.filter(cart__user=request.user):
            qty_key = f"quantity_{item.id}"
            new_qty = int(request.POST.get(qty_key, item.quantity))
            product = item.product

            # Adjust stock
            if new_qty != item.quantity:
                delta = new_qty - item.quantity
                if product.stock >= delta:
                    product.stock -= delta
                    item.quantity = new_qty
                    item.save()
                    product.save()
                else:
                    messages.error(request, f"Not enough stock for {product.name}")
        messages.success(request, "Cart updated successfully.")
    return redirect('view_cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('view_cart')
