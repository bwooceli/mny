
from django.http import Http404
from django.shortcuts import render

from .models import *

def ofx_loader(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            #handle the File
            request.FILES['file']
            return HttpResponseRedirect('')
    
    else:
        form = UploadFileForm()
    
    return render(request, 'upload.html')
    context = {}

    return render(request, 'polls/detail.html', context)