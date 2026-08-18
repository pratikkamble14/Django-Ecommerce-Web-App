# product_app/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category

def product_list(request):
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')

    products = Product.objects.all()
    categories = Category.objects.all()

    if category_id:
        products = products.filter(category__id=category_id)

    if search_query:
        products = products.filter(name__icontains=search_query)

    return render(request, 'product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
    })


def product_detail(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')  # your login view name
    product = get_object_or_404(Product, pk=pk)
    return render(request, template_name='product_detail.html',context={'product': product})

def category_list(request):
    categories = Category.objects.all()
    return render(request, template_name='category_list.html',context= {'categories': categories})


def search_view(request):
    query = request.GET.get('q')
    results = Product.objects.filter(name__icontains=query) if query else []
    return render(request, 'search_result.html', {'query': query, 'results': results})
