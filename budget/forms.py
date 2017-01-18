from django import forms

class OFXUploadForm(forms.Form):
    ofx_file = forms.FileField(label='OFX File')

    ofx_file.widget.attrs = {
        'type': 'file',
        'class': 'form-control',
    }