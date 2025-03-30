from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BankAccount(models.Model):
    # Required fields
    account_number = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pin = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    # Transaction relationship
    transactions = models.ManyToManyField('self', through='Transaction', 
                                        symmetrical=False,
                                        related_name='related_transactions')

    def __str__(self):
        return f"{self.account_name} ({self.account_number})"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('D', 'Deposit'),
        ('W', 'Withdrawal'),
        ('T', 'Transfer'),
    )

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transaction_account')
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    related_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, 
                                      null=True, blank=True, 
                                      related_name='related_account_transactions')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} ({self.timestamp})"