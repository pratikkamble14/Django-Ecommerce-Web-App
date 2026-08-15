from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def register_view(request):
    form = UserRegistrationForm()
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            
            messages.success(request, "Registered successfully. You can now login.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    
    return render(request, 'register.html', {'form': form})



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('product_list')  # Use the correct name from product_app.urls
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, template_name='login.html')


def logout_view(request):
    logout(request)
    return redirect('login')