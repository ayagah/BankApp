from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('account/create/', views.create_account, name='create_account'),
    path('account/<str:account_number>/', views.account_dashboard, name='account_dashboard'),
    path('account/<str:account_number>/deposit/', views.deposit_cash, name='deposit_cash'),
    path('account/<str:account_number>/withdraw/', views.withdraw_cash, name='withdraw_cash'),
    path('account/<str:account_number>/transfer/', views.transfer_cash, name='transfer_cash'),
    path('account/<str:account_number>/change-pin/', views.change_pin, name='change_pin'),
    path('account/<str:account_number>/transactions/', views.view_transactions, name='view_transactions'),
    path('account/<str:account_number>/statement/', views.view_statement, name='view_statement'),
]