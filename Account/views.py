from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import datetime, timedelta
from .models import BankAccount, Transaction
from .forms import StatementPeriodForm, DepositForm, WithdrawForm, TransferForm, PinChangeForm
import pdfkit
from django.contrib.auth import authenticate, login,logout



def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    services = [
        {
            'title': 'Personal Banking',
            'description': 'Comprehensive personal banking solutions tailored to your needs.',
            'icon': '👨‍💼'
        },
        {
            'title': 'Business Accounts',
            'description': 'Specialized accounts and services for businesses of all sizes.',
            'icon': '🏢'
        },
        {
            'title': 'Loans',
            'description': 'Competitive loan products with flexible repayment options.',
            'icon': '💰'
        },
        {
            'title': 'Investment',
            'description': 'Expert investment advice and wealth management services.',
            'icon': '📈'
        },
        {
            'title': 'Mobile Banking',
            'description': 'Bank on the go with our award-winning mobile app.',
            'icon': '📱'
        },
        {
            'title': 'Card Services',
            'description': 'Secure debit and credit cards with great benefits.',
            'icon': '💳'
        }
    ]
    return render(request, 'services.html', {'services': services})

def contact(request):
    branches = [
        {'name': 'Head Office', 'address': '123 Financial Street, Banking City', 'phone': '+1 (555) 123-4567'},
        {'name': 'Downtown Branch', 'address': '456 Commerce Avenue, Downtown', 'phone': '+1 (555) 234-5678'},
        {'name': 'Westside Branch', 'address': '789 Market Road, Westside', 'phone': '+1 (555) 345-6789'},
    ]
    return render(request, 'contact.html', {'branches': branches})

@login_required
def account_dashboard(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    return render(request, "dashboard.html", {"account": account})

@login_required
def view_transactions(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    
    # Get filter parameters from request
    transaction_type = request.GET.get('type')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    
    transactions = account.transactions.all()
    
    # Apply filters if provided
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    context = {
        'account': account,
        'transactions': transactions,
        'transaction_types': dict(Transaction.TRANSACTION_TYPES),
        'filter_type': transaction_type,
        'filter_from': date_from,
        'filter_to': date_to,
    }
    return render(request, 'transaction_list.html', context)

@login_required
def view_statement(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    
    if request.method == 'POST':
        form = StatementPeriodForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            format = form.cleaned_data['format']
            
            transactions = account.transactions.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('-date')
            
            opening_balance = account.transactions.filter(
                date__lt=start_date
            ).order_by('-date').first()
            
            opening_balance = opening_balance.balance_after if opening_balance else account.balance
            
            closing_balance = transactions.last().balance_after if transactions.exists() else opening_balance
            
            context = {
                'account': account,
                'transactions': transactions,
                'start_date': start_date,
                'end_date': end_date,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'total_deposits': transactions.filter(transaction_type='D').aggregate(Sum('amount'))['amount__sum'] or 0,
                'total_withdrawals': transactions.filter(transaction_type='W').aggregate(Sum('amount'))['amount__sum'] or 0,
            }
            
            if format == 'pdf':
                # Generate PDF statement
                html = render_to_string('statement_pdf.html', context)
                options = {
                    'encoding': 'UTF-8',
                    'quiet': '',
                    'page-size': 'A4',
                    'orientation': 'Portrait',
                    'margin-top': '0.5in',
                    'margin-right': '0.5in',
                    'margin-bottom': '0.5in',
                    'margin-left': '0.5in',
                }
                pdf = pdfkit.from_string(html, False, options=options)
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}_{start_date}_to_{end_date}.pdf"'
                return response
            else:
                # HTML view
                return render(request, 'statement.html', context)
    else:
        # Default to last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        form = StatementPeriodForm(initial={
            'start_date': start_date.date(),
            'end_date': end_date.date()
        })
    
    return render(request, 'statement_form.html', {
        'account': account,
        'form': form
    })

