from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login_view'),
    path('signup/', views.signup_view, name='signup_view'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('remove-one/<int:pk>/',views.remove_one_from_cart,name='remove_one_from_cart'),
    path("checkout/", views.checkout, name="checkout"),
    path('razorpay-webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    
 ]

    


