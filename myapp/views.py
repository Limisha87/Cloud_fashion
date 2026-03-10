from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Product, Order, Payment, Cart
from django.contrib.auth.decorators import login_required
from django.conf import settings
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
User = get_user_model()

webhook_secret = "cloudfashion123"


def home(request):
    return render(request, 'myapp/index.html')


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        print("EMAIL:", email)
        print("PASSWORD:", password)

        user = authenticate(request, username=email, password=password)

        print("USER:", user)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "myapp/login.html")


def signup_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup_view')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup_view')

        user = User.objects.create_user(
            email=email,
            password=password1
        )

        messages.success(request, 'Account created successfully')
        return redirect('login_view')

    return render(request, 'myapp/signup.html')


def logout_view(request):
    logout(request)          # session destroy
    return redirect('home') # login page par bhej do


def product_list(request):
    products = Product.objects.all()
    return render(request, 'myapp/product_list.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'myapp/product_detail.html', {'product': product})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    # Convert key to string
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session['cart'] = cart
    request.session.modified = True

    print("CART DATA:", request.session['cart'])  # Debug

    return redirect('cart')


def remove_one_from_cart(request, pk):
    cart = request.session.get('cart', {})

    if str(pk) in cart:
        if cart[str(pk)] > 1:
            cart[str(pk)] -= 1   # only 1 quantity
        else:
            del cart[str(pk)]    # quantity = 1 ho to product remove

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')



def cart_page(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        product.quantity = quantity
        product.subtotal = product.price * quantity
        total += product.subtotal
        products.append(product)

    return render(request, 'myapp/cart.html', {
        'products': products,
        'total': total
    })


@csrf_exempt
def payment_success(request):
    if request.method == "POST":

        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        payment = Payment.objects.get(order_id=razorpay_order_id)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # ✅ If verification successful
            payment.payment_id = razorpay_payment_id
            payment.status = "Success"
            payment.order.is_paid = True
            payment.order.save()
            payment.save()

            return HttpResponse("Payment Verified & Successful ✅")

        except:
            payment.status = "Failed"
            payment.save()
            return HttpResponse("Payment Verification Failed ❌")

    return HttpResponse("Invalid Request")



@csrf_exempt
def razorpay_webhook(request):
    webhook_secret = "YOUR_WEBHOOK_SECRET"

    body = request.body
    received_signature = request.headers.get('X-Razorpay-Signature')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_webhook_signature(
            body,
            received_signature,
            webhook_secret
        )

        payload = json.loads(body)

        if payload['event'] == 'payment.captured':
            razorpay_order_id = payload['payload']['payment']['entity']['order_id']

            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.status = "Success"
            payment.order.is_paid = True
            payment.order.save()
            payment.save()

        return HttpResponse(status=200)

    except:
        return HttpResponse(status=400)
    


def payment(request):
    return render(request, 'payment.html')

@login_required
def checkout(request):

    cart = request.session.get('cart', {})
    total_amount = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        total_amount += product.price * quantity

    print("TOTAL AMOUNT:", total_amount)

    if total_amount <= 0:
        messages.error(request, "Your cart is empty")
        return redirect("cart")

    amount_in_paise = int(total_amount)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    }

    razorpay_order = client.order.create(data=payment_data)

    return render(request, "myapp/checkout.html", {
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount_in_paise
    })
    
    
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, "myapp/dashboard.html", {
        "orders": orders
    })














































































































































































