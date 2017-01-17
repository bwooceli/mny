from django import forms

class OFXUploadForm(forms.Form):
    ofx_file = forms.FileField()
