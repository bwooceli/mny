from django import forms

from .models import *

class OFXUploadForm(forms.Form):
    ofx_file = forms.FileField(label='OFX File')

    ofx_file.widget.attrs = {
        'type': 'file',
        'class': 'form-control',
    }

#Budget forms
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'account']
        