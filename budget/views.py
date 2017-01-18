
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ofxparse import OfxParser

from .models import *
from .forms import *

import codecs

def ofx_processer(ofxfile, u):
    with ofxfile as fileobj:
        ofx = OfxParser.parse(fileobj)
    
    ofx_results={}
    ofx_results['new_transactions'] = []
    ofx_results['updated_transactions'] = []
    ofx_results['new_accounts'] = []
    ofx_results['updated_accounts'] = []
    
    for ofa in ofx.accounts:
        actype = AccountType.objects.get_or_create(
                account_type = int(ofa.type),
                description = ofa.account_type
                )[0]
        a = Account.objects.get_or_create(
            owner = u,
            number = ofa.number,
            routing_number = ofa.routing_number,
            branch_id = ofa.branch_id,
            account_type = actype,
            curdef = ofa.curdef,
            institution = str(ofa.institution)
        )
        
        if a[1]:
            ofx_results['new_accounts'].append(a[0])
        else:
            ofx_results['updated_accounts'].append(a[0])
        a = a[0]

        a.statement_start_date = ofx.account.statement.start_date 
        a.statement_end_date = ofx.account.statement.end_date
        a.statement_balance = ofx.account.statement.balance 
        a.statement_available_balance = ofx.account.statement.available_balance
        a.save()

        prev_t = None
        next_t = None

        first_t = Transaction.objects.all().order_by('date','order')[0]

        transactions = ofx.account.statement.transactions
        transactions.reverse()
        for tr in ofx.account.statement.transactions:
            tr.date = tr.date.replace(hour=0)
            t_obj = Transaction.objects.get_or_create(
                account = a,
                date = tr.date,
                number = tr.id
            )
            if t_obj[1]:
                ofx_results['new_transactions'].append(t_obj[0])
            else:
                ofx_results['updated_transactions'].append(t_obj[0])
            
            t = t_obj[0]
            t.transaction_type = tr.type

            t.payee = tr.payee
            t.memo = tr.memo
            if tr.checknum == '':
                tr.checknum = None
            t.checknum = tr.checknum

            t.sic = tr.sic
            t.amount = tr.amount
            
            try:
                mcc = MerchantCategoryCode.objects.get(mcc_id=int(tr.mcc))
                t.mcc = mcc
            except:
                pass
            #Set previous and next relationships as well as the OrderedModed order
            if not prev_t:
                if t.date < first_t.date:
                    t.above(first_t)
                prev_t = Transaction.objects.filter(date__lt=t.date).order_by('-date', '-order')
                if prev_t:
                    prev_t = prev_t[0]
                    t.below(prev_t)
                else:
                    prev_t = None
            t.save()
            prev_t = t
            
    return ofx_results

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