from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('login_view/', views.login_view, name='login_view'),
    path('signup_view/', views.signup_view, name='signup_view'),
 ]



