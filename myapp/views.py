from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Product, Order, Payment
from django.contrib.auth.decorators import login_required
from django.conf import settings
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json



User = get_user_model()

def home(request):
    return render(request, 'myapp/index.html')


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

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
            password=password1,
            is_active=True
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


def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    cart = request.session.get('cart', {})

    if str(pk) in cart:
        cart[str(pk)] += 1
    else:
        cart[str(pk)] = 1

    request.session['cart'] = cart
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



def cart_view(request):
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
    if not cart:
        messages.error(request, "Cart is empty")
        return redirect('cart')

    total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        total += product.price * quantity

    oorder = Order.objects.create(
    user=request.user,
    total_amount=total,
    status='Pending'
)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment_data = {
        "amount": int(total * 100),
        "currency": "INR",
    }

    razorpay_order = client.order.create(data=payment_data)

    payment = Payment.objects.create(
        user=request.user,
        order=order,
        order_id=razorpay_order['id'],
        amount=total,
        status="Pending"
    )

    context = {
        "order": order,
        "payment": payment,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": int(total * 100),
        "order_id": razorpay_order['id'],
    }

    return render(request, "checkout.html", context)