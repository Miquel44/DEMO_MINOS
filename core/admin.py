from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Users, Products, Orders, OrderItems

# Esto hace que aparezcan en el panel
admin.site.register(Users)
admin.site.register(Products)
admin.site.register(Orders)
admin.site.register(OrderItems)