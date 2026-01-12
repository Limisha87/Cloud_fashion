from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    return render(request, 'myapp/index.html')

def login_view(request):
    if request.method == "POST":
    
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful')
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login_view')

    return render(request, 'myapp/login.html')


def signup_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup_view')

        User.objects.create_user(
            email=email,
            password=password
        )

        messages.success(request, 'Account created successfully')
        return redirect('login_view')

    return render(request, 'myapp/signup.html')


