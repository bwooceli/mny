
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ofxparse import OfxParser

from .models import *
from .forms import *

import codecs

@login_required
def ofx_loader(request):
    # Handle file upload
    if request.method == 'POST':
        form = OFXUploadForm(request.POST, request.FILES)

            with codecs.open(request.FILES['ofx_file'])) as fileobj:
                ofx = OfxParser.parse(fileobj)
            
            new_transactions = []
            new_accounts = []
            
            for account in ofx.accounts:
                a = Account.objects.get_or_create(
                    a.owner = request.User

                    a.number = account.number
                    a.routing_number = account.routing_number
                    a.branch_id = account.branch_id

                    a.account_type = Account.objects.get_or_create(account_type=int(account.type), description=account.account_type)
                                        
                    a.curdef = account.curdef
                    a.institution = str(account.institution)
                )
                a.save()
                new_accounts.append(a)
            
            a = Account.objects.get(owner = request.User, number = ofx.account.number)

            a.statement_start_date = ofx.account.statement.start_date 
            a.statement_end_date = ofx.account.statement.end_date
            a.statement_balance = ofx.account.statement.balance 
            a.statement_available_balance = ofx.account.statement.available_balance
            a.save()

            for tr in ofx.account.statement.transactions:
                t = Transaction.objects.get_or_create(
                        account = a

                        t_tdate = tr.tdate
                        t_id = tr.id
                        t_type = tr.type

                        t_payee = tr.payee
                        t_memo = tr.memo
                        t_checknum = tr.checknum

                        t_mcc = MerchantCategoryCode.objects.get(mcc_id=int(tr.mcc))
                        t_sic = tr.sic
                        t_amount = tr.amount
                )
                t.save
                new_transactions.append(t)

            return HttpResponseRedirect()
    else:
        form = OFXUploadForm()  # A empty, unbound form

    # Load documents for the list page
    #transactions = Document.objects.all()

    # Render list page with the documents and the form
    return render(
        request,
        'ofx_upload.html',
        {
            'new_transactions': new_transactions, 
            'new_accounts': new_accounts
            'form': form
        }
    )