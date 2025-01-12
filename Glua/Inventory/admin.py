from django.contrib import admin
from .models import Drug, Sale, Stocked, Measurement, LockedProduct



admin.register(Drug, Sale, LockedProduct)(admin.ModelAdmin)
# Register your models here.
