from django.contrib import admin

# Register your models here.
from.models import BankAccount
admin.site.register(BankAccount)
admin.site.site_header = "KCB Bank Admin"
admin.site.site_title = "KCB Bank Admin Portal"