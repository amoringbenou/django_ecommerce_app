from django.contrib import admin

from .forms import CustomUserCreationForm
# Register your models here.

from .models import *


admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)