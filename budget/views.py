
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ofxparse import OfxParser

from .models import *
from .forms import *
from .util import *

@login_required
def ofx_upload_view(request):
    # Handle file upload
    u = request.user
    processed = None
    if request.method == 'POST':
        form = OFXUploadForm(request.POST, request.FILES)
        processed = ofx_processer(request.FILES['ofx_file'], u)
        
    else:
        form = OFXUploadForm()  # A empty, unbound form
    
    context = {
        'form': form,
        'processed': processed,
    }

    return render(
        request,
        'ofx_upload.html',
        context
    )