from django import forms
from .models import Drug

class DrugCreation(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ['name', 'batch_no', 'stock', 'expiry_date', 'dose_pack', 'reorder_level']
        labels = {
            'reorder_level': 'Re-order Level',  # Label with a hyphen
        }
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dose_pack': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_no': forms.TextInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
        }


   
