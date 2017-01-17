
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
    
    new_transactions = []
    new_accounts = []
    
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
        
        new_accounts.append(a)
    
    a = Account.objects.get(owner = u, number = ofx.account.number)

    a.statement_start_date = ofx.account.statement.start_date 
    a.statement_end_date = ofx.account.statement.end_date
    a.statement_balance = ofx.account.statement.balance 
    a.statement_available_balance = ofx.account.statement.available_balance
    a.save()

    prev_t = None
    next_t = None

    for tr in ofx.account.statement.transactions:
        if not prev_t:
            prev_t = Transaction.objects.filter(t_tdate__lt=tr.date).order_by('-t_tdate')
            if prev_t:
                prev_t = prev_t[0]
            else:
                prev_t = None

        print(tr.amount)
        t = Transaction.objects.get_or_create(
            account = a,

            t_tdate = tr.date,
            t_id = tr.id,
            t_type = tr.type,

            t_payee = tr.payee,
            t_memo = tr.memo,
            t_checknum = tr.checknum,

            t_sic = tr.sic,
            t_amount = float(tr.amount)
        )
        try:
            t_mcc = MerchantCategoryCode.objects.get(mcc_id=int(tr.mcc))
        except:
            pass
        #Set previous and next relationships
        if p:
            t.previous_trans = p
            p.next_trans = t
            p.save()
        t.save()
        p = t
        new_transactions.append(t)

    return {
        'new_transactions': new_transactions,
        'new_accounts': new_accounts
    }

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