@login_required
def withdraw_cash(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    
    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if amount > account.balance:
                messages.error(request, "Insufficient funds for this withdrawal")
                return render(request, 'withdraw.html', {
                    'account': account,
                    'form': form
                })
            
            account.balance -= amount
            account.save()
            
            # Record withdrawal transaction
            Transaction.objects.create(
                account=account,
                transaction_type='W',
                amount=amount,
                description=f"Cash withdrawal",
                balance_after=account.balance
            )
            
            messages.success(request, f'Successfully withdrew ${amount:.2f}')
            return redirect('account_dashboard', account_number=account.account_number)
    else:
        form = WithdrawForm()
    
    return render(request, 'withdraw.html', {
        'account': account,
        'form': form
    })

@login_required
def transfer_cash(request, account_number):
    sender_account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            recipient_account_number = form.cleaned_data['recipient_account']
            amount = form.cleaned_data['amount']
            
            try:
                recipient_account = BankAccount.objects.get(account_number=recipient_account_number)
                
                if amount > sender_account.balance:
                    messages.error(request, "Insufficient funds for this transfer")
                    return render(request, 'transfer.html', {
                        'account': sender_account,
                        'form': form
                    })
                
                if sender_account == recipient_account:
                    messages.error(request, "Cannot transfer to the same account")
                    return render(request, 'transfer.html', {
                        'account': sender_account,
                        'form': form
                    })
                
                # Perform the transfer
                sender_account.balance -= amount
                recipient_account.balance += amount
                sender_account.save()
                recipient_account.save()
                
                # Record transactions for both accounts
                Transaction.objects.create(
                    account=sender_account,
                    transaction_type='T',
                    amount=amount,
                    description=f"Transfer to {recipient_account.account_number}",
                    balance_after=sender_account.balance,
                    related_account=recipient_account
                )
                
                Transaction.objects.create(
                    account=recipient_account,
                    transaction_type='T',
                    amount=amount,
                    description=f"Transfer from {sender_account.account_number}",
                    balance_after=recipient_account.balance,
                    related_account=sender_account
                )
                
                messages.success(request, f'Successfully transferred ${amount:.2f} to account {recipient_account_number}')
                return redirect('account_dashboard', account_number=sender_account.account_number)
            
            except BankAccount.DoesNotExist:
                messages.error(request, "Recipient account not found")
                return render(request, 'transfer.html', {
                    'account': sender_account,
                    'form': form
                })
    else:
        form = TransferForm()
    
    return render(request, 'transfer.html', {
        'account': sender_account,
        'form': form
    })

@login_required
def change_pin(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    
    if request.method == 'POST':
        form = PinChangeForm(request.POST)
        if form.is_valid():
            old_pin = form.cleaned_data['old_pin']
            new_pin = form.cleaned_data['new_pin']
            confirm_pin = form.cleaned_data['confirm_pin']
            
            if old_pin != account.pin:
                messages.error(request, "Incorrect current PIN")
            elif new_pin != confirm_pin:
                messages.error(request, "New PINs do not match")
            else:
                account.pin = new_pin
                account.save()
                messages.success(request, "PIN changed successfully")
                return redirect('account_dashboard', account_number=account.account_number)
    else:
        form = PinChangeForm()
    
    return render(request, 'change_pin.html', {
        'account': account,
        'form': form
    })

@login_required
def deposit_cash(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, user=request.user)
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            account.balance += amount
            account.save()
            
            # Record transaction
            Transaction.objects.create(
                account=account,
                transaction_type='D',
                amount=amount,
                description=f"Cash deposit",
                balance_after=account.balance
            )
            
            messages.success(request, f'Successfully deposited ${amount:.2f}')
            return redirect('account_dashboard', account_number=account.account_number)
    else:
        form = DepositForm()
    
    return render(request, 'deposit.html', {
        'account': account,
        'form': form
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Check if user has any accounts
            if user.bankaccount_set.exists():
                account = user.bankaccount_set.first()
                return redirect('account_dashboard', account_number=account.account_number)
            else:
                messages.info(request, "You don't have any accounts yet")
                return redirect('create_account')  # Redirect to account creation
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'login.html')
    return render(request, 'login.html')
@login_required
def create_account(request):
    if request.method == 'POST':
        # Create a new account for the user
        account = BankAccount.objects.create(
            user=request.user,
            balance=0.00,
            # other required fields
        )
        return redirect('account_dashboard', account_number=account.account_number)
    
    return render(request, 'create_account.html')
@login_required
def user_logout(request):
    logout(request)
    return render(request, 'logout.html')