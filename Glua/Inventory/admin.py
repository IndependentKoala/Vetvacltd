from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import Drug, Sale, Stocked, Measurement, LockedProduct, MarketingItem, IssuedItem, PickingList, Cannister, IssuedCannister, Client


class DrugAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_no', 'stock', 'expiry_date', 'dose_pack', 'reorder_level')
    search_fields = ('name', 'batch_no')
    list_filter = ('expiry_date', 'stock', 'reorder_level')
    readonly_fields = ('name', 'batch_no')


class SaleAdmin(admin.ModelAdmin):
    list_display = ('drug_sold', 'seller', 'client', 'quantity', 'date_sold')
    search_fields = ('drug_sold', 'client__name', 'seller__username', 'batch_no')
    list_filter = ('date_sold', 'seller', 'client')


class StockedAdmin(admin.ModelAdmin):
    list_display = ('drug_name', 'number_added', 'supplier', 'staff', 'date_added')
    search_fields = ('drug_name__name', 'supplier', 'staff__username')
    list_filter = ('date_added', 'staff', 'drug_name')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'country_code', 'date_created')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('country_code', 'date_created')


class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('name', 'expiry_date')
    search_fields = ('name',)
    list_filter = ('expiry_date',)


class LockedProductAdmin(admin.ModelAdmin):
    list_display = ('drug', 'locked_by', 'date_locked', 'quantity', 'client')
    search_fields = ('drug__name', 'client__name', 'locked_by__username')
    list_filter = ('date_locked', 'locked_by', 'client')

    def save_model(self, request, obj, form, change):
        # Check if the object is being updated (change == True)
        if change:
            original = LockedProduct.objects.get(pk=obj.pk)
            # If the product is locked, prevent any changes to it
            if original.date_locked and obj.drug != original.drug:
                raise PermissionDenied("Cannot update locked drugs.")

        # Call the parent method to save the object
        super().save_model(request, obj, form, change)


class MarketingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock')
    search_fields = ('name',)
    list_filter = ('stock',)


class IssuedItemAdmin(admin.ModelAdmin):
    list_display = ('item', 'issued_to', 'quantity_issued', 'issued_by', 'date_issued')
    search_fields = ('item', 'issued_to', 'issued_by__username')
    list_filter = ('date_issued', 'issued_by')


class PickingListAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'product', 'batch_no', 'quantity')
    search_fields = ('product', 'batch_no', 'client__name')
    list_filter = ('date', 'client')


class CanisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_no', 'stock', 'litres')
    search_fields = ('name', 'batch_no')
    list_filter = ('stock', 'litres')


class IssuedCanisterAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_no', 'staff_on_duty', 'returned_by', 'client', 'quantity', 'date_issued')
    search_fields = ('name', 'batch_no', 'client__name', 'staff_on_duty__username', 'returned_by__username')
    list_filter = ('date_issued', 'date_returned', 'staff_on_duty', 'returned_by', 'client', 'action')


# Register models with their custom admin classes
admin.site.register(Drug, DrugAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Measurement, MeasurementAdmin)
admin.site.register(MarketingItem, MarketingItemAdmin)
admin.site.register(IssuedItem, IssuedItemAdmin)
admin.site.register(LockedProduct, LockedProductAdmin)
admin.site.register(PickingList, PickingListAdmin)
admin.site.register(Cannister, CanisterAdmin)
admin.site.register(IssuedCannister, IssuedCanisterAdmin)
admin.site.register(Stocked, StockedAdmin)